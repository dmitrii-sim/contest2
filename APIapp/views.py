from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import CitizenListSerializer, CitizenInfoGetSerializer, \
    PatchSerializer
from .models import CitizenInfo

from django.shortcuts import get_object_or_404
from django.db.models import Max

from datetime import datetime
import numpy as np



def get_current_import():
    """Определяет номер текущего импорта для POST запроса"""
    previous_import_id = CitizenInfo.objects.aggregate(Max('import_id'))[
        'import_id__max']
    if not previous_import_id:
        previous_import_id = 0
    current_import_id = previous_import_id + 1
    return current_import_id

class CitizenInfoView(APIView):

    def get(self, request, import_id):
        """Возвращает список граждан текущего импорта"""
        all_import_citizens = CitizenInfo.objects.filter(import_id=import_id)
        serializer = CitizenInfoGetSerializer(all_import_citizens, many=True)
        # У каждого объекта приводим уникальный в рамках всех импортов номер
        # родственника из бд к уникальному в рамках импорта для отображения
        for citizen in serializer.data:
            # Преобразуем birth_date к требуемому формату
            db_birth_date = citizen.pop('birth_date')
            JSON_birth_date = datetime.strptime(db_birth_date,
                                                '%Y-%m-%d').strftime('%d.%m.%Y')
            # Вставляем обратно
            citizen['birth_date'] = JSON_birth_date
            # Преобразуем relatives к нужному формату
            relatives_pk_list = citizen.pop('relatives')
            relatives_id_list = []
            # Получаем id родственника по его pk
            for relative_pk in relatives_pk_list:
                relative_obj = all_import_citizens.get(pk=relative_pk)
                relative_id = getattr(relative_obj, 'citizen_id')
                relatives_id_list.append(relative_id)
            # Вставляем обратно
            citizen['relatives'] = relatives_id_list
        return Response({"data": serializer.data})


class CitizenInfoImportView(APIView):

    def post(self, request):
        """Валидация, сериализация и сохранение переданных объектов"""
        # Пробуем распаковать начальный словарь, если нет, то bad_request
        # Заодно отсеиваем всю поломанную структуру json, здесь допустимо
        try:
            citizens = request.data.pop('citizens')
        except:
            return Response('JSON should represent a dict {"citizens": value} '
                            'with correct value-type object',
                            status=status.HTTP_400_BAD_REQUEST)
        # Определяем номер текущего импорта для POST запроса
        current_import_id = get_current_import()
        serializer = CitizenListSerializer(context={"current_import_id":
                                                    current_import_id},
                                           data=citizens,
                                           many=True)
        if serializer.is_valid():
            serializer.save()
            current_import_id = serializer.context['current_import_id']
            # При успешном сохранении возвращаем номер импорта
            return Response({"data": {"import_id": current_import_id}},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class CitizenPatch(APIView):

    def patch(self, request, import_id, citizen_id):
        """
        Частичное либо полное обновление инстанса.
        citizen_id изменять запрещено.
        """
        # TODO поменять либо описать 404 возвраты, а то неясно откуда.
        # 404 если гражданин не найден
        citizen_object = get_object_or_404(CitizenInfo,
                                           import_id=import_id,
                                           citizen_id=citizen_id)
        serializer = PatchSerializer(instance=citizen_object, data=request.data,
                                     partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"data": serializer.data})
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class CitizensPresentsView(APIView):

    def get(self, request, import_id):
        """
        Получаем список месяцев, в каждом указан номер гражданина из
        импорта и сколько подарков в этом месяце он должен подарить.
        """
        all_import_citizens = CitizenInfo.objects.filter(import_id=import_id)
        # Можно без сериализации, но так удобнее
        serializer = CitizenInfoGetSerializer(all_import_citizens, many=True)
        # Определяем структуру ответа
        result_dict = {"1": [], "2": [], "3": [], "4": [], "5": [], "6": [],
                       "7": [], "8": [], "9": [], "10": [], "11": [], "12": []}
        for citizen in serializer.data:
            citizen_id = citizen.get('citizen_id')
            relatives_pk_list = citizen.get('relatives')
            if relatives_pk_list:
                relatives_obj = all_import_citizens.filter(pk__in=relatives_pk_list)
                for month in result_dict:
                    # Считаем число родственников с ДР в этом месяце (подарки)
                    presents = relatives_obj.filter(
                        birth_date__month=month).count()
                    # Если нет подарков, то запись не делаем
                    if presents != 0:
                        result_dict[str(month)].append({"citizen_id": citizen_id,
                                                        "presents": presents})
        return Response({"data": result_dict})


class CitizensAgeView(APIView):
    def get(self, requset, import_id):
        """
        Возвращает значение перцентилей по возрасту для каждого города
        из импорта.
        """
        all_import_citizens = CitizenInfo.objects.filter(import_id=import_id)
        # Уникальный список всех городов из импорта
        town_list = all_import_citizens.order_by(
            'town').values_list('town', flat=True).distinct()
        result_list = []

        for town in town_list:
            age_list = []
            town_citizens = all_import_citizens.filter(town=town)
            for citizen in town_citizens:
                # Вычисляем возраст каждого человека
                birth_date = citizen.birth_date
                current_date = datetime.now().date()
                delta_date = (current_date - birth_date).days
                # year_date = float(date) / 365.2425
                difference_in_years = delta_date / 365.2425
                age_list.append(difference_in_years)
            result_dict = {}
            # Находим перцентили возраста для каждого города
            age_list = np.array(age_list)
            p50 = round(np.percentile(age_list, 50), 2)
            p75 = round(np.percentile(age_list, 75), 2)
            p99 = round(np.percentile(age_list, 99), 2)
            result_dict['town'] = town
            result_dict['p50'] = p50
            result_dict['p75'] = p75
            result_dict['p99'] = p99
            result_list.append(result_dict)
        return Response({"data": result_list})
