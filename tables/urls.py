from django.urls import path
from . import views

urlpatterns = [
    path('select_table/', views.select_table, name='select_table'),
]
