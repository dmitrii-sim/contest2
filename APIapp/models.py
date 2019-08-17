from django.db import models

# Create your models here.

GENDER_CHOICES = [
    ("male", "male"),
    ("female", "female"),
]


class CitizenInfo(models.Model):
    citizen_id = models.PositiveIntegerField()
    import_id = models.PositiveIntegerField()
    town = models.CharField(max_length=255)
    street = models.CharField(max_length=255)
    building = models.CharField(max_length=255)
    apartment = models.PositiveIntegerField()
    name = models.CharField(max_length=255)
    bitrh_date = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    # Приходит в виде номера PK по дефолту, нужно будет вручную исправлять при передаче и приеме
    relatives = models.ManyToManyField('self', blank=True)

    class Meta:
        # Айдишники импорта и человека образуют уникальную пару
        unique_together = ('import_id', 'citizen_id',)
