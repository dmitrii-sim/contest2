from rest_framework.views import APIView
from rest_framework.response import Response

from django.shortcuts import render
from rest_framework.generics import CreateAPIView, ListAPIView
from .serializers import CitizenListSerializer
from .models import CitizenInfo
from rest_framework import status

class CitizenInfoView(APIView):
    # TODO разобраться с сериализацией, serializer.data не работает (там ошибка, формат str)
    def get(self, request, import_id):
        all_citizens = CitizenInfo.objects.filter(import_id=import_id)
        serializer = CitizenListSerializer(all_citizens, many=True)
        return Response({"data": all_citizens})


class CitizenInfoImportView(APIView):
    # TODO валидация relatives и оптимизация сохранения (в сериализаторе)
    def post(self, request):
        # Пробуем распаковать начальный словарь, если нет, то bad_request
        try:
            citizens = request.data.pop('citizens')
        except:
            return Response('Wrong format. Key should be "citizens"', status=status.HTTP_400_BAD_REQUEST)
        # Будем валидировать, а затем сохранять сразу всех граждан.
        # Поэтому если запрос плохой, то состояние БД не меняется.
        serializer = CitizenListSerializer(data=citizens, many=True)
        if serializer.is_valid():
            serializer_response = serializer.save()
            # В кастомном ответе сериализатора получаем айдишник текущего импорта
            # И отдаем его в качестве ответа, при успешном сохранении
            current_import_id = serializer_response[1]
            return Response({"data":
                                 {"import_id": current_import_id}}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



