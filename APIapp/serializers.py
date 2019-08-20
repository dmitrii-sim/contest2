from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings
from .models import CitizenInfo
from django.db.models import Max
from datetime import datetime
from rest_framework.exceptions import APIException


# TODO может ли человек быть сам себе родственником??? citizen_id: 1, relatives: [1, 2, 3]



# Словарь citizen_id: relatives_id в рамках импорта для валидации relative
relatives_dict = {}


# Логика полного сохранения гражданина
def save_citizens(citizen_data, current_import_id):
    new_citizen = CitizenInfo(import_id=current_import_id,
                              citizen_id=citizen_data.get('citizen_id'),
                              town=citizen_data.get('town'),
                              street=citizen_data.get('street'),
                              building=citizen_data.get('building'),
                              apartment=citizen_data.get('apartment'),
                              name=citizen_data.get('name'),
                              birth_date=citizen_data.get('birth_date'),
                              gender=citizen_data.get('gender'),
                              )
    # Сохраняем, так как добавление m2m поля должно быть к существующему объекту
    # Получается, что объекты у нас сохраняются не разом в return, а постепенно
    # TODO попробовать что-то решить, но скорее всего нет, т.к m2m
    new_citizen.save()
    importing_citizens = CitizenInfo.objects.filter(import_id=current_import_id)
    # Здесь ожидаем уже валидированных родственников
    # Так как наша связь many2many симметрична, то список родственников
    # будем сохранять постепенно, по мере создания граждан
    relatives_id_list = citizen_data.get('relatives')
    # В рамках одного импорта citizen_id == relative_id
    relative_pk_list = []
    for relative_id in relatives_id_list:
        # Если объекта нет, то продолжаем цикл
        try:
            relative_pk = importing_citizens.get(citizen_id=relative_id)
        except:
            continue
        # Добавляем каждого родственника по-одному
        new_citizen.relatives.add(relative_pk)


class BulkCitizensSerializer(serializers.ListSerializer):

    # Сюда приходят валидные данные по всем полям, кроме relatives
    # Делаем для relatives кастомную валидацию.
    # Далее сохраняем в нужном виде relatives, добавляем значение
    # для поля import_id
    def create(self, validated_data):
        # Валидация поля relatives у всех граждан.
        # TODO хорошенько протестировать валидацию родственников
        for citizen_data in validated_data:
            citizen_id = citizen_data.get('citizen_id')
            for relative_id in citizen_data.get('relatives'):
                # Гарантировано, что значения уникальные и существуют.
                try:
                    relatives_dict[relative_id]
                except:
                    raise serializers.ValidationError(
                        'At least one of the relatives_id does not exist.')
                if citizen_id in relatives_dict[relative_id]:
                    # Экономим время, если нашли симметрию, то удаляем
                    # текущего гражданина из "родственников" его родственника
                    relatives_dict[relative_id].remove(citizen_id)
                # Если находим несовпадение, то сразу отдаем 400 BAD_REQUEST
                elif citizen_id not in relatives_dict[relative_id]:
                    raise serializers.ValidationError(
                        'At least one of the relatives_id is not matching.')
        # Достаем номер последнего импорта
        # в формате словаря {'import_id__max': *число*}
        # И определяем текущий импорт
        previous_import_id = CitizenInfo.objects.aggregate(Max('import_id'))['import_id__max']
        if not previous_import_id:
            previous_import_id = 0
        current_import_id = previous_import_id + 1
        # Сохраняем валидные объект
        for citizen_data in validated_data:
            save_citizens(citizen_data, current_import_id)
        return CitizenInfo.objects.filter(import_id=current_import_id),\
               current_import_id


class CitizenListSerializer(serializers.ModelSerializer):
    # Переопределяю сериализатор для того, чтобы написать кастомную валидацию
    # Иначе он сразу пытался делать валидацию m2m (согласно своей модели)
    # на еще не созданные объекты
    relatives = serializers.ListField()

    # Добавляем кастомную валидацию неизвестных полей в запросе.
    # Дополняем словарь relatives для последующей валидации в create
    def run_validation(self, data=empty):
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: errors,
                })
        citizen_id = data.get('citizen_id')
        relatives_id_list = data.get('relatives')
        # Добавляем список id родственников в общий словарь граждан
        relatives_dict[citizen_id] = relatives_id_list
        return super(CitizenListSerializer, self).run_validation(data)

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]
        list_serializer_class = BulkCitizensSerializer


class ImportDetailSerializer(serializers.ModelSerializer):
    # Сериализатор для GET
    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]
