from django.urls import path
from . import views
from .views import home, matriz_de_progressao, prazos_de_integralizacao, progressao_individual, progressao_turma, gerenciar_arquivos, checar_arquivos_necessarios, progresso, migracao
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('login/', views.login_google, name='login_google'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('', home, name='home'),
    path('progresso/', progresso, name='progresso'),
    path('migracao/', migracao, name='migracao'),
    path('desempenho/', progressao_individual, name='progressao_individual'),
    path('progressao-turma/', progressao_turma, name='progressao_turma'),
    path('heatmap/', matriz_de_progressao, name='matriz_de_progressao'),
    path('integralizacao/', prazos_de_integralizacao,
         name='prazos_de_integralizacao'),
    path('gerenciar-arquivos/', gerenciar_arquivos, name='gerenciar_arquivos'),
    path('checar-arquivos/', checar_arquivos_necessarios,
         name='checar_arquivos_necessarios'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
