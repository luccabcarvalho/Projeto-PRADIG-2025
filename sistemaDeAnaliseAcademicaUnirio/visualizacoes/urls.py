from django.urls import path
from . import views

urlpatterns = [
    path('status-integralizacao/', views.status_integralizacao, name='status_integralizacao'),
    path('desempenho-aluno-periodo/', views.desempenho_aluno_periodo, name='desempenho_aluno_periodo'),
    path('heatmap-desempenho/', views.heatmap_desempenho, name='heatmap_desempenho'),
]