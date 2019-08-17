from rest_framework import serializers
from .models import CitizenInfo


class CitizenListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CitizenInfo
        fields = '__all__'


