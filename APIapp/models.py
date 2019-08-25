from django.db import models


GENDER_CHOICES = [
    ("male", "male"),
    ("female", "female"),
]


class ImportId(models.Model):
    # Уникальный импорт с инкремнтацией. Для одновременных post requests
    # При удалении данных в PostgreSQL (хотя нам это и не нужно),
    # pk не возвращается к единице.
    # Только DROP TABLE поможет, если нужно обнулить это поле
    import_id = models.AutoField(primary_key=True)

    def __str__(self):
        return 'Import {}'.format(self.import_id)


class CitizenInfo(models.Model):
    citizen_id = models.PositiveIntegerField()
    import_id = models.ForeignKey(ImportId, on_delete=models.CASCADE)
    town = models.CharField(max_length=256)
    street = models.CharField(max_length=256)
    building = models.CharField(max_length=256)
    apartment = models.PositiveIntegerField()
    name = models.CharField(max_length=256)
    # Хранит значения в виде Y-m-d. При сериализации
    # преобразуем в d.m.Y
    birth_date = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    # Хранит значения в виде pk. При сериализации преобразуем в список
    # из citizen_id в рамках импорта.
    relatives = models.ManyToManyField('self', blank=True)

    def __str__(self):
        return 'Citizen {} from {}'.format(self.citizen_id, self.import_id)

    class Meta:
        # Айдишники импорта и гражданина образуют уникальную пару
        ordering = ['citizen_id']
        unique_together = ('import_id', 'citizen_id',)
