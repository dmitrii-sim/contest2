from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import PostSerializer, \
    PatchSerializer, BaseCitizenInfoSerializer
from .models import CitizenInfo, ImportId

from django.db.models import Max

from datetime import datetime
import numpy as np


class CitizenInfoView(APIView):

    def get(self, request, import_id):
        """Возвращает список граждан текущего импорта"""
        # Проверяем существует ли запрошенный import_id
        # Достаем последний импорт из БД и сравниваем с запрошенным
        # В try except проверяется ситуация, когда импортов еще вообще нет в БД,
        # громоздко конечно. Можно использовать get_object_or_404, но надо 400.
        try:
            last_import = ImportId.objects.latest('import_id').import_id
            if import_id > last_import:
                raise
        except:
            return Response(
                "import_id does not exist",
                status=status.HTTP_400_BAD_REQUEST)
        all_import_citizens = CitizenInfo.objects.filter(import_id=import_id)
        serializer = BaseCitizenInfoSerializer(all_import_citizens, many=True)
        return Response({"data": serializer.data})


class CitizenInfoImportView(APIView):

    def post(self, request):
        """Валидация, сериализация и сохранение переданных объектов"""
        # Пробуем распаковать начальный словарь, если нет, то bad_request
        # Заодно отсеиваем всю поломанную структуру json, здесь допустимо
        try:
            citizens = request.data.pop('citizens')
        except:
            return Response('JSON should represent a dict {"citizens": [values]} '
                            'with correct value-type object',
                            status=status.HTTP_400_BAD_REQUEST)
        # Проверяем, что value в {citizens: [values]} это непустой лист.
        # Ожидаю ключ в виде непустого списка словарей объектов, иначе
        # какой смысл делать импорт. В ТЗ явно не указано
        if isinstance(citizens, list) and len(citizens) > 0:
            pass
        else:
            return Response('JSON should represent a dict {"citizens": [values]} '
                            'with correct value-type object',
                            status=status.HTTP_400_BAD_REQUEST)
        # В контекст добавляем словарь citizen_id: relatives_id для валидации
        # relatives, а так же "import_id" для получения и вывода значения
        serializer = PostSerializer(data=citizens, many=True,
                                    context={"relatives_dict": {},
                                             "import_id": 0})
        if serializer.is_valid():
            serializer.save()
            # Возвращаем номер импорта из контекста
            import_id = serializer.context.pop("import_id")
            return Response({"data": {"import_id": import_id}},
                            status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CitizenPatch(APIView):

    def patch(self, request, import_id, citizen_id):
        """
        Частичное либо полное обновление инстанса.
        citizen_id изменять запрещено.
        """
        # 400 если гражданин не найден.
        # Можно использовать get_object_or_404, но ТЗ говорит 400
        # (вдруг робот не поймет).
        try:
            citizen_object = CitizenInfo.objects.get(import_id=import_id,
                                                     citizen_id=citizen_id)
        except:
            return Response('Сitizen not found',
                            status=status.HTTP_400_BAD_REQUEST)
        # Валидацию на наличие данных делаем здесь (если делать
        # в сериализаторе, то чет выдает ошибку в serializer.errors
        # "ValueError: too many values to unpack (expected 2)"
        if not request.data:
            return Response("Input data can't be empty",
                            status=status.HTTP_400_BAD_REQUEST)
        serializer = PatchSerializer(instance=citizen_object, data=request.data,
                                     partial=True)
        if serializer.is_valid():
            # Если данные валидны, обновляем инстанс гражданина
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
        # Проверяем существует ли запрошенный import_id
        # Достаем последний импорт из БД и сравниваем с запрошенным
        try:
            last_import = ImportId.objects.latest('import_id').import_id
            if import_id > last_import:
                raise
        except:
            return Response(
                "import_id does not exist",
                status=status.HTTP_400_BAD_REQUEST)
        # Получаем инстансы всех граждан указанного импорта
        all_import_citizens = CitizenInfo.objects.filter(import_id=import_id)
        # Можно без сериализации, но так удобнее
        serializer = BaseCitizenInfoSerializer(all_import_citizens, many=True)
        # Определяем структуру ответа
        result_dict = {"1": [], "2": [], "3": [], "4": [], "5": [], "6": [],
                       "7": [], "8": [], "9": [], "10": [], "11": [], "12": []}
        # У каждого гражданина определяем его id и список id родственников
        for citizen in serializer.data:
            citizen_id = citizen.get('citizen_id')
            relatives_id_list = citizen.get('relatives')
            # Если родственники есть, то достаем их инстансы по их id
            if relatives_id_list:
                relatives_obj = all_import_citizens.\
                                        filter(citizen_id__in=relatives_id_list)
                for month in result_dict:
                    # Считаем число родственников с ДР в этом месяце (подарки)
                    presents = relatives_obj.filter(
                        birth_date__month=month).count()
                    # Если есть подарки, то делаем запись
                    if presents != 0:
                        result_dict[str(month)].append({"citizen_id": citizen_id,
                                                        "presents": presents})
        return Response({"data": result_dict})


class CitizensAgeView(APIView):
    def get(self, request, import_id):
        """
        Возвращает значение перцентилей по возрасту для каждого города
        из импорта.
        """
        # Проверяем существует ли запрошенный import_id
        # Достаем последний импорт из БД и сравниваем с запрошенным
        try:
            last_import = ImportId.objects.latest('import_id').import_id
            if import_id > last_import:
                raise
        except:
            return Response(
                "import_id does not exist",
                status=status.HTTP_400_BAD_REQUEST)
        # Получаем всех граждан нужного импорта
        all_import_citizens = CitizenInfo.objects.filter(import_id=import_id)
        # Получаем уникальный список всех городов из текущего импорта
        town_list = all_import_citizens.order_by(
            'town').values_list('town', flat=True).distinct()
        result_list = []
        # Для каждого города получаем его жителей
        for town in town_list:
            age_list = []
            town_citizens = all_import_citizens.filter(town=town)
            # Для каждого жителя города вычисляем его возраст
            # (округляем до полных лет)
            for citizen in town_citizens:
                # Вычисляем возраст каждого человека
                birth_date = citizen.birth_date
                current_date = datetime.now().date()
                # Дельта в днях
                delta_date = (current_date - birth_date).days
                # Полных лет
                age = delta_date // 365.2425
                age_list.append(age)
            result_dict = {}
            age_list = np.array(age_list)
            # Находим перцентили возраста для каждого города
            # Округляем до 2 после запятой
            p50 = round(np.percentile(age_list, 50), 2)
            p75 = round(np.percentile(age_list, 75), 2)
            p99 = round(np.percentile(age_list, 99), 2)
            # Заполняем структуру ответа и возвращаем в виде списка словарей
            result_dict['town'] = town
            result_dict['p50'] = p50
            result_dict['p75'] = p75
            result_dict['p99'] = p99
            result_list.append(result_dict)
        return Response({"data": result_list})
