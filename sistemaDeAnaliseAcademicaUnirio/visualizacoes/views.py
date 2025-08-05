import pandas as pd
import numpy as np
import plotly.graph_objects as go
from django.shortcuts import render
from django.urls import reverse
import os
import time

def status_integralizacao(request):
    start_total = time.time()

    # Bloco 1: Leitura dos dados
    start = time.time()
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df_alunos = pd.read_csv(os.path.join(data_dir, 'alunosPorCurso.csv'))
    df_historico = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))
    print(f"Tempo leitura CSVs: {time.time() - start:.3f}s")

    # --- Filtros ---
    filtro_ativos = request.GET.get('ativos', 'todos')
    if filtro_ativos == 'ativos':
        alunos_ativos = df_alunos[df_alunos['FORMA EVASAO'] == 'Sem evasão']['ID PESSOA'].unique()
        df_historico = df_historico[df_historico['ID PESSOA'].isin(alunos_ativos)]
        df_alunos = df_alunos[df_alunos['ID PESSOA'].isin(alunos_ativos)]

    filtro_periodo = request.GET.get('periodo_ingresso', '')
    if filtro_periodo:
        df_alunos = df_alunos[df_alunos['PERIODO INGRESSO'] == filtro_periodo]
        df_historico = df_historico[df_historico['ID PESSOA'].isin(df_alunos['ID PESSOA'].unique())]

    periodos_unicos = sorted(df_alunos['PERIODO INGRESSO'].dropna().unique())
    periodos_options = [
        {'value': p, 'label': p, 'selected': p == filtro_periodo}
        for p in periodos_unicos
    ]

    # Bloco 2: Preparação de alunos_dict
    start = time.time()
    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    alunos = df_historico['MATR ALUNO'].unique().tolist()

    alunos_dict = {}
    for idx, row in enumerate(df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().itertuples(index=False)):
        alunos_dict[idx] = {
            'MATR ALUNO': row[0],
            'NOME PESSOA': row[1]
        }
    print(f"Tempo alunos_dict: {time.time() - start:.3f}s")


    # Bloco 3: Preparação de periodos_dict
    start = time.time()
    periodos_unicos = df_historico[['ANO', 'PERIODO']].drop_duplicates().reset_index(drop=True)
    periodos_unicos = periodos_unicos[periodos_unicos['ANO'].astype(str).str.isnumeric()].reset_index(drop=True)

    periodos_dict = {}
    anos = periodos_unicos['ANO'].values
    periodos = periodos_unicos['PERIODO'].values
    for idx in range(len(periodos_unicos)):
        periodos_dict[idx] = {
            'ANO': anos[idx],
            'PERIODO': periodos[idx]
        }
    print(f"Tempo periodos_dict: {time.time() - start:.3f}s")

    def formatar_periodo(ano, periodo):
        periodo = periodo.replace('. semestre', '')
        return f"{str(ano)[-2:]}/{periodo}"

    blocos = [
        ('Prazo Previsto', 8, '#6fa8dc'),
        ('Prazo Máximo', 2, '#9fc5e8'),
        ('Exigir plano de integralização', 2, '#f6b26b'),
        ('Prorrogação Máxima', 2, '#f9cb9c'),
        ('Situação Irregular', 2, '#e06666'),
        ('Mobilidade', 1, '#93c47d'),
        ('Períodos Excepcionais', 3, '#ffe599'),
        ('Atividades Calendário Emergencial', 2, '#ffd966'),
        ('Trancamentos Totais (regulares)', 2, '#b7b7b7'),
        ('Trancamentos Totais (especiais)', 2, '#cccccc'),
    ]

    status_aprovados = {
        'APV - Aprovado', 'APV- Aprovado', 'APV - Aprovado sem nota',
        'ADI - Aproveitamento', 'ADI - Aproveitamento de créditos da disciplina',
        'ADI - Dispensa com nota', 'DIS - Dispensa sem nota'
    }
    status_reprovados = {
        'REP - Reprovado por nota/conceito', 'REF - Reprovado por falta',
        'ASC - Reprovado sem nota', 'TRA - Trancamento de disciplina'
    }
    status_matriculado = {'ASC - Matrícula'}

    # Bloco 4: Construção da matriz_geral

    matriculas_validas = set(alunos_dict[idx]['MATR ALUNO'] for idx in alunos_dict)
    periodos_validos = set((periodos_dict[idx]['ANO'], periodos_dict[idx]['PERIODO']) for idx in periodos_dict)

    matriz_geral = {}

    total_iteracoes_estrutura = 0
    total_adicoes_matr = 0
    total_adicoes_periodo = 0

    start = time.time()
    for mt, an, pr in zip(df_historico['MATR ALUNO'], df_historico['ANO'], df_historico['PERIODO']):
        total_iteracoes_estrutura += 1
        matr = mt
        periodo = (an, pr)
        if matr not in matriculas_validas or periodo not in periodos_validos:
            continue
        if matr not in matriz_geral:
            matriz_geral[matr] = {}
            total_adicoes_matr += 1
        if periodo not in matriz_geral[matr]:
            matriz_geral[matr][periodo] = {}
            total_adicoes_periodo += 1
    print(f"Tempo matriz_geral (estrutura): {time.time() - start:.3f}s")
    print(f"Iterações totais (estrutura): {total_iteracoes_estrutura}")
    print(f"Novas matrículas adicionadas: {total_adicoes_matr}")
    print(f"Novos períodos adicionados: {total_adicoes_periodo}")

    # Bloco 5: Preenchimento da matriz_geral
    start = time.time()
    total_iteracoes_preenchimento = 0
    total_celulas_criadas = 0

    matr_aluno = df_historico['MATR ALUNO'].values
    anos = df_historico['ANO'].values
    periodos = df_historico['PERIODO'].values
    nomes_pessoa = df_historico['NOME PESSOA'].values
    descr_situacao = df_historico['DESCR SITUACAO'].values
    nome_ativ_curric = df_historico['NOME ATIV CURRIC'].values
    cod_ativ_curric = df_historico['COD ATIV CURRIC'].values
    nota_ativ_curric = df_historico['MEDIA FINAL'].values

    for i in range(len(df_historico)):
        total_iteracoes_preenchimento += 1
        matr = matr_aluno[i]
        periodo = (anos[i], periodos[i])
        if matr not in matriculas_validas or periodo not in periodos_validos:
            continue
        nome = nomes_pessoa[i]
        status = descr_situacao[i]

        celula = matriz_geral[matr][periodo]
        if not celula:
            matriz_geral[matr][periodo] = {
                'nome': nome,
                'aprovacoes': [],
                'reprovacoes': [],
                'outros': []
            }
            celula = matriz_geral[matr][periodo]
            total_celulas_criadas += 1
        if status in status_aprovados:
            celula['aprovacoes'].append({
                'nome': nome_ativ_curric[i],
                'status': descr_situacao[i],
                'codigo': cod_ativ_curric[i],
                'nota': nota_ativ_curric[i] if pd.notna(nota_ativ_curric[i]) else 'N/A'
            })
        elif status in status_reprovados:
            celula['reprovacoes'].append({
                'nome': nome_ativ_curric[i],
                'status': descr_situacao[i],
                'codigo': cod_ativ_curric[i],
                'nota': nota_ativ_curric[i] if pd.notna(nota_ativ_curric[i]) else 'N/A'
            })
        else:
            celula['outros'].append({
                'nome': nome_ativ_curric[i],
                'status': descr_situacao[i],
                'codigo': cod_ativ_curric[i],
                'nota': nota_ativ_curric[i] if pd.notna(nota_ativ_curric[i]) else 'N/A'
            })
    print(f"Tempo matriz_geral (preenchimento): {time.time() - start:.3f}s")
    print(f"Iterações totais (preenchimento): {total_iteracoes_preenchimento}")
    print(f"Novas células criadas: {total_celulas_criadas}")

    # Bloco 6: Construção da matriz_integralizacao
    start = time.time()
    n_periodos = sum([bloco[1] for bloco in blocos])
    matriculas = list(matriz_geral.keys())
    matriz_integralizacao = []
    tooltips_integralizacao = []

    for matr in matriculas:
        periodos_ordenados = sorted(
            matriz_geral[matr].keys(),
            key=lambda x: (int(x[0]), 1 if '1' in x[1] else 2)
        )
        linha = []
        linha_tooltip = []
        for idx, periodo in enumerate(periodos_ordenados):
            if len(linha) >= n_periodos:
                break
            label = formatar_periodo(*periodo)
            celula = matriz_geral[matr][periodo]
            todas_disciplinas = (
                celula.get('aprovacoes', []) +
                celula.get('reprovacoes', []) +
                celula.get('outros', [])
            )
            if todas_disciplinas:
                disciplinas_tooltip = [
                    f"{disc['nome']}<br>    Nota: {disc['nota']}<br>    Situação: {disc['status']}"
                    for disc in todas_disciplinas
                ]
                tooltip = "<br>".join(disciplinas_tooltip)
            else:
                tooltip = "Nenhuma disciplina cursada"
            linha.append(label)
            linha_tooltip.append(tooltip)
        if len(periodos_ordenados) > n_periodos:
            linha[-1] = '+'
            linha_tooltip[-1] = 'Períodos excedentes'
        while len(linha) < n_periodos:
            linha.append('')
            linha_tooltip.append('')
        matriz_integralizacao.append(linha)
        tooltips_integralizacao.append(linha_tooltip)
    print(f"Tempo matriz_integralizacao: {time.time() - start:.3f}s")

    # Bloco 7: Construção do gráfico
    start = time.time()
    colunas = []
    cores = []
    for nome, tam, cor in blocos:
        colunas += [""] * (tam - 1) + [nome]
        cores += [cor] * tam

    nomes = [
        next((alunos_dict[idx]['NOME PESSOA'] for idx in alunos_dict if alunos_dict[idx]['MATR ALUNO'] == matr), '')
        for matr in matriculas
    ]

    fig = go.Figure(data=go.Heatmap(
        z=[[i for i in range(n_periodos)] for _ in range(len(matriculas))],
        x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
        y=[f"{matriculas[i]} - {nomes[i]}" for i in range(len(matriculas))],
        text=matriz_integralizacao,
        hovertext=tooltips_integralizacao,
        hoverinfo='text',
        texttemplate='%{text}',
        colorscale=[[i/(n_periodos-1), cor] for i, cor in enumerate(cores)],
        showscale=False
    ))

    for i, cor in enumerate(cores):
        fig.add_shape(
            type="rect",
            x0=i-0.5, x1=i+0.5,
            y0=-0.5, y1=len(matriculas)-0.5,
            fillcolor=cor, line=dict(width=0),
            layer="below"
        )

    fig.update_traces(
        showscale=False,
        textfont=dict(size=13, color='black'),
    )

    fig.update_layout(
        title='Status de Integralização dos Alunos por Período',
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(n_periodos)),
            ticktext=[f'{colunas[i]}' for i in range(n_periodos)],
            tickangle=20,
            side='top',
            range=[
                (n_periodos / 2) - 5,  
                (n_periodos / 2) + 5   
            ],
        ),
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=10),
            scaleanchor="x",
            scaleratio=1.1,
            range=[-0.5, min(9.5, len(matriculas)-0.5)],
            dtick=0.5,
        ),
        autosize=False,
        width=1800,
        height=650,
        margin=dict(l=10, r=10, t=60, b=10),
    )

    print(f"Tempo gráfico: {time.time() - start:.3f}s")

    print(f"Tempo total: {time.time() - start_total:.3f}s")

    plot_div = fig.to_html(full_html=False)
    filtros_options = [
        {'name': 'ativos', 'label': 'Exibir apenas alunos ativos (sem evasão)', 'selected': filtro_ativos == 'ativos'},
    ]
    return render(request, 'status_integralizacao.html', {
        'plot_div': plot_div,
        'filtros_options': filtros_options,
        'periodos_options': periodos_options,
    })

def desempenho_aluno_periodo(request):
    import pandas as pd
    import plotly.graph_objects as go
    import os

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df_historico = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))
    df_alunos = pd.read_csv(os.path.join(data_dir, 'alunosPorCurso.csv'))

    df_historico['PERIODO_NUM'] = df_historico['PERIODO'].str.extract(r'(\d)')[0].astype(float)
    df_historico = df_historico.sort_values(['MATR ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_NUM'])
    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    df_historico['ANO_PERIODO'] = df_historico['ANO'].astype(str) + ' - ' + df_historico['PERIODO']

    matr_aluno_param = request.GET.get('matr_aluno')
    if matr_aluno_param:
        try:
            matr_aluno = int(matr_aluno_param)
            if matr_aluno not in df_historico['MATR ALUNO'].values:
                matr_aluno = df_historico['MATR ALUNO'].iloc[0]
        except (ValueError, TypeError):
            matr_aluno = df_historico['MATR ALUNO'].iloc[0]
    else:
        matr_aluno = df_historico['MATR ALUNO'].iloc[0]

    dados_aluno = df_historico[df_historico['MATR ALUNO'] == matr_aluno].copy()
    dados_aluno['STATUS'] = dados_aluno['DESCR SITUACAO'].str.strip()
    dados_aluno['CARGA'] = dados_aluno['TOTAL CARGA HORARIA']
    dados_aluno['DISCIPLINA'] = (
        dados_aluno['COD ATIV CURRIC'].astype(str) + ' - ' +
        dados_aluno['NOME ATIV CURRIC'] + ' (' +
        dados_aluno['CARGA'].astype(str) + 'h)'
    )

    def ordenar_periodo(periodo):
        ano, per = periodo.split(' - ')
        return int(ano) * 10 + (1 if '1' in per else 2)

    periodos = sorted(dados_aluno['ANO_PERIODO'].unique(), key=ordenar_periodo)
    status_aprovados = {
        'APV - Aprovado', 'APV- Aprovado', 'APV - Aprovado sem nota',
        'ADI - Aproveitamento', 'ADI - Aproveitamento de créditos da disciplina',
        'ADI - Dispensa com nota', 'DIS - Dispensa sem nota'
    }
    status_reprovados = {
        'REP - Reprovado por nota/conceito', 'REF - Reprovado por falta',
        'ASC - Reprovado sem nota', 'TRA - Trancamento de disciplina'
    }
    cores_aprovados = ['#006400', '#228B22', '#32CD32', '#7CFC00', '#ADFF2F']
    cores_reprovados = ['#8B0000', '#CD5C5C', '#FFA07A']
    cores_status = {}
    for idx, status in enumerate(status_aprovados):
        cores_status[status] = cores_aprovados[idx % len(cores_aprovados)]
    for idx, status in enumerate(status_reprovados):
        cores_status[status] = cores_reprovados[idx % len(cores_reprovados)]

    carga_aprovada_acumulada = (
        dados_aluno[dados_aluno['STATUS'].isin(status_aprovados)]
        .groupby('ANO_PERIODO')['CARGA']
        .sum()
        .reindex(periodos, fill_value=0)
        .cumsum()
        .shift(fill_value=0)
    )

    barras = []
    for status in status_reprovados:
        cor = cores_status[status]
        dados_status = dados_aluno[dados_aluno['STATUS'] == status]
        if dados_status.empty:
            continue
        y = dados_status.groupby('ANO_PERIODO')['CARGA'].sum().reindex(periodos, fill_value=0)
        hover = dados_status.groupby('ANO_PERIODO').apply(
            lambda grupo: "<br>".join(
                f"{linha['DISCIPLINA']}<br>Status: {linha['STATUS']}" for _, linha in grupo.iterrows()
            )
        ).reindex(periodos, fill_value="Nenhuma disciplina").tolist()
        barra = go.Bar(
            x=periodos,
            y=y,
            base=carga_aprovada_acumulada.tolist(),
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)

    for status in status_aprovados:
        cor = cores_status[status]
        dados_status = dados_aluno[dados_aluno['STATUS'] == status]
        if dados_status.empty:
            continue
        y = dados_status.groupby('ANO_PERIODO')['CARGA'].sum().reindex(periodos, fill_value=0)
        hover = dados_status.groupby('ANO_PERIODO').apply(
            lambda grupo: "<br>".join(
                f"{linha['DISCIPLINA']}<br>Status: {linha['STATUS']}" for _, linha in grupo.iterrows()
            )
        ).reindex(periodos, fill_value="Nenhuma disciplina").tolist()
        barra = go.Bar(
            x=periodos,
            y=y,
            base=carga_aprovada_acumulada.tolist(),
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)

    carga_referencia = 3240
    linha_referencia = go.Scatter(
        x=periodos,
        y=[carga_referencia] * len(periodos),
        mode='lines',
        name='Ritmo de Integralização de Referência',
        line=dict(color='rgba(100,100,100,0.3)')
    )
    barras.append(linha_referencia)

    fig = go.Figure(barras)
    fig.update_layout(
        barmode='stack',
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária',
        title='Desempenho por Período com Acúmulo de Aprovados',
        height=800
    )

    alunos_options = [
        {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
        for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
    ]

    plot_div = fig.to_html(full_html=False)
    return render(request, 'desempenho_aluno_periodo.html', {
        'plot_div': plot_div,
        'alunos_options': alunos_options,
        'selected_id': str(matr_aluno), 
    })

def heatmap_desempenho(request):
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import os

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))
    df_alunos = pd.read_csv(os.path.join(data_dir, 'alunosPorCurso.csv'))

    # --- Filtros ---
    filtro_ativos = request.GET.get('ativos', 'todos')
    if filtro_ativos == 'ativos':
        alunos_ativos = df_alunos[df_alunos['FORMA EVASAO'] == 'Sem evasão']['ID PESSOA'].unique()
        df = df[df['ID PESSOA'].isin(alunos_ativos)]
        df_alunos = df_alunos[df_alunos['ID PESSOA'].isin(alunos_ativos)]

    filtro_periodo = request.GET.get('periodo_ingresso', '')
    if filtro_periodo:
        df_alunos = df_alunos[df_alunos['PERIODO INGRESSO'] == filtro_periodo]
        df = df[df['ID PESSOA'].isin(df_alunos['ID PESSOA'].unique())]

    curriculos_disponiveis = sorted(df['NUM VERSAO'].unique())
    periodos_unicos = sorted(df_alunos['PERIODO INGRESSO'].dropna().unique())
    periodos_options = [
        {'value': p, 'label': p, 'selected': p == filtro_periodo}
        for p in periodos_unicos
    ]

    curriculos_selecionados = request.GET.getlist('curriculos')
    if not curriculos_selecionados:
        curriculos_selecionados = [curriculos_disponiveis[-1]]  # Último currículo por padrão

    df_filtrado = df[df['NUM VERSAO'].isin(curriculos_selecionados)]

    if df_filtrado.empty:
        fig = go.Figure()
        fig.update_layout(
            title='Nenhum dado encontrado para os currículos selecionados',
            xaxis_title='Disciplinas',
            yaxis_title='Matrículas',
            height=400
        )
        plot_div = fig.to_html(full_html=False)

        curriculos_options = [
            {'value': curriculo, 'label': curriculo, 'selected': curriculo in curriculos_selecionados}
            for curriculo in curriculos_disponiveis
        ]

        return render(request, 'heatmap_desempenho.html', {
            'plot_div': plot_div,
            'curriculos_options': curriculos_options,
            'periodos_options': periodos_options,
            'filtros_options': [
                {'name': 'ativos', 'label': 'Exibir apenas alunos ativos (sem evasão)', 'selected': filtro_ativos == 'ativos'},
            ],
        })

    matricula_id_col = 'MATR ALUNO'
    disciplinas_dict = dict(zip(df_filtrado['COD ATIV CURRIC'], df_filtrado['NOME ATIV CURRIC']))
    matriculas = df_filtrado[matricula_id_col].unique().tolist()
    disciplinas = df_filtrado['COD ATIV CURRIC'].unique().tolist()
    mapa_matriculas = {mat: i for i, mat in enumerate(matriculas)}
    mapa_disciplinas = {disc: i for i, disc in enumerate(disciplinas)}

    matriz = [[[] for _ in range(len(disciplinas))] for _ in range(len(matriculas))]
    for (matricula, cod_disc), grupo in df_filtrado.groupby([matricula_id_col, 'COD ATIV CURRIC']):
        i = mapa_matriculas[matricula]
        j = mapa_disciplinas[cod_disc]
        matriz[i][j] = grupo['DESCR SITUACAO'].astype(str).tolist()

    df_matriz = pd.DataFrame(
        [[', '.join(attempts) if attempts else '' for attempts in linha] for linha in matriz],
        index=matriculas,
        columns=[disciplinas_dict[cod] for cod in disciplinas]
    )

    if 'NOME PESSOA' in df_filtrado.columns:
        aluno_info = df_filtrado.drop_duplicates(matricula_id_col).set_index(matricula_id_col)[['NOME PESSOA', 'NUM VERSAO']]
        df_matriz.index = [
            f"{mid} - {aluno_info.loc[mid, 'NOME PESSOA']} (Currículo: {aluno_info.loc[mid, 'NUM VERSAO']})"
            for mid in df_matriz.index
        ]

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

    def classificar_status(cell):
        if pd.isna(cell) or not cell.strip():
            return np.nan
        status_list = [s.strip() for s in cell.split(',') if s.strip()]
        if any(s in aprovados for s in status_list):
            return 1
        if any(s in matriculado for s in status_list):
            return 0
        if any(s in reprovados for s in status_list):
            return -1
        else:
            return 0

    df_numerico = df_matriz.map(classificar_status)

    def construir_tooltip(nome_aluno, disciplina, status_str):
        if pd.isna(status_str) or not status_str.strip():
            return (
                f"{disciplina}<br>"
                f"<b>Histórico:</b><br>"
                f"    Nenhum<br>"
                f"<b>Situação final:</b><br>"
                f"    Indefinido"
            )
        status_list = [s.strip() for s in status_str.split(',') if s.strip()]
        status_formatado = ""
        # Buscar períodos para cada status usando df_filtrado
        status_periodos = []
        for s in status_list:
            # Resgata o período da disciplina para o aluno
            filtro = (
                (df_filtrado['NOME PESSOA'] == nome_aluno.split(' - ')[-2].strip() if ' - ' in nome_aluno else nome_aluno) &
                (df_filtrado['NOME ATIV CURRIC'] == disciplina)
            )
            # Se não encontrar, tenta por matrícula
            if not df_filtrado[filtro].empty:
                ano = df_filtrado[filtro]['ANO'].iloc[0]
                periodo = df_filtrado[filtro]['PERIODO'].iloc[0]
                periodo_str = f"{ano} - {periodo}"
            else:
                periodo_str = ""
            status_periodos.append((s, periodo_str))

        for s, periodo_str in status_periodos:
            if periodo_str:
                status_formatado += f"    {s} ({periodo_str})<br>"
            else:
                status_formatado += f"    {s}<br>"
        status_final = status_list[-1] if status_list else 'Indefinido'
        return (
            f"{disciplina}<br>"
            f"<b>Histórico:</b><br>{status_formatado}"
            f"<b>Situação final:</b><br>    {status_final}"
        )

    hover_text = df_matriz.apply(
        lambda row: [
            "" if pd.isna(row.iloc[j]) or not str(row.iloc[j]).strip()
            else construir_tooltip(row.name, df_matriz.columns[j], row.iloc[j])
            for j in range(len(row))
        ],
        axis=1
    ).tolist()

    fig = go.Figure(data=go.Heatmap(
        z=df_numerico.values,
        x=df_numerico.columns,
        y=df_numerico.index,
        text=hover_text,
        hoverinfo='text',
        colorscale=[
            [0.0, 'red'],
            [0.5, 'yellow'],
            [1.0, 'green']
        ],
        colorbar=dict(
            title='Status',
            tickvals=[-1, 0, 1],
            ticktext=['Reprovado/Trancado', 'Matriculado', 'Aprovado']
        ),
        showscale=False
    ))

    if len(curriculos_selecionados) == 1:
        titulo_curriculos = f"Currículo: {curriculos_selecionados[0]}"
    else:
        titulo_curriculos = f"Currículos: {', '.join(curriculos_selecionados)}"

    fig.update_layout(
        title=f'Desempenho Acadêmico por Matrícula e Disciplina<br><sub>{titulo_curriculos}</sub>',
        xaxis=dict(title='Disciplinas', tickangle=45, tickfont=dict(size=9)),
        yaxis=dict(title='Matrículas', tickfont=dict(size=9)),
        autosize=True,
        margin=dict(l=50, r=50, t=100, b=100),
        height=max(600, len(matriculas) * 20 + 200),
    )

    plot_div = fig.to_html(full_html=False)

    curriculos_options = [
        {'value': curriculo, 'label': curriculo, 'selected': curriculo in curriculos_selecionados}
        for curriculo in curriculos_disponiveis
    ]

    filtros_options = [
        {'name': 'ativos', 'label': 'Exibir apenas alunos ativos (sem evasão)', 'selected': filtro_ativos == 'ativos'},
    ]

    return render(request, 'heatmap_desempenho.html', {
        'plot_div': plot_div,
        'curriculos_options': curriculos_options,
        'periodos_options': periodos_options,
        'filtros_options': filtros_options,
    })

def home(request):
    return render(request, 'home.html')

def visualizacoes_hub(request):
    visualizacoes = [
        {
            'url': 'desempenho_aluno_periodo',
            'icon': 'fas fa-chart-line',
            'titulo': 'Desempenho Acadêmico',
            'descricao': 'Acompanhe o desempenho individual dos alunos ao longo dos períodos.'
        },
        {
            'url': 'heatmap_desempenho',
            'icon': 'fas fa-fire',
            'titulo': 'Heatmap de Desempenho',
            'descricao': 'Visualize padrões de aprovação e reprovação por disciplina e turma.'
        },
        {
            'url': 'status_integralizacao',
            'icon': 'fas fa-tasks',
            'titulo': 'Status de Integralização',
            'descricao': 'Monitore o progresso dos alunos em relação à conclusão do curso.'
        }
    ]
    return render(request, 'visualizacoes_hub.html', {'visualizacoes': visualizacoes})