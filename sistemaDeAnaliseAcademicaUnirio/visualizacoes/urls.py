from django.urls import path
from . import views
from views import matriz_de_progressao
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('desempenho/', views.desempenho_aluno_periodo, name='desempenho_aluno_periodo'),
    path('heatmap/', matriz_de_progressao, name='matriz_de_progressao'),
    path('integralizacao/', views.status_integralizacao, name='status_integralizacao'),
    path('gerenciar-arquivos/', views.gerenciar_arquivos, name='gerenciar_arquivos'),
    path('checar-arquivos/', views.checar_arquivos_necessarios, name='checar_arquivos_necessarios'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)