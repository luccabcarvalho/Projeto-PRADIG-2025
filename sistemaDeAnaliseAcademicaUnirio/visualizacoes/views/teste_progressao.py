from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import plotly.graph_objects as go

USER_ID = 'user1'

# Conjuntos que classificam a forma de evasão para determinar a cor do marcador final
EVASAO_BOA = {'CON - Curso concluído'}   # verde
EVASAO_SEM = {'Sem evasão'}              # sem destaque (aluno ainda ativo)

