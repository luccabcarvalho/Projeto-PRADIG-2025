from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import plotly.graph_objects as go

USER_ID = 'user1'

# Conjuntos que classificam a forma de evasão para determinar a cor do marcador final
EVASAO_BOA = {'CON - Curso concluído'}   # verde
EVASAO_SEM = {'Sem evasão'}              # sem destaque (aluno ainda ativo)

def dicionario_de_equivalencias():
    # Carrega o arquivo de equivalências
    caminho_arquivo = os.path.join(USER_DIR, 'alunosP')
    df_equivalencias = pd.read_csv(caminho_arquivo)
    
    # Cria um dicionário de equivalências
    
    
    return equivalencias