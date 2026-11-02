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

COD_SEPARADOR = 'separador'
LABEL_SEPARADOR = '<b>Optativas</b>'

PREFIXO_COD_OPTATIVA = 'optativa_'
PREFIXO_LABEL_OPTATIVA = 'Optativa '

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

def _formatar_notas(serie):
    """Converte a coluna de nota em texto no padrão brasileiro (ex.: '7,4').
    Devolve '' quando a cursagem não tem nota."""
    texto = serie.astype(str).str.strip()
    vazio = serie.isna() | texto.str.lower().isin(['', 'nan', 'none', '<na>'])
    numero = pd.to_numeric(texto.str.replace(',', '.', regex=False), errors='coerce')
    formatado = numero.map(lambda v: f'{v:g}'.replace('.', ',') if pd.notna(v) else '')
    return formatado.where(numero.notna(), texto).where(~vazio, '')

def _preparar_registros(reg):
    """Cria período, ordem cronológica e a linha de hover de cada cursagem.
    Devolve os registros ordenados da cursagem mais recente para a mais antiga."""
    reg = reg.copy()

    periodo_txt = reg['PERIODO'].fillna('').astype(str)
    semestre = periodo_txt.str.extract(r'(\d)')[0].fillna('?')
    semestre = pd.Series(np.where(periodo_txt.str.contains('rias', case=False), 'Férias', semestre), index=reg.index)
    ano = pd.to_numeric(reg['ANO'], errors='coerce').fillna(0).astype(int)
    reg['ANO_PERIODO'] = ano.astype(str) + '.' + semestre
    reg['ORDEM'] = ano * 10 + np.where(semestre == '1', 1, 2)

    status = reg['DESCR SITUACAO'].fillna('').astype(str).str.strip()
    if 'MEDIA FINAL' in reg.columns:
        nota = _formatar_notas(reg['MEDIA FINAL'])
    else:
        nota = pd.Series('', index=reg.index)
    sufixo_nota = (' (nota ' + nota + ')').where(nota != '', '')

    # • período: situação (nota, se houver)
    reg['LINHA_HIST'] = '• ' + reg['ANO_PERIODO'] + ': ' + status + sufixo_nota

    return reg.sort_values('ORDEM', ascending=False, kind='stable')

def _valor_final(valido, chaves):
    """Valor final de cada célula: 1 se houve alguma aprovação; caso contrário, o valor
    da cursagem mais recente. 'valido' deve estar ordenado do mais recente ao mais antigo."""
    ultimo = valido.groupby(chaves)['VALOR'].first()
    aprovado = valido.assign(_ok=valido['VALOR'] == 1).groupby(chaves)['_ok'].any()
    return ultimo.mask(aprovado.reindex(ultimo.index), 1)

def _agrupar_optativas(origens_por_coluna, codigos_optativas):
    """Une optativas ligadas por equivalência (ex.: código antigo e novo da mesma disciplina),
    para que uma mesma optativa ocupe uma única posição 'Optativa N' do aluno."""
    pai = {cod: cod for cod in codigos_optativas}

    def achar(x):
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    dono = {}
    for cod in codigos_optativas:
        for origem in origens_por_coluna[cod]:
            if origem in dono:
                pai[achar(cod)] = achar(dono[origem])
            else:
                dono[origem] = cod
    return {cod: achar(cod) for cod in codigos_optativas}

def _slots_optativas(reg_opt):
    """Uma linha por (aluno, optativa) com o valor final da célula e a posição dela na
    linha do aluno: Optativa 1, 2, 3... por ordem cronológica da primeira cursagem."""
    valido = reg_opt.dropna(subset=['VALOR'])
    colunas = ['_r', '_grupo', 'VALOR', '_primeira', '_slot']
    if valido.empty:
        return pd.DataFrame(columns=colunas)

    chaves = ['_r', '_grupo']
    final = _valor_final(valido, chaves).reset_index()
    primeira = valido.groupby(chaves)['ORDEM'].min().rename('_primeira').reset_index()

    slots = final.merge(primeira, on=chaves)
    slots = slots.sort_values(['_r', '_primeira', '_grupo'], kind='stable')
    slots['_slot'] = slots.groupby('_r').cumcount()
    return slots[colunas]

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

    nome_por_codigo = dict(zip(df_colunas['COD DISCIPLINA'], df_colunas['NOME CURTO']))
    obrigatorias = df_colunas[df_colunas['ORDEM_TIPO'] == 1]
    optativas = df_colunas[df_colunas['ORDEM_TIPO'] == 2]
    grupo_optativa = _agrupar_optativas(origens_por_coluna, optativas['COD DISCIPLINA'].tolist())

    pares = pd.DataFrame(
        [(origem, coluna) for coluna, origens in origens_por_coluna.items() for origem in origens],
        columns=['COD ATIV CURRIC', 'COD COLUNA'],
    )
    historico_alunos = (
        df_historico[df_historico['ID PESSOA'].isin(alunos_dict)]
        .rename_axis('_rid')
        .reset_index()
    )
    reg = historico_alunos.merge(pares, on='COD ATIV CURRIC', how='inner')
    reg['VALOR'] = reg['DESCR SITUACAO'].map(status_para_num)

    reg_obr = reg.iloc[0:0]
    reg_opt = reg.iloc[0:0]
    slots = pd.DataFrame(columns=['_r', '_grupo', 'VALOR', '_primeira', '_slot'])
    n_slots = 0

    if not reg.empty:
        reg = _preparar_registros(reg)
        reg['_r'] = reg['ID PESSOA'].map(alunos_dict)

        eh_optativa = reg['COD COLUNA'].isin(grupo_optativa)
        reg_obr = reg[~eh_optativa]

        # Optativas ligadas por equivalência contam como uma só; um mesmo registro do
        # histórico nunca ocupa duas posições (preferindo o código exato cursado).
        reg_opt = reg[eh_optativa].copy()
        reg_opt['_grupo'] = reg_opt['COD COLUNA'].map(grupo_optativa)
        reg_opt['_exato'] = reg_opt['COD ATIV CURRIC'] == reg_opt['COD COLUNA']
        reg_opt = (
            reg_opt.sort_values('_exato', ascending=False, kind='stable')
            .drop_duplicates(['_rid', '_grupo'])
            .sort_values('ORDEM', ascending=False, kind='stable')
        )

        slots = _slots_optativas(reg_opt)
        n_slots = int(slots['_slot'].max()) + 1 if len(slots) else 0

    disciplinas_codigos = obrigatorias['COD DISCIPLINA'].tolist()
    disciplinas_labels = obrigatorias['NOME CURTO'].tolist()

    if disciplinas_codigos and n_slots:
        disciplinas_codigos.append(COD_SEPARADOR)
        disciplinas_labels.append(LABEL_SEPARADOR)

    deslocamento_optativas = len(disciplinas_codigos)
    disciplinas_codigos += [f'{PREFIXO_COD_OPTATIVA}{i}' for i in range(1, n_slots + 1)]
    disciplinas_labels += [f'{PREFIXO_LABEL_OPTATIVA}{i}' for i in range(1, n_slots + 1)]

    if not disciplinas_codigos:
        return renderizar(mensagem='Nenhum aluno cursou optativas para os filtros selecionados.')

    n_disciplinas = len(disciplinas_codigos)
    disciplinas_dict = {cod: j for j, cod in enumerate(disciplinas_codigos)}

    z = np.full((n_alunos, n_disciplinas), np.nan)
    textos = np.full((n_alunos, n_disciplinas), '', dtype=object)

    # --- Obrigatórias: uma coluna por disciplina ---
    if not reg_obr.empty:
        reg_obr = reg_obr.assign(_c=reg_obr['COD COLUNA'].map(disciplinas_dict).astype(int))

        valido = reg_obr.dropna(subset=['VALOR'])
        if not valido.empty:
            final = _valor_final(valido, ['_r', '_c']).reset_index()
            z[final['_r'].to_numpy(int), final['_c'].to_numpy(int)] = final['VALOR'].to_numpy()

        historicos = reg_obr.groupby(['_r', '_c'], sort=False)['LINHA_HIST'].agg('<br>'.join)
        for (r, c), historico in historicos.items():
            nome_disciplina = nome_por_codigo[disciplinas_codigos[c]]
            textos[r, c] = f"{nomes_alunos[r]}<br>{nome_disciplina}<br>{historico}"

    # --- Optativas: colunas genéricas "Optativa N", em ordem cronológica por aluno ---
    if n_slots:
        colunas_slot = deslocamento_optativas + slots['_slot'].to_numpy(int)
        z[slots['_r'].to_numpy(int), colunas_slot] = slots['VALOR'].to_numpy()

        reg_slots = reg_opt.merge(slots[['_r', '_grupo', '_slot']], on=['_r', '_grupo'], how='inner')
        agrupado = reg_slots.groupby(['_r', '_slot'], sort=False).agg(
            historico=('LINHA_HIST', '<br>'.join),
            codigo=('COD COLUNA', 'first'),
        )
        for (r, s), linha in zip(agrupado.index, agrupado.itertuples(index=False)):
            nome_optativa = nome_por_codigo[linha.codigo]
            textos[r, deslocamento_optativas + s] = (
                f"{nomes_alunos[r]}<br><b>{nome_optativa}</b><br>{linha.historico}"
            )

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