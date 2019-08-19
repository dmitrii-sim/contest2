from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings
from .models import CitizenInfo
from django.db.models import Max
from datetime import datetime


def save_citizens(citizen_data, current_import_id):
    # birth_date в БД кладется в формате Django (Y-d-m)
    new_citizen = CitizenInfo(import_id=current_import_id, citizen_id=citizen_data.get('citizen_id'),
                                             town=citizen_data.get('town'), street=citizen_data.get('street'),
                                             building=citizen_data.get('building'),
                                             apartment=citizen_data.get('apartment'),
                                             name=citizen_data.get('name'), birth_date=citizen_data.get('birth_date'))
    current_import_citizens = CitizenInfo.objects.filter(import_id=current_import_id)
    for relative in citizen_data.get('relatives'):
        new_citizen.relatives.add(relative)
    return new_citizen

class BulkCitizensSerializer(serializers.ListSerializer):

    # Из пост запроса приходит уже валидированые данные
    # Здесь их сохраняем и добавляем import_id
    # Так же с полем родственники тоже скорее всего тут будем работать при Post
    def create(self, validated_data):
        # Достаем номер последнего импорта. В формате словаря {'import_id__max': *число*}
        # И определяем текущий импорт
        previous_import_id = CitizenInfo.objects.aggregate(Max('import_id'))['import_id__max']
        if not previous_import_id:
            previous_import_id = 0
        current_import_id = previous_import_id + 1
        # Инстансы для return
        new_citizens = [save_citizens(citizen_data, current_import_id) for citizen_data in validated_data]
        return CitizenInfo.objects.bulk_create(new_citizens), current_import_id



class CitizenListSerializer(serializers.ModelSerializer):

    # Валидатор неизвестных полей в запросе
    def run_validation(self, data=empty):
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError({
                    api_settings.NON_FIELD_ERRORS_KEY: errors,
                })
        return super(CitizenListSerializer, self).run_validation(data)

    class Meta:
        model = CitizenInfo
        exclude = ['id', 'import_id', ]
        list_serializer_class = BulkCitizensSerializer
