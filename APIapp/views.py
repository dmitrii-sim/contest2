from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CitizenListSerializer, ImportDetailSerializer, \
    PatchSerializer
from .models import CitizenInfo
from rest_framework import status
from datetime import datetime
from django.shortcuts import get_object_or_404


class CitizenInfoView(APIView):

    def get(self, request, import_id):
        all_import_citizens = CitizenInfo.objects.filter(import_id=import_id)
        serializer = ImportDetailSerializer(all_import_citizens, many=True)
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
        # Пробуем распаковать начальный словарь, если нет, то bad_request
        # Заодно отсеиваем всю поломанную структуру json, здесь допустимо
        try:
            citizens = request.data.pop('citizens')
        except:
            return Response('JSON should represent a dict {"citizens": value} '
                            'with correct value-type object',
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = CitizenListSerializer(data=citizens, many=True)
        if serializer.is_valid():
            serializer_response = serializer.save()
            # В кастомном ответе сериализатора получаем айдишник текущего импорта
            # И отдаем его в качестве ответа, при успешном сохранении
            current_import_id = serializer_response[1]
            return Response({"data": {"import_id": current_import_id}},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, import_id, citizen_id):
        # Проверка на наличие поля citizen_id в запросе
        try:
            if request.data.pop('citizen_id'):
                return Response("Citizen_id can't be changed",
                                status=status.HTTP_400_BAD_REQUEST)
        except:
            pass

        # TODO понять возвращать при неверном url 400 или 404 тоже можно
        citizen_object = get_object_or_404(CitizenInfo,
                                           import_id=import_id,
                                           citizen_id=citizen_id)
        citizens_from_import = CitizenInfo.objects.filter(import_id=import_id)
        # TODO проверить возврат relatives обратно в запрос
        # здесь получаем вытаскиваем relatives, если они есть и преобразуем
        try:
            relatives_id_list = request.data.pop('relatives')
            relatives_pk_list = []
            for relative_id in relatives_id_list:
                relative_pk = citizens_from_import.get(citizen_id=relative_id).pk
                relatives_pk_list.append(relative_pk)
            request.data['relatives'] = relatives_pk_list
        except:
            pass

        serializer = ImportDetailSerializer(citizen_object, data=request.data, partial=True)
        if serializer.is_valid():

            serializer.save()
            return Response({"data": serializer.data})
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class CitizenPatch(APIView):
    # TODO потестить patch
    def patch(self, request, import_id, citizen_id):
        # Проверка на наличие поля citizen_id в запросе
        # try:
        #     if request.data.pop('citizen_id'):
        #         return Response("Citizen_id can't be changed",
        #                         status=status.HTTP_400_BAD_REQUEST)
        # except:
        #     pass
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