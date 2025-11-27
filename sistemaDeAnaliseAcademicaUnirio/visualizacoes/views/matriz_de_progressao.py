from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go

def matriz_de_progressao(request):
    if not request.GET:
        return redirect(f"{reverse('matriz_de_progressao')}?curriculos=20232&tipo_disciplina=obrigatoria")

    USER_ID = 'user1'
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')

    df_alunos = pd.read_csv(alunos_path)
    df_historico = pd.read_csv(historico_path)

    df_disciplinas_20232 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20232.csv'))
    df_disciplinas_20052 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20052.csv'))
    df_disciplinas_20002 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20002.csv'))
    df_disciplinas_20081 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20081.csv'))

    # --- Filtros ---
    filtro_ativos = request.GET.get('ativos', 'todos')
    filtro_curriculos = request.GET.getlist('curriculos')
    filtro_tipo_disciplina = request.GET.get('tipo_disciplina', 'obrigatoria')
    curriculos_map = {
        '20232': df_disciplinas_20232,
        '20052': df_disciplinas_20052,
        '20002': df_disciplinas_20002,
        '20081': df_disciplinas_20081,
    }
    curriculos_options = [
        {'value': '20232', 'label': 'Currículo 2023/2', 'selected': '20232' in filtro_curriculos},
        {'value': '20052', 'label': 'Currículo 2005/2', 'selected': '20052' in filtro_curriculos},
        {'value': '20002', 'label': 'Currículo 2000/2', 'selected': '20002' in filtro_curriculos},
        {'value': '20081', 'label': 'Currículo 2008/1', 'selected': '20081' in filtro_curriculos},
    ]
    tipo_disciplina_options = [
        {'value': 'todas', 'label': 'Todas', 'selected': filtro_tipo_disciplina == 'todas'},
        {'value': 'obrigatoria', 'label': 'Obrigatórias', 'selected': filtro_tipo_disciplina == 'obrigatoria'},
        {'value': 'optativa', 'label': 'Optativas', 'selected': filtro_tipo_disciplina == 'optativa'},
    ]

    # Filtrar alunos ativos
    if filtro_ativos == 'ativos':
        alunos_ativos = df_alunos[df_alunos['FORMA EVASAO'] == 'Sem evasão']['ID PESSOA'].unique()
        df_historico = df_historico[df_historico['ID PESSOA'].isin(alunos_ativos)]
        df_alunos = df_alunos[df_alunos['ID PESSOA'].isin(alunos_ativos)]

    # Filtrar currículos e tipo de disciplina
    def filtrar_disciplinas(df, curriculo, tipo):
        if tipo == 'todas':
            if curriculo == '20002':
                return df['COD DISCIPLINA']
            else:
                return df['COD DISCIPLINA']
        elif tipo == 'obrigatoria':
            if curriculo == '20002':
                return df[df['DESCR ESTRUTURA'] == 'Disciplinas obrigatórias']['COD DISCIPLINA']
            else:
                return df[df['TIPO DISCIPLINA'] == 'Obrigatória']['COD DISCIPLINA']
        elif tipo == 'optativa':
            if curriculo == '20002':
                return df[df['DESCR ESTRUTURA'] == 'Disciplinas optativas']['COD DISCIPLINA']
            else:
                return df[df['TIPO DISCIPLINA'] == 'Optativa']['COD DISCIPLINA']
        else:
            return df['COD DISCIPLINA']

    def ordenar_disciplinas_por_periodo(df, codigos):
        if 'PERIODO IDEAL' in df.columns:
            df_filtrado = df[df['COD DISCIPLINA'].isin(codigos)].copy()
            df_filtrado['PERIODO IDEAL'] = pd.to_numeric(df_filtrado['PERIODO IDEAL'], errors='coerce').fillna(9999)
            df_filtrado = df_filtrado.sort_values(['PERIODO IDEAL', 'COD DISCIPLINA'])
            return df_filtrado['COD DISCIPLINA'].tolist()
        else:
            return sorted(list(codigos))

    if filtro_curriculos:
        disciplinas_set = set()
        disciplinas_periodo = []
        for curr in filtro_curriculos:
            df = curriculos_map.get(curr)
            if df is not None:
                disciplinas = filtrar_disciplinas(df, curr, filtro_tipo_disciplina)
                disciplinas_set.update(disciplinas)
        df_ord = curriculos_map.get(filtro_curriculos[0], df_disciplinas_20232)
        disciplinas_list = ordenar_disciplinas_por_periodo(df_ord, disciplinas_set)
    else:
        disciplinas_set = set()
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20232, '20232', filtro_tipo_disciplina))
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20052, '20052', filtro_tipo_disciplina))
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20002, '20002', filtro_tipo_disciplina))
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20081, '20081', filtro_tipo_disciplina))
        disciplinas_list = ordenar_disciplinas_por_periodo(df_disciplinas_20232, disciplinas_set)

    df_alunos['MATR ALUNO'] = df_alunos['MATR ALUNO'].astype(str)
    df_alunos = df_alunos.drop_duplicates(subset=['MATR ALUNO'])
    df_alunos = df_alunos.sort_values('MATR ALUNO').reset_index(drop=True)
    df_historico['MATR ALUNO'] = df_historico['MATR ALUNO'].astype(str)

    alunos_dict = dict((matricula, idx) for idx, matricula in enumerate(df_alunos['MATR ALUNO']))
    disciplinas_dict = dict((cod_disciplina, idx) for idx, cod_disciplina in enumerate(disciplinas_list))

    n_alunos = len(alunos_dict)
    n_disciplinas = len(disciplinas_dict)
    matriz_geral = [['' for _ in range(n_disciplinas)] for _ in range(n_alunos)]
    matriz_tooltips = [[{} for _ in range(n_disciplinas)] for _ in range(n_alunos)]

    for matricula, cod_disciplina, status in zip(df_historico['MATR ALUNO'], df_historico['COD ATIV CURRIC'], df_historico['DESCR SITUACAO']):
        idx_aluno = alunos_dict.get(str(matricula))
        idx_disc = disciplinas_dict.get(cod_disciplina)
        if idx_aluno is not None and idx_disc is not None:
            matriz_geral[idx_aluno][idx_disc] = status

    for matricula, nome_aluno, cod_disciplina, status, media_final, ano, periodo, nome, nome_disciplina in zip(
        df_historico['MATR ALUNO'],
        df_historico['NOME PESSOA'],
        df_historico['COD ATIV CURRIC'],
        df_historico['DESCR SITUACAO'],
        df_historico['MEDIA FINAL'],
        df_historico['ANO'],
        df_historico['PERIODO'],
        df_historico['NOME PESSOA'],
        df_historico['NOME ATIV CURRIC']
    ):
        idx_aluno = alunos_dict.get(str(matricula))
        idx_disc = disciplinas_dict.get(cod_disciplina)
        if (
            idx_aluno is not None and idx_disc is not None
            and 0 <= idx_aluno < n_alunos
            and 0 <= idx_disc < n_disciplinas
        ):
            matriz_geral[idx_aluno][idx_disc] = status
            if 'status_list' not in matriz_tooltips[idx_aluno][idx_disc]:
                matriz_tooltips[idx_aluno][idx_disc]['status_list'] = []
            matriz_tooltips[idx_aluno][idx_disc]['status_list'].append({
                'nome_disciplina': nome_disciplina,
                'status': status,
                'media_final': media_final,
                'ano_periodo': f"{ano}.{periodo}",
                'nome_aluno': nome_aluno
            })

    alunos_labels = [
        f"{matricula} - {df_alunos.loc[df_alunos['MATR ALUNO'] == matricula, 'NOME PESSOA'].values[0]}"
        if not df_alunos.loc[df_alunos['MATR ALUNO'] == matricula, 'NOME PESSOA'].empty else str(matricula)
        for matricula in df_alunos['MATR ALUNO']
    ]
    def get_nome_disciplina(cod):
        for df in [df_disciplinas_20232, df_disciplinas_20052, df_disciplinas_20002, df_disciplinas_20081]:
            nome = df.loc[df['COD DISCIPLINA'] == cod, 'NOME DISCIPLINA']
            if not nome.empty:
                nome_val = nome.values[0]
                if ' - ' in nome_val:
                    return nome_val.split(' - ', 1)[1].strip()
                return nome_val.strip()
        return str(cod)

    disciplinas_labels = [get_nome_disciplina(cod) for cod in disciplinas_list]

    aprovados = {
        'APV - Aprovado', 'APV- Aprovado', 'APV - Aprovado sem nota',
        'ADI - Aproveitamento', 'ADI - Dispensa com nota',
        'DIS - Dispensa sem nota', 'ADI - Aproveitamento de créditos da disciplina',
    }
    reprovados = {
        'REP - Reprovado por nota/conceito',
        'REF - Reprovado por falta',
        'ASC - Reprovado sem nota',
        'TRA - Trancamento de disciplina'
    }
    matriculado = {'ASC - Matrícula'}

    def status_to_num(status):
        if status in aprovados:
            return 1
        if status in matriculado:
            return 0
        if status in reprovados:
            return -1
        return np.nan

    matriz_numerica = [
        [status_to_num(cell) for cell in row]
        for row in matriz_geral
    ]

    def tooltip_format(cell_tooltip):
        if not cell_tooltip or 'status_list' not in cell_tooltip:
            return ""
        status_list = cell_tooltip['status_list']
        if len(status_list) == 1:
            s = status_list[0]
            nome_aluno = s.get('nome_aluno', '')
            nome_disciplina = s.get('nome_disciplina', '')
            status = s.get('status', '')
            media = s.get('media_final', '')
            periodo = s.get('ano_periodo', '')
            nota_str = f"{media}" if pd.notna(media) else ""
            return (
                f"{nome_aluno}<br>"
                f"{nome_disciplina}<br>"
                f"  Status: {status}<br>"
                f"      {periodo}<br>"
                f"      {nota_str}<br>"
            )
        else:
            s0 = status_list[0]
            nome_aluno = s0.get('nome_aluno', '')
            nome_disciplina = s0.get('nome_disciplina', '')
            historico = []
            for s in sorted(status_list, key=lambda x: x.get('ano_periodo', ''), reverse=True):
                status = s.get('status', '')
                media = s.get('media_final', '')
                periodo = s.get('ano_periodo', '')
                nota_str = f"{media}" if pd.notna(media) else ""
                historico.append(f"{status} ({periodo}) {nota_str}")
            return (
                f"{nome_aluno}<br>"
                f"{nome_disciplina}<br>"
                f"Histórico: <br>" + "<br>".join(historico)
            )

    matriz_tooltips_str = [
        [tooltip_format(cell) for cell in row]
        for row in matriz_tooltips
    ]

    alunos_length = len(alunos_labels)

    fig = go.Figure(data=go.Heatmap(
        z=matriz_numerica,
        x=disciplinas_labels,
        y=alunos_labels,
        text=matriz_tooltips_str,
        hoverinfo='text',
        colorscale=[
            [0.0, 'red'],
            [0.5, 'yellow'],
            [1.0, 'green']
        ],
        showscale=False
    ))

    fig.update_layout(
        font=dict(size=18),
        xaxis=dict(
            tickangle=330,
            tickfont=dict(size=16),
            fixedrange=True  
        ),
        yaxis=dict(
            tickfont=dict(size=16),
            range=[alunos_length - 30, alunos_length - 1],
        ),
        autosize=True,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        height=920,
        width=2200,
        dragmode="pan"  
    )

    plot_div = fig.to_html(full_html=False)
    filtros_options = [
        {'name': 'ativos', 'label': 'Alunos ativos', 'selected': filtro_ativos == 'ativos'},
    ]
    return render(request, 'matriz_de_progressao.html', {
        'plot_div': plot_div,
        'curriculos_options': curriculos_options,
        'periodos_options': [],
        'filtros_options': filtros_options,
        'curriculos_selecionados': filtro_curriculos,
        'tipo_disciplina_options': tipo_disciplina_options,
        'tipo_disciplina_selecionado': filtro_tipo_disciplina,
    })