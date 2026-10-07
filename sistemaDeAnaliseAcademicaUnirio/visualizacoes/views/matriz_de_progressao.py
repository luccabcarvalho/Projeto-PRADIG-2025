from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
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

def _ler_csv(nome_arquivo, **kwargs):
    caminho = os.path.join(settings.MEDIA_ROOT, USER_ID, nome_arquivo)
    return pd.read_csv(caminho, **kwargs)

def _chave_versao(versao):
    ano, _, semestre = str(versao).partition('/')
    return (int(ano) if ano.isdigit() else 0, int(semestre) if semestre.isdigit() else 0)

def _versao_para_param(versao):
    return str(versao).replace('/', '')

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
        return redirect(f"{reverse('matriz_de_progressao')}?curriculos=20232&tipo_disciplina=obrigatoria")

    df_alunos = _ler_csv('alunosPorCurso.csv', sep=None, engine='python')
    df_historico = _ler_csv('historicoEscolar.csv', sep=None, engine='python')
    df_curriculos = carregar_curriculos()
    equiv_map = dicionario_de_equivalencias()

    versoes_disponiveis = sorted(df_curriculos['NUM VERSAO'].unique(), key=_chave_versao, reverse=True)
    param_para_versao = {_versao_para_param(v): v for v in versoes_disponiveis}

    filtro_ativos = request.GET.get('ativos', 'todos')
    filtro_curriculos = request.GET.getlist('curriculos')
    filtro_tipo_disciplina = request.GET.get('tipo_disciplina', 'obrigatoria')

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
    
    disciplinas_codigos = df_colunas['COD DISCIPLINA'].tolist()
    disciplinas_labels = df_colunas['NOME CURTO'].tolist()
    nome_por_codigo = dict(zip(disciplinas_codigos, disciplinas_labels))
    if not disciplinas_codigos:
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
    n_disciplinas = len(disciplinas_codigos)
    if n_alunos == 0:
        return renderizar(mensagem='Não há alunos para os filtros selecionados.')

    alunos_ids = df_alunos['ID PESSOA'].tolist()
    nomes_alunos = df_alunos['NOME PESSOA'].tolist()
    alunos_labels = (df_alunos['MATR ALUNO'] + ' - ' + df_alunos['NOME PESSOA'].astype(str)).tolist()
    alunos_dict = {id_pessoa: i for i, id_pessoa in enumerate(alunos_ids)}
    disciplinas_dict = {cod: j for j, cod in enumerate(disciplinas_codigos)}

    pares = pd.DataFrame(
        [(origem, coluna) for coluna, origens in origens_por_coluna.items() for origem in origens],
        columns=['COD ATIV CURRIC', 'COD COLUNA'],
    )
    reg = df_historico[df_historico['ID PESSOA'].isin(alunos_dict)].merge(pares, on='COD ATIV CURRIC', how='inner')

    z = np.full((n_alunos, n_disciplinas), np.nan)
    textos = np.full((n_alunos, n_disciplinas), '', dtype=object)

    if not reg.empty:
        reg = reg.copy()
        reg['VALOR'] = reg['DESCR SITUACAO'].map(status_para_num)

        periodo_txt = reg['PERIODO'].fillna('').astype(str)
        semestre = periodo_txt.str.extract(r'(\d)')[0].fillna('?')
        semestre = pd.Series(np.where(periodo_txt.str.contains('rias', case=False), 'Férias', semestre), index=reg.index)
        ano = pd.to_numeric(reg['ANO'], errors='coerce').fillna(0).astype(int)
        reg['ANO_PERIODO'] = ano.astype(str) + '.' + semestre
        reg['ORDEM'] = ano * 10 + np.where(semestre == '1', 1, 2)

        reg['_r'] = reg['ID PESSOA'].map(alunos_dict)
        reg['_c'] = reg['COD COLUNA'].map(disciplinas_dict)
        reg = reg.sort_values('ORDEM', ascending=False, kind='stable') 

        valido = reg.dropna(subset=['VALOR'])
        chave = [valido['_r'], valido['_c']]
        ultimo = valido.groupby(chave)['VALOR'].first()
        aprovado = (valido['VALOR'] == 1).groupby(chave).any()
        final = ultimo.mask(aprovado.reindex(ultimo.index)) 
        final = final.fillna(pd.Series(np.where(aprovado.reindex(final.index), 1, np.nan), index=final.index))
        
        if len(final):
            z[final.index.get_level_values(0).astype(int), final.index.get_level_values(1).astype(int)] = final.values

        status = reg['DESCR SITUACAO'].fillna('').astype(str).str.strip()
    
        reg['LINHA_HIST'] = status + ' (' + reg['ANO_PERIODO'] + ') '
        reg['LINHA_UNICA'] = (
            '  Status: ' + status + '<br>'
            + reg['ANO_PERIODO']
        )
        agrupado = reg.groupby(['_r', '_c'], sort=False).agg(
            n=('LINHA_HIST', 'size'),
            historico=('LINHA_HIST', '<br>'.join),
            unica=('LINHA_UNICA', 'first'),
        )
        for (r, c), linha in zip(agrupado.index, agrupado.itertuples(index=False)):
            cabecalho = f"{nomes_alunos[r]}<br>{nome_por_codigo[disciplinas_codigos[c]]}<br>"
            if linha.n == 1:
                textos[r, c] = cabecalho + linha.unica
            else:
                textos[r, c] = cabecalho + "Histórico: <br>" + linha.historico

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

    fig.update_layout(
    font=dict(
        family='Arial, sans-serif',
        size=13,
        color='#25364A'
    ),

    xaxis=dict(
        side='top',
        type='category',
        tickmode='array',
        tickvals=disciplinas_codigos,
        ticktext=disciplinas_labels,
        tickangle=-45,
        tickfont=dict(
            size=12,
            color='#34495E'
        ),
        fixedrange=True,
        automargin=True,
        showgrid=False,
        zeroline=False
    ),

    yaxis=dict(
        tickfont=dict(
            size=12,
            color='#34495E'
        ),
        fixedrange=True,
        autorange='reversed',
        automargin=True,
        showgrid=False,
        zeroline=False
    ),

    autosize=False,
    width=plot_width,
    height=plot_height,

    margin=dict(
        l=10,
        r=20,
        t=150,
        b=20
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
    return renderizar(plot_div=fig.to_html(full_html=False, config={'displayModeBar': False}))