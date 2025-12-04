from django.urls import path
from . import views
from .views import home, matriz_de_progressao, prazos_de_integralizacao, progressao_individual, gerenciar_arquivos, checar_arquivos_necessarios
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('desempenho/', progressao_individual, name='progressao_individual'),
    path('heatmap/', matriz_de_progressao, name='matriz_de_progressao'),
    path('integralizacao/', prazos_de_integralizacao, name='prazos_de_integralizacao'),
    path('gerenciar-arquivos/', gerenciar_arquivos, name='gerenciar_arquivos'),
    path('checar-arquivos/', checar_arquivos_necessarios, name='checar_arquivos_necessarios'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)