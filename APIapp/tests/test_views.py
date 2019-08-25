import json
from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ..models import CitizenInfo, ImportId
import datetime


# Глобально определяем дефолтного клиента
client = Client()


class TestCaseInitialData(TestCase):
    """Начальный setup для Get и Patch"""
    def setUp(self):
        # Создаем инстанс импорта
        self.import_instance = ImportId.objects.create()
        self.citizen1 = CitizenInfo.objects.create(
            citizen_id=1, import_id=self.import_instance, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Иван Иванович",
            birth_date="1986-12-26", gender="male"
        )
        self.citizen2 = CitizenInfo.objects.create(
            citizen_id=2, import_id=self.import_instance, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Сергей Иванович",
            birth_date="1997-04-01", gender="male"
        )
        self.citizen3 = CitizenInfo.objects.create(
            citizen_id=3, import_id=self.import_instance, town="Керчь", street="Иосифа Бродского",
            building="2", apartment=11, name="Романова Мария Леонидовна",
            birth_date="1986-11-23", gender="female"
        )
        # Добавляем m2m, она симметрична
        self.citizen1.relatives.add(self.citizen2, self.citizen3)


class PostCitizensTest(TestCase):
    """ Тест POST запроса """

    def setUp(self):
        # Валидные данные
        self.valid_payload = {
   "citizens":[
      {
         "citizen_id":1,
         "town":"Москва",
         "street":"Льва Толстого",
         "building":"16к7стр5",
         "apartment":7,
         "name":"Иванов Иван Иванович",
         "birth_date":"26.12.1986",
         "gender":"male",
         "relatives":[
            2
         ]
      },
      {
         "citizen_id":2,
         "town":"Москва",
         "street":"Льва Толстого",
         "building":"16к7стр5",
         "apartment":7,
         "name":"Иванов Сергей Иванович",
         "birth_date":"01.04.1997",
         "gender":"male",
         "relatives":[
            3,
            1
         ]
      },
      {
         "citizen_id":3,
         "town":"Керчь",
         "street":"Иосифа Бродского",
         "building":"2",
         "apartment":11,
         "name":"Романова Мария Леонидовна",
         "birth_date":"23.11.1986",
         "gender":"female",
         "relatives":[
            2
         ]
      }
   ]
}
        # Невалидные данные
        # пустой список в значении словаря citizens
        self.invalid_payload1 = {"citizens":[]}
        # список из пустых словарей в значении словаря citizens
        self.invalid_payload2 = {"citizens":[{}, {}]}
        # неверный ключ словаря citizens
        self.invalid_payload3 = {"cins":[
                            {
                                "citizen_id":1,
                                "town":"Москва",
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":7,
                                "name":"Иванов Иван Иванович",
                                "birth_date":"26.12.1986",
                                "gender":"male",
                                "relatives":[]
                            }]}
        # citizen_id с типом str
        self.invalid_payload4 = {"citizens":[
                            {
                                "citizen_id":"1",
                                "town":"Москва",
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":7,
                                "name":"Иванов Иван Иванович",
                                "birth_date":"26.12.1986",
                                "gender":"male",
                                "relatives":[]
                            }]}
        # town типа int
        self.invalid_payload5 = {"citizens":[
                            {
                                "citizen_id":1,
                                "town":15,
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":7,
                                "name":"Иванов Иван Иванович",
                                "birth_date":"26.12.1986",
                                "gender":"male",
                                "relatives":[]
                            }]}
        # apartment тиа str
        self.invalid_payload6 = {"citizens":[
                            {
                                "citizen_id":1,
                                "town":"Москва",
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":"123",
                                "name":"Иванов Иван Иванович",
                                "birth_date":"26.12.1986",
                                "gender":"male",
                                "relatives":[]
                            }]}
        # День рождения больше текущей даты (актуально до 27.12.2050)
        self.invalid_payload7 = {"citizens":[
                            {
                                "citizen_id":1,
                                "town":"Москва",
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":7,
                                "name":"Иванов Иван Иванович",
                                "birth_date":"26.12.2050",
                                "gender":"male",
                                "relatives":[]
                            }]}
        # Пол не совпадает с предопределенными значениями "male", "female"
        self.invalid_payload8 = {"citizens":[
                            {
                                "citizen_id":1,
                                "town":"Москва",
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":7,
                                "name":"Иванов Иван Иванович",
                                "birth_date":"26.12.1986",
                                "gender":"transgender",
                                "relatives":[]
                            }]}
        # Указан несуществующий родственник
        self.invalid_payload9 = {"citizens":[
                            {
                                "citizen_id":1,
                                "town":"Москва",
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":7,
                                "name":"Иванов Иван Иванович",
                                "birth_date":"26.12.1986",
                                "gender":"male",
                                "relatives":[5]
                            }]}
        # Несуществующая дата
        self.invalid_payload10 = {"citizens":[
                            {
                                "citizen_id":1,
                                "town":"Москва",
                                "street":"Льва Толстого",
                                "building":"16к7стр5",
                                "apartment":7,
                                "name":"Иванов Иван Иванович",
                                "birth_date":"32.12.1986",
                                "gender":"male",
                                "relatives":[]
                            }]}
        # id одного из родственников типа str
        self.invalid_payload11 = {"citizens": [
            {
                "citizen_id": 1,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986",
                "gender": "male",
                "relatives": [2, "1"]
            }, {
                "citizen_id": 2,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997",
                "gender": "male",
                "relatives": [1]
            }
        ]}
        # у второго гражданина родственник указан без списка
        self.invalid_payload12 = {"citizens": [
            {
                "citizen_id": 1,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986",
                "gender": "male",
                "relatives": [2, 1]
            }, {
                "citizen_id": 2,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997",
                "gender": "male",
                "relatives": 1
            }
        ]},
        # у второго гражданина пропущено обязательное поле name
        self.invalid_payload13 = {"citizens": [
            {
                "citizen_id": 1,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986",
                "gender": "male",
                "relatives": [2, 1]
            }, {
                "citizen_id": 2,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "birth_date": "01.04.1997",
                "gender": "male",
                "relatives": [1]
            }
        ]}
        # не совпадают входные списки родственников у граждан
        self.invalid_payload14 = {"citizens": [
            {
                "citizen_id": 1,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Иван Иванович",
                "birth_date": "26.12.1986",
                "gender": "male",
                "relatives": [2, 1]
            }, {
                "citizen_id": 2,
                "town": "Москва",
                "street": "Льва Толстого",
                "building": "16к7стр5",
                "apartment": 7,
                "name": "Иванов Сергей Иванович",
                "birth_date": "01.04.1997",
                "gender": "male",
                "relatives": []
            }
        ]}
        self.invalid_payloads = [self.invalid_payload1, self.invalid_payload2,
                                 self.invalid_payload3, self.invalid_payload4,
                                 self.invalid_payload5, self.invalid_payload6,
                                 self.invalid_payload7, self.invalid_payload8,
                                 self.invalid_payload9, self.invalid_payload10,
                                 self.invalid_payload11, self.invalid_payload12,
                                 self.invalid_payload13, self.invalid_payload14]

    def test_post_valid_citizens(self):
        """Тест на получение валидного ответа"""
        response = client.post(
            reverse('post_citizens'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        # Джанговский AutoField в PostgreSQL обнуляется только при DROP TABLE.
        # Поэтому, т.к в unittest используется своя БД, которая дропается
        # при новом запуске, то номер импорта определим через его модель,
        # так как при юниттесте конкретно этого блока - import_id = 1,
        # а при общем запуске тест файла через консоль import_id равен
        # колличеству вызовов create инстанса ImportId до него (но это не точно)
        last_import = ImportId.objects.latest('import_id').import_id
        self.assertEqual(response.data, {'data': {'import_id': last_import}})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_invalid_citizens(self):
        """Тест всех возможных невалидных запросов POST"""
        for invalid_payload in self.invalid_payloads:
            response = client.post(
                reverse('post_citizens'),
                data=json.dumps(invalid_payload),
                content_type='application/json'
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_imports_production(self):
        """Нагрузочное тестирование нескольких POST запросов"""
        i = 0
        while i < 100:
            response = client.post(
                reverse('post_citizens'),
                data=json.dumps(self.valid_payload),
                content_type='application/json'
            )
            last_import = ImportId.objects.latest('import_id').import_id
            self.assertEqual(response.data,
                             {'data': {'import_id': last_import}})
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            i += 1


class GetCitizensFromImportTest(TestCaseInitialData):
    """Тест для GET запроса списка граждан из импорта"""

    # Заранее известный результат
    expected_data = {'data': [
        {'citizen_id': 1, 'town': 'Москва', 'street': 'Льва Толстого',
         'building': '16к7стр5', 'apartment': 7,
         'name': 'Иванов Иван Иванович', 'birth_date': '26.12.1986',
         'gender': 'male', 'relatives': [2, 3]},
        {'citizen_id': 2, 'town': 'Москва', 'street': 'Льва Толстого',
         'building': '16к7стр5', 'apartment': 7,
         'name': 'Иванов Сергей Иванович', 'birth_date': '01.04.1997',
         'gender': 'male', 'relatives': [1]},
        {'citizen_id': 3, 'town': 'Керчь', 'street': 'Иосифа Бродского',
         'building': '2', 'apartment': 11,
         'name': 'Романова Мария Леонидовна', 'birth_date': '23.11.1986',
         'gender': 'female', 'relatives': [1]}]}

    def test_get_valid_import_citizens_list(self):
        """Тест статуса и ответа сервера при валидном запросе"""
        response = client.get(
            reverse('get_all_import_citizens',
                    kwargs={'import_id': self.import_instance.import_id}))
        self.assertEqual(response.data, self.expected_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_import_citizens_list(self):
        """Тест статуса сервера при запросе несуществующего импорта"""
        response = client.get(
            reverse('get_all_import_citizens', kwargs={'import_id': 10}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_valid_import_citizens_list_production(self):
        """
        Нагрузочное тестирование статуса и ответа сервера при валидном запросе
        """
        i = 0
        while i < 100:
            response = client.get(
                   reverse('get_all_import_citizens',
                            kwargs={'import_id': self.import_instance.import_id}))
            self.assertEqual(response.data, self.expected_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            i += 1


class PatchCitizenTest(TestCaseInitialData):
    """
    Тест PATCH запроса
    Чтобы провести нагрузочное тестирование patch запроса используем пару
    начальных валидных данных и пару ожидаемых значений и меняем их в цикле.
    """
    def setUp(self):
        """
        Наследуемся от начального набора данных и добавляем
        валидные и невалидные случаи PATCH запросов
        """
        super(PatchCitizenTest, self).setUp()
        # Валидный набор данных
        self.valid_payload1 = {
            "town": "Не Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванова Мария Леонидовна",
            "relatives": [1]
        }
        self.valid_payload2 = {
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванова Мария Леонидовна",
            "relatives": [1]
        }
        # Невалидные наборы
        # Пустой словарь
        self.invalid_payload1 = {}
        # citizen_id менять запрещено
        self.invalid_payload2 = {
            "citizen_id": 1,
            "town": "Москва"
        }
        # Неизвестное поле
        self.invalid_payload3 = {
            "tn": "Москва",
        }
        # Невалидная дата
        self.invalid_payload4 = {
            "birth_date": "-26.12.1986",
            "gender": "male",
            "relatives": []
        }
        # Пол указан вне предопределенных значений
        self.invalid_payload5 = {
            "gender": "apache69",
        }
        # Отрицательные числа запрещены
        self.invalid_payload9 = {
            "apartment": -7,
        }
        # Значения списка родственников должны быть только целые числа
        self.invalid_payload10 = {
            "relatives": ["2"]
        }
        self.invalid_payloads = [self.invalid_payload1, self.invalid_payload2,
                                 self.invalid_payload3, self.invalid_payload4,
                                 self.invalid_payload5, self.invalid_payload9,
                                 self.invalid_payload10]
        # Ожидаемый результат
        self.expected_data1 = {'data': {'citizen_id': 1, 'town': 'Не Москва',
                                     'street': 'Льва Толстого',
                                     'building': '16к7стр5', 'apartment': 7,
                                     'name': 'Иванова Мария Леонидовна',
                                     'birth_date': '26.12.1986',
                                     'gender': 'male', 'relatives': [1]}}
        # Разные значения поля town.
        self.expected_data2 = {'data': {'citizen_id': 1, 'town': 'Москва',
                                        'street': 'Льва Толстого',
                                        'building': '16к7стр5', 'apartment': 7,
                                        'name': 'Иванова Мария Леонидовна',
                                        'birth_date': '26.12.1986',
                                        'gender': 'male', 'relatives': [1]}}

    def test_valid_patch_citizen(self):
        """Тест валидные данные, ответ и статус"""
        response = client.patch(
            reverse('patch_citizen',
                    kwargs={'import_id': self.import_instance.import_id,
                            'citizen_id': self.citizen1.citizen_id}),
            data=json.dumps(self.valid_payload1),
            content_type='application/json'
        )
        self.assertEqual(response.data, self.expected_data1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_patch_citizen(self):
        """Тест невалидные данные"""
        for invalid_payload in self.invalid_payloads:
            response = client.patch(
                reverse('patch_citizen',
                        kwargs={'import_id': self.import_instance.import_id,
                                'citizen_id': self.citizen1.citizen_id}),
                data=json.dumps(invalid_payload),
                content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_valid_patch_citizen_production(self):
        """Нагрузочный тест валидного PATCH запроса. Две пары значений"""
        i = 0
        flag = True
        while i < 100:
            if flag:
                response = client.patch(
                    reverse('patch_citizen',
                            kwargs={'import_id': self.import_instance.import_id,
                                    'citizen_id': self.citizen1.citizen_id}),
                    data=json.dumps(self.valid_payload1),
                    content_type='application/json'
                )
                self.assertEqual(response.data, self.expected_data1)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                flag = False
            elif not flag:
                response = client.patch(
                    reverse('patch_citizen',
                            kwargs={'import_id': self.import_instance.import_id,
                                    'citizen_id': self.citizen1.citizen_id}),
                    data=json.dumps(self.valid_payload2),
                    content_type='application/json'
                )
                self.assertEqual(response.data, self.expected_data2)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                flag = True
            i += 1


class GetPresents(TestCaseInitialData):
    """Тест GET список подарков"""

    # Заранее известный результат
    expected_data = {'data': {'1': [], '2': [], '3': [],
                                 '4': [{'citizen_id': 1, 'presents': 1}],
                                 '5': [], '6': [], '7': [], '8': [], '9': [],
                                 '10': [],
                                 '11': [{'citizen_id': 1, 'presents': 1}],
                                 '12': [{'citizen_id': 2, 'presents': 1},
                                        {'citizen_id': 3, 'presents': 1}]}}

    def test_get_valid_presents(self):
        """Тест статуса и ответа сервера при валидном запросе"""
        response = client.get(
            reverse('get_presents',
                    kwargs={'import_id': self.import_instance.import_id}))
        self.assertEqual(response.data, self.expected_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_presents(self):
        """Тест статуса сервера при запросе несуществующего импорта"""
        response = client.get(
            reverse('get_presents', kwargs={'import_id': 10}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_valid_presents_production(self):
        """Нагрузочное тестирование"""
        i = 0
        while i < 100:
            response = client.get(
                reverse('get_presents',
                        kwargs={'import_id': self.import_instance.import_id}))
            self.assertEqual(response.data, self.expected_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            i += 1


class GetPercentileAge(TestCaseInitialData):
    """Тест GET перцентили возрастов"""

    # Заранее известный результат
    expected_data = {
        'data': [{'town': 'Керчь', 'p50': 32.0, 'p75': 32.0, 'p99': 32.0},
                 {'town': 'Москва', 'p50': 27.0, 'p75': 29.5, 'p99': 31.9}]}

    def test_get_valid_percentile_age(self):
        """Тест статуса и ответа сервера при валидном запросе"""
        response = client.get(
            reverse('get_percentile_age',
                    kwargs={'import_id': self.import_instance.import_id}))
        self.assertEqual(response.data, self.expected_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_percentile_age(self):
        """Тест статуса сервера при запросе несуществующего импорта"""
        response = client.get(
            reverse('get_percentile_age', kwargs={'import_id': 10}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_valid_percentile_age_production(self):
        """Нагрузочное тестирование"""
        i = 0
        while i < 100:
            response = client.get(
                reverse('get_percentile_age',
                        kwargs={'import_id': self.import_instance.import_id}))
            self.assertEqual(response.data, self.expected_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            i += 1