from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings
from .models import CitizenInfo
from django.db.models import Max
from datetime import datetime
from django.shortcuts import get_object_or_404


# Словарь citizen_id: relatives_id в рамках импорта для валидации relative
relatives_dict = {}


# def current_import_id():
#     """Определяет номер текущего импорта для POST запроса"""
#     previous_import_id = CitizenInfo.objects.aggregate(Max('import_id'))[
#         'import_id__max']
#     if not previous_import_id:
#         previous_import_id = 0
#     current_import_id = previous_import_id + 1
#     return current_import_id


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
    for relative_id in relatives_id_list:
        # Если объекта нет, то продолжаем цикл
        try:
            relative_instance = importing_citizens.get(citizen_id=relative_id)
        except:
            continue
        # Добавляем инстанс каждого родственника по-одному
        new_citizen.relatives.add(relative_instance)


class BulkCitizensSerializer(serializers.ListSerializer):
    """
    Логика сохранения объектов для POST запроса в create. Всё ради m2m
    Сюда приходят валидные данные по всем полям, кроме relatives.
    Делаем для relatives кастомную валидацию.
    Далее сохраняем в нужном виде relatives.
    """

    def create(self, validated_data):
        # Валидация поля relatives у всех граждан.
        # TODO хорошенько протестировать валидацию родственников
        for citizen_data in validated_data:
            citizen_id = citizen_data.get('citizen_id')
            for relative_id in citizen_data.get('relatives'):
                # Гарантировано, что значения уникальные и существуют, но
                # на всякий случай проверяю существование.
                try:
                    relatives_dict[relative_id]
                except:
                    raise serializers.ValidationError(
                        'At least one of the relatives_id does not exist.')
                if citizen_id in relatives_dict[relative_id]:
                    # Экономим время, если нашли симметрию, то удаляем
                    # текущего гражданина из "родственников" его родственника,
                    # Что бы не проверять по два раза
                    relatives_dict[relative_id].remove(citizen_id)
                # Если находим несовпадение, то сразу отдаем 400 BAD_REQUEST
                elif citizen_id not in relatives_dict[relative_id]:
                    raise serializers.ValidationError(
                        'At least one of the relatives_id is not matching.')
        # Достаем из контекста номер текущего импорта
        current_import_id = self.context.get('current_import_id')
        # Сохраняем валидные объект
        for citizen_data in validated_data:
            save_citizens(citizen_data, current_import_id)
        return CitizenInfo.objects.filter(import_id=current_import_id)

    def save(self, ):
    pass

class CitizenListSerializer(serializers.ModelSerializer):
    """
    Сериализатор для POST запроса. Логика сохранения в BulkCitizensSerializer
    """
    # Переопределяю сериализатор для того, чтобы написать кастомную валидацию
    # Иначе он сразу пытался делать валидацию m2m (согласно своей модели)
    # на еще не созданные объекты
    relatives = serializers.ListField(child=serializers.IntegerField())

    def validate_birth_date(self, value):
        """
        Валидация дня рождения
        Проверяем, чтобы дата была не позже чем сегодня
        """
        birth_date = value
        current_date = datetime.now().date()
        if birth_date > current_date:
            raise serializers.ValidationError("Birth_date can't be "
                                              "after current date")
        return value


    def run_validation(self, data=empty):
        """
        Валидация неизвестных полей в запросе. Отдаем 400, если есть
        Так же здесь подготовка к общей валидации relatives, которая будет
        проходить с данными из глобального
        словаря relatives_dict, в сериализаторе BulkCitizensSerializer

        Добавляем в глобальный словарь {"id гражданина": [id его родственников]}
        для последующей валидации.
        """
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: errors,
                })
        citizen_id = data['citizen_id']
        relatives_id_list = data['relatives']
        # Добавляем список id родственников в общий словарь граждан
        relatives_dict[citizen_id] = relatives_id_list
        return super(CitizenListSerializer, self).run_validation(data)

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]
        # Для доступа ко всем инстансам разом используем доп сериализатор
        list_serializer_class = BulkCitizensSerializer


class ImportDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]


class PatchSerializer(serializers.ModelSerializer):
    """Сериализатор для PATCH запроса"""
    relatives = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]

    def validate_citizen_id(self, value):
        """Запрещаем менять citizen_id"""
        raise serializers.ValidationError("Citizen_id can't be changed")

    def validate_birth_date(self, value):
        """Проверяем, чтобы дата была не позже чем сегодня"""
        birth_date = value
        current_date = datetime.now().date()
        if birth_date > current_date:
            raise serializers.ValidationError("Birth_date can't be "
                                              "after current date")
        return value

    def validate_relatives(self, value):
        """Преобразуем relatives_id в relatives_pk"""
        import_id = self.instance.import_id
        relatives_pk_list = []
        for citizen_id in value:
            citizen_pk = get_object_or_404(CitizenInfo, import_id=import_id,
                                           citizen_id=citizen_id).pk
            relatives_pk_list.append(citizen_pk)
        return relatives_pk_list

    def run_validation(self, data=empty):
        """Валидация неизвестных полей. Отдаем 400, если есть."""
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: errors,
                })
        return super(PatchSerializer, self).run_validation(data)

    def to_representation(self, instance):
        """Меняем отображение на PATCH запрос в случае успеха.
        Разбираемся с m2m отображением, а так же днём рождения"""
        citizen_pk = instance.pk
        citizen = CitizenInfo.objects.filter(pk=citizen_pk)
        relatives_pk = citizen.values_list('relatives', flat=True)
        relatives_id_list = []
        # Сюда попадает None
        # TODO исправить!
        if relatives_pk:
            for relative_pk in relatives_pk:
                if relative_pk == None:
                    break
                relative_id = get_object_or_404(CitizenInfo,
                                                pk=relative_pk).citizen_id
                relatives_id_list.append(relative_id)
        # Сортирую по порядку, вдруг важно при отображении
        relatives_id_list.sort()
        # Нужный формат дня рождения
        JSON_birth_date = datetime.strptime(str(instance.birth_date),
                                            '%Y-%m-%d').strftime('%d.%m.%Y')
        # Не нашел адекватного способа обойти ошибку сериализации m2m у
        # instance, поэтому вручную возвращаю ответ
        return {"citizen_id": instance.citizen_id,
                "town": instance.town,
                "street": instance.street,
                "building": instance.building,
                "apartment": instance.apartment,
                "name": instance.name,
                "birth_date": JSON_birth_date,
                "gender": instance.gender,
                "relatives": relatives_id_list}


class CitizensAgeSerializer(serializers.ModelSerializer):

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]

