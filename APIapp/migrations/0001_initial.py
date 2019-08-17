# Generated by Django 2.2.4 on 2019-08-17 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CitizenInfo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('citizen_id', models.PositiveIntegerField()),
                ('import_id', models.PositiveIntegerField()),
                ('town', models.CharField(max_length=255)),
                ('street', models.CharField(max_length=255)),
                ('building', models.CharField(max_length=255)),
                ('apartment', models.PositiveIntegerField()),
                ('name', models.CharField(max_length=255)),
                ('bitrh_date', models.DateField()),
                ('gender', models.CharField(choices=[('male', 'male'), ('female', 'female')], max_length=10)),
                ('relatives', models.ManyToManyField(blank=True, related_name='_citizeninfo_relatives_+', to='APIapp.CitizenInfo')),
            ],
            options={
                'unique_together': {('import_id', 'citizen_id')},
            },
        ),
    ]