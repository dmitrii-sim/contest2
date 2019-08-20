from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CitizenListSerializer, ImportDetailSerializer
from .models import CitizenInfo
from rest_framework import status
from datetime import datetime


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
            citizen['birth_date'] = JSON_birth_date
            # Преобразуем relatives к нужному формату
            relatives_pk_list = citizen.pop('relatives')
            relatives_id_list = []
            # Получаем id родственника по его pk
            for relative_pk in relatives_pk_list:
                relative_obj = all_import_citizens.get(pk=relative_pk)
                relative_id = getattr(relative_obj, 'citizen_id')
                relatives_id_list.append(relative_id)
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



