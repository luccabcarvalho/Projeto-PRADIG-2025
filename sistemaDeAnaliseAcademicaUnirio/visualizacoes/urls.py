from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('hub/', views.visualizacoes_hub, name='visualizacoes_hub'),
    path('desempenho/', views.desempenho_aluno_periodo, name='desempenho_aluno_periodo'),
    path('heatmap/', views.heatmap_desempenho, name='heatmap_desempenho'),
    path('integralizacao/', views.status_integralizacao, name='status_integralizacao'),
    path('gerenciar-arquivos/', views.gerenciar_arquivos, name='gerenciar_arquivos'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)