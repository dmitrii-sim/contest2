import json
from rest_framework import status
from django.test import TestCase, Client
from django.urls import reverse
from ..models import CitizenInfo


client = Client()


class PostCitizensTest(TestCase):
    """ Тест POST запроса """

    def setUp(self):
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
        self.invalid_payload1 = {"citizens":[]}
        self.invalid_payload2 = {"citizens":[{}]}
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
        response = client.post(
            reverse('post_citizens'),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        self.assertEqual(response.data, {'data': {'import_id': 1}})
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


class GetCitizensFromImportTest(TestCase):
    """Тест для GET запросов"""

    def setUp(self):
        self.citizen1 = CitizenInfo.objects.create(
            citizen_id=1, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Иван Иванович",
            birth_date="1986-12-26", gender="male"
        )
        self.citizen2 = CitizenInfo.objects.create(
            citizen_id=2, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Сергей Иванович",
            birth_date="1997-04-01", gender="male"
        )
        self.citizen3 = CitizenInfo.objects.create(
            citizen_id=3, import_id=1, town="Керчь", street="Иосифа Бродского",
            building="2", apartment=11, name="Романова Мария Леонидовна",
            birth_date="1986-11-23", gender="female"
        )
        # Добавляем m2m, она симметрична
        self.citizen1.relatives.add(self.citizen2, self.citizen3)

    def test_get_valid_import_citizens_list(self):
        """Тест статуса и ответа сервера при валидном запросе"""
        response = client.get(
            reverse('get_all_import_citizens',
                    kwargs={'import_id': self.citizen1.import_id}))
        # Заранее известный результат
        correct_response = {'data': [{'citizen_id': 1, 'town': 'Москва', 'street': 'Льва Толстого', 'building': '16к7стр5', 'apartment': 7, 'name': 'Иванов Иван Иванович', 'birth_date': '26.12.1986', 'gender': 'male', 'relatives': [2, 3]}, {'citizen_id': 2, 'town': 'Москва', 'street': 'Льва Толстого', 'building': '16к7стр5', 'apartment': 7, 'name': 'Иванов Сергей Иванович', 'birth_date': '01.04.1997', 'gender': 'male', 'relatives': [1]}, {'citizen_id': 3, 'town': 'Керчь', 'street': 'Иосифа Бродского', 'building': '2', 'apartment': 11, 'name': 'Романова Мария Леонидовна', 'birth_date': '23.11.1986', 'gender': 'female', 'relatives': [1]}]}
        self.assertEqual(response.data, correct_response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_import_citizens_list(self):
        """Тест статуса сервера при запросе несуществующего импорта"""
        response = client.get(
            reverse('get_all_import_citizens', kwargs={'import_id': 10}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PatchCitizenTest(TestCase):
    """ Тест PATCH запроса """
    def setUp(self):
        self.citizen1 = CitizenInfo.objects.create(
            citizen_id=1, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Иван Иванович",
            birth_date="1986-12-26", gender="male"
        )
        self.citizen2 = CitizenInfo.objects.create(
            citizen_id=2, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Сергей Иванович",
            birth_date="1997-04-01", gender="male"
        )
        self.citizen3 = CitizenInfo.objects.create(
            citizen_id=3, import_id=1, town="Керчь", street="Иосифа Бродского",
            building="2", apartment=11, name="Романова Мария Леонидовна",
            birth_date="1986-11-23", gender="female"
        )
        # Добавляем m2m, она симметрична
        self.citizen1.relatives.add(self.citizen2)
        self.valid_payload = {
            "town": "Москва",
            "street": "Льва Толстого",
            "building": "16к7стр5",
            "apartment": 7,
            "name": "Иванова Мария Леонидовна",
            "relatives": [1]
        }
        self.invalid_payload1 = {}
        self.invalid_payload2 = {
            "citizen_id": 1,
            "town": "Москва"
        }
        self.invalid_payload3 = {
            "tn": "Москва",
        }
        self.invalid_payload4 = {
            "birth_date": "-26.12.1986",
            "gender": "male",
            "relatives": []
        }
        self.invalid_payload5 = {
            "gender": "apache69",
        }
        self.invalid_payload9 = {
            "apartment": -7,
        }
        self.invalid_payload10 = {
            "relatives": ["2"]
        }
        self.invalid_payloads = [self.invalid_payload1, self.invalid_payload2,
                                 self.invalid_payload3, self.invalid_payload4,
                                 self.invalid_payload5, self.invalid_payload9,
                                 self.invalid_payload10]
        # Добавляем m2m, она симметрична
        self.citizen1.relatives.add(self.citizen2)

    def test_valid_patch_citizen(self):
        """Тест успешный ответ и статус"""
        response = client.patch(
            reverse('patch_citizen',
                    kwargs={'import_id': self.citizen1.import_id,
                            'citizen_id': self.citizen1.citizen_id}),
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        correct_response = {'data': {'citizen_id': 1, 'town': 'Москва', 'street': 'Льва Толстого', 'building': '16к7стр5', 'apartment': 7, 'name': 'Иванова Мария Леонидовна', 'birth_date': '26.12.1986', 'gender': 'male', 'relatives': [1]}}
        self.assertEqual(response.data, correct_response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_patch_citizen(self):
        """Тест невалидные данные"""
        for invalid_payload in self.invalid_payloads:
            response = client.patch(
                reverse('patch_citizen',
                        kwargs={'import_id': self.citizen1.import_id,
                                'citizen_id': self.citizen1.citizen_id}),
                data=json.dumps(invalid_payload),
                content_type='application/json')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class GetPresents(TestCase):
    """Тест GET список подарков"""

    def setUp(self):
        self.citizen1 = CitizenInfo.objects.create(
            citizen_id=1, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Иван Иванович",
            birth_date="1986-12-26", gender="male"
        )
        self.citizen2 = CitizenInfo.objects.create(
            citizen_id=2, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Сергей Иванович",
            birth_date="1997-04-01", gender="male"
        )
        self.citizen3 = CitizenInfo.objects.create(
            citizen_id=3, import_id=1, town="Керчь", street="Иосифа Бродского",
            building="2", apartment=11, name="Романова Мария Леонидовна",
            birth_date="1986-11-23", gender="female"
        )
        # Добавляем m2m, она симметрична
        self.citizen1.relatives.add(self.citizen2, self.citizen3)

    def test_get_valid_presents(self):
        """Тест статуса и ответа сервера при валидном запросе"""
        response = client.get(
            reverse('get_presents',
                    kwargs={'import_id': self.citizen1.import_id}))
        # Заранее известный результат
        correct_response = {'data': {'1': [], '2': [], '3': [], '4': [{'citizen_id': 1, 'presents': 1}], '5': [], '6': [], '7': [], '8': [], '9': [], '10': [], '11': [{'citizen_id': 1, 'presents': 1}], '12': [{'citizen_id': 2, 'presents': 1}, {'citizen_id': 3, 'presents': 1}]}}
        self.assertEqual(response.data, correct_response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_presents(self):
        """Тест статуса сервера при запросе несуществующего импорта"""
        response = client.get(
            reverse('get_presents', kwargs={'import_id': 10}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetPercentileAge(TestCase):
    """Тест GET перцентили возрастов"""

    def setUp(self):
        self.citizen1 = CitizenInfo.objects.create(
            citizen_id=1, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Иван Иванович",
            birth_date="1986-12-26", gender="male"
        )
        self.citizen2 = CitizenInfo.objects.create(
            citizen_id=2, import_id=1, town="Москва", street="Льва Толстого",
            building="16к7стр5", apartment=7, name="Иванов Сергей Иванович",
            birth_date="1997-04-01", gender="male"
        )
        self.citizen3 = CitizenInfo.objects.create(
            citizen_id=3, import_id=1, town="Керчь", street="Иосифа Бродского",
            building="2", apartment=11, name="Романова Мария Леонидовна",
            birth_date="1986-11-23", gender="female"
        )
        # Добавляем m2m, она симметрична
        self.citizen1.relatives.add(self.citizen2, self.citizen3)

    def test_get_valid_percentile_age(self):
        """Тест статуса и ответа сервера при валидном запросе"""
        response = client.get(
            reverse('get_percentile_age',
                    kwargs={'import_id': self.citizen1.import_id}))
        # Заранее известный результат
        correct_response = {'data': [{'town': 'Керчь', 'p50': 32.0, 'p75': 32.0, 'p99': 32.0}, {'town': 'Москва', 'p50': 27.0, 'p75': 29.5, 'p99': 31.9}]}
        self.assertEqual(response.data, correct_response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_invalid_percentile_age(self):
        """Тест статуса сервера при запросе несуществующего импорта"""
        response = client.get(
            reverse('get_percentile_age', kwargs={'import_id': 10}))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
