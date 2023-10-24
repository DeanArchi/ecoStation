from django.urls import path
from . import views

urlpatterns = [
    path('', views.select_table, name='tables'),
]
