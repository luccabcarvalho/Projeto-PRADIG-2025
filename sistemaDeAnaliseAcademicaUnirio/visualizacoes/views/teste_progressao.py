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
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID) # Definindo caminhos dos arquivos
    equivalencias_path = os.path.join(USER_DIR, 'relacaoEquivalenciaDisciplinas.csv')
    df_equivalencias = pd.read_csv(equivalencias_path, encoding='latin1', sep=';')
    
    VERSION_ORDER = ['2002/2', '2005/2', '2008/1', '2023/2']

    # Inicializa todas as versões com dicts vazios
    equivalencias = {v: {} for v in VERSION_ORDER}

    # Filtra o dataframe para incluir apenas as linhas com equivalências
    df_validos = df_equivalencias[df_equivalencias['NOME_DISC_EQUIV'].notna()][['NUM_VERSAO', 'NOME_DISCIPLINA', 'NOME_DISC_EQUIV']]