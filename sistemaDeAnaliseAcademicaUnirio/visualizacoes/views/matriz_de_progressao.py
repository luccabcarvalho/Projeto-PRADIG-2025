from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from html import escape
import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go

USER_ID = 'user1'

FILTRAR_ALUNOS_POR_CURRICULO = True

TIPOS_DISCIPLINA = {
    'obrigatoria': 'Obrigatória',
    'optativa': 'Optativa',
}

COD_SEPARADOR = 'separador'
LABEL_SEPARADOR = 'Optativas'

# Ordem das cores na fila de optativas de cada aluno: verde (vencido), amarelo (inscrito), vermelho (não vencido)
ORDEM_COR = {1: 0, 0: 1, -1: 2}

CSS_MATRIZ = '''
<style>
.matriz-grade { display: grid; grid-template-columns: max-content max-content; width: max-content; background: white; font-family: Arial, sans-serif; font-size: 12px; color: #34495E; }
.matriz-canto { position: sticky; top: 0; left: 0; z-index: 4; background: white; }
.matriz-topo { position: sticky; top: 0; z-index: 3; background: white; height: var(--altura-topo); width: var(--largura-plot); }
.matriz-esq { position: sticky; left: 0; z-index: 2; background: white; }
.matriz-esq div { height: var(--altura-celula); line-height: var(--altura-celula); padding: 0 8px 0 10px; text-align: right; white-space: nowrap; }
.matriz-rotulo { position: absolute; bottom: 4px; transform-origin: left bottom; transform: rotate(-45deg); white-space: nowrap; }
.matriz-separador { font-weight: bold; }
</style>
'''

def _ler_csv(nome_arquivo, **kwargs):
    caminho = os.path.join(settings.MEDIA_ROOT, USER_ID, nome_arquivo)
    return pd.read_csv(caminho, **kwargs)

def _chave_versao(versao):
    ano, _, semestre = str(versao).partition('/')
    return (int(ano) if ano.isdigit() else 0, int(semestre) if semestre.isdigit() else 0)

def _versao_para_param(versao):
    return str(versao).replace('/', '')

def _largura_texto(texto, tamanho_fonte=12):
    # Estimativa da largura (px) de um texto em Arial: maiúsculas ocupam mais que minúsculas, espaços e pontuação menos
    return tamanho_fonte * sum(0.72 if c.isupper() else 0.28 if c in ' .,:;-/' else 0.56 for c in texto)

def montar_matriz_html(plot_div, alunos_labels, disciplinas_codigos, disciplinas_labels, plot_width, plot_height):
    # O Plotly não tem eixo fixo, então os nomes saem do gráfico e viram HTML com position: sticky
    # (alunos presos à esquerda, disciplinas presas ao topo) alinhado com as células do heatmap
    largura_celula = plot_width / len(disciplinas_codigos)
    altura_celula = plot_height / len(alunos_labels)
    altura_topo = int(max(_largura_texto(label) for label in disciplinas_labels) * 0.7071) + 24
    margem_direita = max(0, int(_largura_texto(disciplinas_labels[-1]) * 0.7071 - largura_celula / 2)) + 12

    rotulos_disciplinas = ''
    for j, (cod, label) in enumerate(zip(disciplinas_codigos, disciplinas_labels)):
        classe = 'matriz-rotulo matriz-separador' if cod == COD_SEPARADOR else 'matriz-rotulo'
        rotulos_disciplinas += f'<span class="{classe}" style="left:{(j + 0.5) * largura_celula:.2f}px">{escape(label)}</span>'
    rotulos_alunos = ''.join(f'<div>{escape(label)}</div>' for label in alunos_labels)

    estilo = (
        f'--altura-topo:{altura_topo}px; --altura-celula:{altura_celula:.4f}px; '
        f'--largura-plot:{plot_width}px; padding-right:{margem_direita}px'
    )
    return (
        CSS_MATRIZ
        + f'<div class="matriz-grade" style="{estilo}">'
        + '<div class="matriz-canto"></div>'
        + f'<div class="matriz-topo">{rotulos_disciplinas}</div>'
        + f'<div class="matriz-esq">{rotulos_alunos}</div>'
        + f'<div class="matriz-plot">{plot_div}</div>'
        + '</div>'
    )

def carregar_curriculos():
    df = _ler_csv('curriculos-bsi.csv', encoding='utf-8', sep=';')
    df['NUM VERSAO'] = df['NUM VERSAO'].astype(str).str.strip()
    df['COD DISCIPLINA'] = df['COD DISCIPLINA'].astype(str).str.strip()
    df['TIPO DISCIPLINA'] = df['TIPO DISCIPLINA'].astype(str).str.strip()
    df['PERIODO IDEAL'] = pd.to_numeric(df['PERIODO IDEAL'], errors='coerce').fillna(9999)
    df['NOME CURTO'] = df['NOME DISCIPLINA'].str.split(' - ', n=1).str[-1].str.strip()
    return df

def dicionario_de_equivalencias():
    df = _ler_csv('relacaoEquivalenciaDisciplinas.csv', encoding='latin1', sep=';')
    df_validos = df[df['NOME_DISC_EQUIV'].notna()][['NOME_DISCIPLINA', 'NOME_DISC_EQUIV']]
    
    codigos_novos = df_validos['NOME_DISCIPLINA'].str.split(' - ').str[0].str.strip()
    codigos_antigos = df_validos['NOME_DISC_EQUIV'].str.split(' - ').str[0].str.strip()
    
    mapeamento = {} 
    for antigo, novo in zip(codigos_antigos, codigos_novos):
        if novo not in mapeamento: 
            mapeamento[novo] = [] 
        mapeamento[novo].append(antigo) 
    return mapeamento

def status_para_num(status):
    if not isinstance(status, str):
        return np.nan
    s = status.strip().upper()
    
    if s.startswith(('APV', 'ADI', 'DIS')):
        return 1
    if s.startswith(('REP', 'REF')) or (s.startswith('TRA') and 'DISCIPLINA' in s): 
        return -1
    if s.startswith('MAT') or s.startswith('ASC'):
        if 'REPROVADO' in s:
            return -1
        return 0
        
    return np.nan 

def matriz_de_progressao(request):
    if not request.GET:
        return redirect(f"{reverse('matriz_de_progressao')}?curriculos=20232&tipo_disciplina=todas")

    df_alunos = _ler_csv('alunosPorCurso.csv', sep=None, engine='python')
    df_historico = _ler_csv('historicoEscolar.csv', sep=None, engine='python')
    df_curriculos = carregar_curriculos()
    equiv_map = dicionario_de_equivalencias()

    versoes_disponiveis = sorted(df_curriculos['NUM VERSAO'].unique(), key=_chave_versao, reverse=True)
    param_para_versao = {_versao_para_param(v): v for v in versoes_disponiveis}

    filtro_ativos = request.GET.get('ativos', 'todos')
    filtro_curriculos = request.GET.getlist('curriculos')
    filtro_tipo_disciplina = request.GET.get('tipo_disciplina', 'todas')

    versoes_selecionadas = [param_para_versao[c] for c in filtro_curriculos if c in param_para_versao]
    if not versoes_selecionadas:
        versoes_selecionadas = versoes_disponiveis

    curriculos_options = [
        {'value': _versao_para_param(v), 'label': f'Currículo {v}', 'selected': _versao_para_param(v) in filtro_curriculos}
        for v in versoes_disponiveis
    ]
    tipo_disciplina_options = [
        {'value': 'todas', 'label': 'Todas', 'selected': filtro_tipo_disciplina == 'todas'},
        {'value': 'obrigatoria', 'label': 'Obrigatórias', 'selected': filtro_tipo_disciplina == 'obrigatoria'},
        {'value': 'optativa', 'label': 'Optativas', 'selected': filtro_tipo_disciplina == 'optativa'},
    ]
    filtros_options = [
        {'name': 'ativos', 'label': 'Alunos ativos', 'selected': filtro_ativos == 'ativos'},
    ]

    def renderizar(plot_div='', mensagem=''):
        return render(request, 'matriz-de-progressao/matriz_de_progressao.html', {
            'plot_div': plot_div,
            'mensagem': mensagem,
            'curriculos_options': curriculos_options,
            'periodos_options': [],
            'filtros_options': filtros_options,
            'curriculos_selecionados': filtro_curriculos,
            'tipo_disciplina_options': tipo_disciplina_options,
            'tipo_disciplina_selecionado': filtro_tipo_disciplina,
        })

    origens_por_coluna = {}
    partes = []
    
    for versao in versoes_selecionadas:
        df_v = df_curriculos[df_curriculos['NUM VERSAO'] == versao]
        if filtro_tipo_disciplina in TIPOS_DISCIPLINA:
            df_v = df_v[df_v['TIPO DISCIPLINA'] == TIPOS_DISCIPLINA[filtro_tipo_disciplina]]
            
        for cod in df_v['COD DISCIPLINA']:
            origens = {cod}
            if cod in equiv_map:
                origens.update(equiv_map[cod])
            origens_por_coluna.setdefault(cod, set()).update(origens)
            
        partes.append(df_v)

    df_colunas = pd.concat(partes)
    df_colunas['ORDEM_TIPO'] = np.where(
        df_colunas['TIPO DISCIPLINA'].str.contains('Obrigatória', case=False, na=False), 
        1, 
        2
    )
    df_colunas = (
        df_colunas.sort_values(['ORDEM_TIPO', 'PERIODO IDEAL', 'COD DISCIPLINA'], kind='stable')
        .drop_duplicates('COD DISCIPLINA')
    )
    
    if df_colunas.empty:
        return renderizar(mensagem='Não há disciplinas para os filtros selecionados.')

    df_alunos['MATR ALUNO'] = df_alunos['MATR ALUNO'].astype(str).str.strip()
    df_alunos['NUM VERSAO'] = df_alunos['NUM VERSAO'].astype(str).str.strip()
    df_historico['MATR ALUNO'] = df_historico['MATR ALUNO'].astype(str).str.strip()
    df_historico['COD ATIV CURRIC'] = df_historico['COD ATIV CURRIC'].astype(str).str.strip()

    matr_historico = df_historico.drop_duplicates('ID PESSOA').set_index('ID PESSOA')['MATR ALUNO']
    invalida = ~df_alunos['MATR ALUNO'].str.fullmatch(r'\d+')
    df_alunos.loc[invalida, 'MATR ALUNO'] = (
        df_alunos.loc[invalida, 'ID PESSOA'].map(matr_historico).fillna('sem matrícula')
    )

    if filtro_ativos == 'ativos':
        df_alunos = df_alunos[df_alunos['FORMA EVASAO'] == 'Sem evasão']
    if FILTRAR_ALUNOS_POR_CURRICULO and filtro_curriculos:
        df_alunos = df_alunos[df_alunos['NUM VERSAO'].isin(versoes_selecionadas)]

    df_alunos = (
        df_alunos.drop_duplicates('ID PESSOA')
        .loc[lambda d: d['ID PESSOA'].isin(df_historico['ID PESSOA'])] 
        .sort_values(['MATR ALUNO', 'ID PESSOA'])
        .reset_index(drop=True)
    )
    n_alunos = len(df_alunos)
    if n_alunos == 0:
        return renderizar(mensagem='Não há alunos para os filtros selecionados.')

    alunos_ids = df_alunos['ID PESSOA'].tolist()
    nomes_alunos = df_alunos['NOME PESSOA'].tolist()
    alunos_labels = (df_alunos['MATR ALUNO'] + ' - ' + df_alunos['NOME PESSOA'].astype(str)).tolist()
    alunos_dict = {id_pessoa: i for i, id_pessoa in enumerate(alunos_ids)}

    pares = pd.DataFrame(
        [(origem, coluna) for coluna, origens in origens_por_coluna.items() for origem in origens],
        columns=['COD ATIV CURRIC', 'COD COLUNA'],
    )
    reg = df_historico[df_historico['ID PESSOA'].isin(alunos_dict)].merge(pares, on='COD ATIV CURRIC', how='inner')
    reg['VALOR'] = reg['DESCR SITUACAO'].map(status_para_num)
    reg['_r'] = reg['ID PESSOA'].map(alunos_dict)

    periodo_txt = reg['PERIODO'].fillna('').astype(str)
    semestre = periodo_txt.str.extract(r'(\d)')[0].fillna('?')
    semestre = pd.Series(np.where(periodo_txt.str.contains('rias', case=False), 'Férias', semestre), index=reg.index)
    ano = pd.to_numeric(reg['ANO'], errors='coerce').fillna(0).astype(int)
    reg['ANO_PERIODO'] = ano.astype(str) + '.' + semestre
    reg['ORDEM'] = ano * 10 + np.where(semestre == '1', 1, 2)
    reg = reg.sort_values('ORDEM', ascending=False, kind='stable') 

    # Situação final de cada aluno em cada disciplina (a cor da célula)
    valido = reg.dropna(subset=['VALOR'])
    chave = [valido['_r'], valido['COD COLUNA']]
    ultimo = valido.groupby(chave)['VALOR'].first()
    aprovado = (valido['VALOR'] == 1).groupby(chave).any()
    final = ultimo.mask(aprovado.reindex(ultimo.index)) 
    final = final.fillna(pd.Series(np.where(aprovado.reindex(final.index), 1, np.nan), index=final.index))
    primeira = valido.groupby(chave)['ORDEM'].min()

    # Fila de optativas de cada aluno: verdes, amarelas e vermelhas; dentro de cada cor, 
    # pela primeira vez em que a disciplina aparece no histórico (desempate pelo código)
    optativas_codigos = df_colunas.loc[df_colunas['ORDEM_TIPO'] == 2, 'COD DISCIPLINA'].tolist()
    fila_optativas = pd.DataFrame({'VALOR': final, 'PRIMEIRA': primeira}).reset_index()
    fila_optativas = fila_optativas[fila_optativas['COD COLUNA'].isin(optativas_codigos)].copy()
    fila_optativas['COR'] = fila_optativas['VALOR'].map(ORDEM_COR)
    fila_optativas = fila_optativas.sort_values(['_r', 'COR', 'PRIMEIRA', 'COD COLUNA'], kind='stable')
    fila_optativas['_slot'] = fila_optativas.groupby('_r').cumcount()
    n_optativas = int(fila_optativas['_slot'].max()) + 1 if len(fila_optativas) else 0

    obrigatorias = df_colunas[df_colunas['ORDEM_TIPO'] == 1]
    disciplinas_codigos = obrigatorias['COD DISCIPLINA'].tolist()
    disciplinas_labels = obrigatorias['NOME CURTO'].tolist()
    nome_por_codigo = dict(zip(df_colunas['COD DISCIPLINA'], df_colunas['NOME CURTO']))

    primeira_optativa = len(disciplinas_codigos) + (1 if disciplinas_codigos else 0)
    if n_optativas:
        if disciplinas_codigos:
            disciplinas_codigos.append(COD_SEPARADOR)
            disciplinas_labels.append(LABEL_SEPARADOR)
        for k in range(1, n_optativas + 1):
            disciplinas_codigos.append(f'optativa_{k}')
            disciplinas_labels.append(f'Optativa {k}')

    if not disciplinas_codigos:
        return renderizar(mensagem='Nenhum aluno cursou optativas para os filtros selecionados.')

    n_disciplinas = len(disciplinas_codigos)
    disciplinas_dict = {cod: j for j, cod in enumerate(disciplinas_codigos)}

    z = np.full((n_alunos, n_disciplinas), np.nan)
    textos = np.full((n_alunos, n_disciplinas), '', dtype=object)

    if not reg.empty:
        reg = reg.merge(fila_optativas[['_r', 'COD COLUNA', '_slot']], on=['_r', 'COD COLUNA'], how='left')
        reg['_c'] = reg['COD COLUNA'].map(disciplinas_dict).fillna(primeira_optativa + reg['_slot'])
        reg = reg.dropna(subset=['_c']).astype({'_c': int})

        if len(final):
            coluna_do_par = reg.drop_duplicates(['_r', 'COD COLUNA']).set_index(['_r', 'COD COLUNA'])['_c']
            z[final.index.get_level_values(0).astype(int), coluna_do_par.reindex(final.index).astype(int).values] = final.values

        status = reg['DESCR SITUACAO'].fillna('').astype(str).str.strip()
        nota = reg['MEDIA FINAL'].fillna('').astype(str).str.strip()
        nota = (' (nota: ' + nota + ')').where(nota != '', '')

        reg['LINHA_HIST'] = '• ' + reg['ANO_PERIODO'] + ' - ' + status + nota
        agrupado = reg.groupby(['_r', '_c'], sort=False).agg(
            cod=('COD COLUNA', 'first'),
            historico=('LINHA_HIST', '<br>'.join),
        )
        for (r, c), linha in zip(agrupado.index, agrupado.itertuples(index=False)):
            textos[r, c] = f"{nomes_alunos[r]}<br>{nome_por_codigo[linha.cod]}<br>{linha.historico}"

    plot_width = max(1100, n_disciplinas * 50)
    plot_height = max(550, n_alunos * 32)

    fig = go.Figure(data=go.Heatmap(
    z=z.tolist(),
    x=disciplinas_codigos,
    y=alunos_labels,
    text=textos.tolist(),
    hovertemplate='%{text}<extra></extra>',

    colorscale=[
        [0.0, '#D9534F'],   # Não vencido ou inscrição anterior
        [0.5, '#F4C95D'],   # Inscrito
        [1.0, '#4CAF78']    # Vencido
    ],

    zmin=-1,
    zmax=1,
    showscale=False,

    xgap=2,
    ygap=2
))

    if COD_SEPARADOR in disciplinas_dict:
        pos_separador = disciplinas_dict[COD_SEPARADOR]
        fig.add_vrect(
            x0=pos_separador - 0.5,
            x1=pos_separador + 0.5,
            fillcolor='#E3E9EF',
            line_width=0,
            layer='above'
        )

    fig.update_layout(
    font=dict(
        family='Arial, sans-serif',
        size=13,
        color='#25364A'
    ),

    xaxis=dict(
        type='category',
        visible=False,
        fixedrange=True
    ),

    yaxis=dict(
        type='category',
        autorange='reversed',
        visible=False,
        fixedrange=True
    ),

    autosize=False,
    width=plot_width,
    height=plot_height,

    margin=dict(
        l=0,
        r=0,
        t=0,
        b=0
    ),

    hovermode='closest',

    hoverlabel=dict(
        bgcolor='white',
        bordercolor='#D5DCE3',
        font=dict(
            family='Arial, sans-serif',
            size=13,
            color='#25364A'
        ),
        align='left'
    ),

    plot_bgcolor='white',
    paper_bgcolor='white'
)
    plot_div = fig.to_html(full_html=False, config={'displayModeBar': False})
    return renderizar(plot_div=montar_matriz_html(plot_div, alunos_labels, disciplinas_codigos, disciplinas_labels, plot_width, plot_height))