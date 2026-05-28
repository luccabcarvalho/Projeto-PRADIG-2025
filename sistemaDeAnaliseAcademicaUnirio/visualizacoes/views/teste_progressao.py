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
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    equivalencias_path = os.path.join(USER_DIR, 'relacaoEquivalenciaDisciplinas.csv')
    df = pd.read_csv(equivalencias_path, encoding='latin1', sep=';')

    df_validos = df[df['NOME_DISC_EQUIV'].notna()][['NOME_DISCIPLINA', 'NOME_DISC_EQUIV']]

    # Extrai apenas o código (parte antes do ' - ')
    codigos_novos   = df_validos['NOME_DISCIPLINA'].str.split(' - ').str[0].str.strip()
    codigos_antigos = df_validos['NOME_DISC_EQUIV'].str.split(' - ').str[0].str.strip()

    mapeamento = {} # Dicionário vazio
    for antigo, novo in zip(codigos_antigos, codigos_novos): # Itera sobre os códigos formando pares
        if antigo not in mapeamento: # Se o código antigo ainda não tiver sido adicionado ao dicionário
            mapeamento[antigo] = [] # Inicia uma lista vazia para armazenar códigos equivalentes
        mapeamento[antigo].append(novo) # Anexa o código novo na lista do código antigo equivalente

    # Dict comprehension
    equivalencias = {
        antigo: (nomes[0] if len(nomes) == 1 else nomes) # Se antigo tiver apenas uma equivalência, retorna uma string. Mais de uma, retorna uma lista.
        for antigo, nomes in mapeamento.items() # Itera sobre o mapeamento retornando pares de antigo e nomes
    }

    return equivalencias