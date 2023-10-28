from django.urls import path
from . import views

urlpatterns = [
    path('', views.select_data, name='data'),
    path('generate_pdf/<str:station_address>/', views.generate_pdf, name='generate_pdf'),
]
