from django.urls import path
from . import views

urlpatterns = [
    path('status-integralizacao/', views.status_integralizacao, name='status_integralizacao'),
]