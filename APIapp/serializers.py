from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings

from .models import CitizenInfo

from datetime import datetime


# Словарь citizen_id: relatives_id в рамках импорта, для валидации relative
# в POST запросе
relatives_dict = {}


class TrueIntegerField(serializers.IntegerField):
    """
    В DRF стандартный сериализатор IntegerField, какого-то дедушки, может
    принимать число в виде str и конвертировать его до валидации
    (туда строка в виде int приходит). По ТЗ нам нужно принимать только
    целые числа.
    Поэтому наследуемся от сериализатора IntegerField и переопределяем первичную валидацию.
    Если входные данные str, то возвращаем bad request 400.
    """
    def to_internal_value(self, data):
        if isinstance(data, int):
            return super().to_internal_value(data)
        raise serializers.ValidationError("Value should be an integer")


class TrueCharField(serializers.CharField):
    """
    Так как в DRF стандартный сериализатор CharField принимает int и
    конвертирует его до валидации (туда он приходит уже в виде str),
    то наследуемся от этого класса и переопределяем первичную валидацию.
    Если входные данные int, то возвращаем bad request 400.
    """
    def to_internal_value(self, data):
        if isinstance(data, str):
            return super().to_internal_value(data)
        raise serializers.ValidationError("Value should be a string")


class BaseCitizenInfoSerializer(serializers.ModelSerializer):
    """
    Кастомный базовый валидатор с общей логикой сериализации
    и десериализации
    """
    # Наследуемся от кастомных валидаторов типа данных
    citizen_id = TrueIntegerField(min_value=0)
    town = TrueCharField(max_length=256)
    street = TrueCharField(max_length=256)
    building = TrueCharField(max_length=256)
    apartment = TrueIntegerField(min_value=0)
    name = TrueCharField(max_length=256)
    relatives = serializers.ListField(child=TrueIntegerField(min_value=0))

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]

    def run_validation(self, data=empty):
        """Валидация неизвестных полей. Отдаем 400, если есть."""
        if data:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: errors,
                })
        return super(BaseCitizenInfoSerializer, self).run_validation(data)

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

    def to_representation(self, instance):
        """
        Корректируем отображение данных из БД.
        m2m отображение родственников, формат даты дня рождения
        """
        citizen_pk = instance.pk
        citizen = CitizenInfo.objects.filter(pk=citizen_pk)
        relatives_pk = citizen.values_list('relatives', flat=True)
        relatives_id_list = []
        if None not in relatives_pk:
            for relative_pk in relatives_pk:
                relative_id = CitizenInfo.objects.get(pk=relative_pk).citizen_id
                relatives_id_list.append(relative_id)
        # Сортирую по порядку, вдруг важно при отображении
        relatives_id_list.sort()
        # Нужный формат дня рождения
        JSON_birth_date = datetime.strptime(str(instance.birth_date),
                                            '%Y-%m-%d').strftime('%d.%m.%Y')
        # Составляем ответ вручную
        return {
            "citizen_id": instance.citizen_id,
            "town": instance.town,
            "street": instance.street,
            "building": instance.building,
            "apartment": instance.apartment,
            "name": instance.name,
            "birth_date": JSON_birth_date,
            "gender": instance.gender,
            "relatives": relatives_id_list
        }


def save_citizens(citizen_data, current_import_id):
    """Логика полного сохранения гражданина"""
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
    # Тут допустимо сохранить объект, так как добавление m2m поля должно
    # быть к существующему объекту и по одному инстансу.
    # К этому моменту мы уверены, что все данные прошли валидацию.
    # (иначе может засориться БД и сбиться очерёдность import_id)
    new_citizen.save()
    # Далее достаем сохраненные объекты данного импорта уже из БД
    importing_citizens = CitizenInfo.objects.filter(import_id=current_import_id)
    # Поле родственников будем сохранять постепенно, по мере создания граждан
    relatives_id_list = citizen_data.get('relatives')
    # В рамках одного импорта citizen_id == relative_id
    for relative_id in relatives_id_list:
        # Если родственник еще не сохранен в БД, то просто продолжаем цикл,
        # так как связь симметричная и далее он все-равно попадет в родственники
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
    Делаем для relatives кастомную валидацию (проверяем, что все родственники
    прописаны друг у друга). Далее сохраняем в нужном виде relatives.
    """

    def create(self, validated_data):
        """Здесь валидация поля relatives, а так же сохранение объектов"""
        # Валидация поля relatives у всех граждан.
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
                    # Что бы не проверять по два раза. Сохранению не помешает.
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


class PostSerializer(BaseCitizenInfoSerializer):
    """
    Сериализатор для POST запроса. Логика сохранения в BulkCitizensSerializer
    """

    def run_validation(self, data=empty):
        """
        Помимо родительской логики здесь подготовка к общей валидации relatives,
        которая будет проходить с данными из глобального
        словаря relatives_dict, в сериализаторе BulkCitizensSerializer

        Добавляем в глобальный словарь {"id гражданина": [id его родственников]}
        для последующей валидации.
        """
        # Если входных данных нет, то отдаем bad request 400
        if not data:
            raise serializers.ValidationError("Input data can't be empty")
        citizen_id = data['citizen_id']
        relatives_id_list = data['relatives']
        # Добавляем список id родственников в общий словарь граждан
        relatives_dict[citizen_id] = relatives_id_list
        return super(PostSerializer, self).run_validation(data)

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]
        # Для доступа ко всем инстансам разом используем доп сериализатор
        list_serializer_class = BulkCitizensSerializer


class PatchSerializer(BaseCitizenInfoSerializer):
    """
    Сериализатор для PATCH запроса.
    Наследуемся и немного меняем логику валидации
    """

    def validate_citizen_id(self, value):
        """Запрещаем менять citizen_id"""
        raise serializers.ValidationError("Citizen_id can't be changed")

    def validate_relatives(self, value):
        """Преобразуем relatives_id в relatives_pk"""
        import_id = self.instance.import_id
        relatives_pk_list = []
        for citizen_id in value:
            # Проверяем, существует ли родственник с таким id
            try:
                citizen_pk = CitizenInfo.objects.get(import_id=import_id,
                                                     citizen_id=citizen_id).pk
            except:
                raise serializers.ValidationError("Relative not found")
            relatives_pk_list.append(citizen_pk)
        return relatives_pk_list
