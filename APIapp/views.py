from django.shortcuts import render
from rest_framework import generics
from .serializers import CitizenListSerializer
from .models import CitizenInfo




class CitizenCreateView(generics.CreateAPIView):
    serializer_class = CitizenListSerializer



class CitizenListView(generics.ListAPIView):
    # Сейчас все вызыываем, исправить на конкретный import_id
    serializer_class = CitizenListSerializer
    queryset = CitizenInfo.objects.all()


