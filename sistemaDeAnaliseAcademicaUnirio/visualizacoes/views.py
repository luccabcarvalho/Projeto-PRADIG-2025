import pandas as pd
import numpy as np
import plotly.graph_objects as go
from django.shortcuts import render
import os

def status_integralizacao(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df_alunos = pd.read_csv(os.path.join(data_dir, 'alunosPorCurso.csv'))
    df_hist = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))

    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    alunos = df_hist['MATR ALUNO'].unique().tolist()

    blocos = [
        ('Prazo Previsto', 8, '#6fa8dc'),
        ('Prazo Máximo', 2, '#9fc5e8'),
        ('Exigir plano de integralização', 2, '#f6b26b'),
        ('Prorrogação Máxima', 2, '#f9cb9c'),
        ('Situação Irregular', 2, '#e06666'),
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

    colunas = []
    cores = []
    for nome, tam, cor in blocos:
        colunas += [nome] + [""] * (tam - 1)
        cores += [cor] * tam
    n_periodos = len(colunas)

    df_hist['PERIODO_LABEL'] = (
        df_hist['ANO'].astype(str).str[-2:] + '/' +
        df_hist['PERIODO'].astype(str).str.replace('. semestre', '', regex=False).str.strip()
    )

    mapa_matricula_nome = dict(zip(df_hist['MATR ALUNO'], df_hist['NOME PESSOA']))

    aluno_periodos = {}
    for matricula, grupo in df_hist.groupby('MATR ALUNO'):
        periodos = grupo['PERIODO_LABEL'].drop_duplicates().tolist()
        aluno_periodos[matricula] = periodos

    def tooltip_periodo(matricula, periodo):
        aluno_nome = mapa_matricula_nome.get(matricula, str(matricula))
        dados = df_hist[(df_hist['MATR ALUNO'] == matricula) & (df_hist['PERIODO_LABEL'] == periodo)]
        if dados.empty:
            return periodo

        aprovadas = []
        reprovadas = []
        matriculadas = []
        outros = []
        for _, row in dados.iterrows():
            status = str(row['DESCR SITUACAO']).strip()
            disciplina = f"{row['COD ATIV CURRIC']} - {row['NOME ATIV CURRIC']} ({row['TOTAL CARGA HORARIA']}h)"
            if status in status_aprovados:
                aprovadas.append(disciplina)
            elif status in status_reprovados:
                reprovadas.append(disciplina)
            elif status in status_matriculado:
                matriculadas.append(disciplina)
            else:
                outros.append(f"{disciplina} [{status}]")

        tooltip = f"<b>Aluno:</b> {aluno_nome}<br><b>Período:</b> {periodo}<br>"
        if aprovadas:
            tooltip += "<b>Aprovadas:</b><br>" + "<br>".join(aprovadas) + "<br>"
        if reprovadas:
            tooltip += "<b>Reprovadas:</b><br>" + "<br>".join(reprovadas) + "<br>"
        if matriculadas:
            tooltip += "<b>Matriculadas:</b><br>" + "<br>".join(matriculadas) + "<br>"
        if outros:
            tooltip += "<b>Outros:</b><br>" + "<br>".join(outros) + "<br>"
        return tooltip

    matriz = []
    tooltip_matriz = []
    for matricula in alunos:
        periodos = aluno_periodos.get(matricula, [])
        linha = [''] * n_periodos
        tooltips = [''] * n_periodos
        limite = min(len(periodos), n_periodos)
        for i in range(limite):
            linha[i] = periodos[i]
            tooltips[i] = tooltip_periodo(matricula, periodos[i])
        if len(periodos) > n_periodos:
            linha[-1] = '+'
            excedentes = periodos[n_periodos - 1:]
            tooltips[-1] = 'Períodos excedentes: ' + ', '.join(excedentes)
        matriz.append(linha)
        tooltip_matriz.append(tooltips)

    fig = go.Figure(data=go.Heatmap(
        z=[[i for i in range(n_periodos)] for _ in range(len(alunos))],
        x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
        y=[f"{matricula} - {mapa_matricula_nome.get(matricula, '')}" for matricula in alunos],
        text=matriz,
        customdata=tooltip_matriz,
        hovertemplate='%{customdata}',
        texttemplate='%{text}',
        colorscale=[[i/(n_periodos-1), cor] for i, cor in enumerate(cores)],
        showscale=False
    ))

    for i, cor in enumerate(cores):
        fig.add_shape(
            type="rect",
            x0=i-0.5, x1=i+0.5,
            y0=-0.5, y1=len(alunos)-0.5,
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
            tickangle=45,
            side='top',
            range=[-0.5, 25.5]
        ),
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=12),
            scaleanchor="x",
            scaleratio=1,
            range=[-0.5, 14.5]
        ),
        autosize=False,
        width=1800,
        height=900,
        margin=dict(l=10, r=10, t=80, b=10),
    )

    plot_div = fig.to_html(full_html=False)
    return render(request, 'status_integralizacao.html', {'plot_div': plot_div})

def desempenho_aluno_periodo(request):
    import pandas as pd
    import plotly.graph_objects as go
    import os

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df_historico = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))
    df_alunos = pd.read_csv(os.path.join(data_dir, 'alunosPorCurso.csv'))

    df_historico['PERIODO_NUM'] = df_historico['PERIODO'].str.extract(r'(\d)')[0].astype(float)
    df_historico = df_historico.sort_values(['ID ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_NUM'])
    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    df_historico['ANO_PERIODO'] = df_historico['ANO'].astype(str) + ' - ' + df_historico['PERIODO']

    id_aluno = df_alunos['ID PESSOA'].iloc[0]
    dados_aluno = df_historico[df_historico['ID PESSOA'] == id_aluno].copy()
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
        height=600
    )

    alunos_options = [
        {'id': str(row['ID PESSOA']), 'label': f"{row['ID PESSOA']} - {row['NOME PESSOA']}"}
        for _, row in df_alunos.iterrows()
    ]

    plot_div = fig.to_html(full_html=False)
    return render(request, 'desempenho_aluno_periodo.html', {
        'plot_div': plot_div,
        'alunos_options': alunos_options,
        'selected_id': id_aluno,
    })

def heatmap_desempenho(request):
    import pandas as pd
    import numpy as np
    import plotly.graph_objects as go
    import os

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))

    matricula_id_col = 'MATR ALUNO'
    disciplinas_dict = dict(zip(df['COD ATIV CURRIC'], df['NOME ATIV CURRIC']))
    matriculas = df[matricula_id_col].unique().tolist()
    disciplinas = df['COD ATIV CURRIC'].unique().tolist()
    mapa_matriculas = {mat: i for i, mat in enumerate(matriculas)}
    mapa_disciplinas = {disc: i for i, disc in enumerate(disciplinas)}

    matriz = [[[] for _ in range(len(disciplinas))] for _ in range(len(matriculas))]
    for _, row in df.iterrows():
        i = mapa_matriculas[row[matricula_id_col]]
        j = mapa_disciplinas[row['COD ATIV CURRIC']]
        matriz[i][j].append(row['DESCR SITUACAO'])

    df_matriz = pd.DataFrame(
        [[', '.join(attempts) if attempts else '' for attempts in linha] for linha in matriz],
        index=matriculas,
        columns=[disciplinas_dict[cod] for cod in disciplinas]
    )
    if 'NOME PESSOA' in df.columns:
        nomes_por_matricula = df.drop_duplicates(matricula_id_col).set_index(matricula_id_col)['NOME PESSOA']
        df_matriz.index = [f"{mid} - {nomes_por_matricula.get(mid, '')}" for mid in df_matriz.index]

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
                f"<b>Aluno:</b> {nome_aluno}<br>"
                f"<b>Disciplina:</b> {disciplina}<br>"
                f"<b>Status:</b> Nenhum"
            )
        status_list = [s.strip() for s in status_str.split(',') if s.strip()]
        status_formatado = ""
        for s in status_list:
            partes = s.split('em')
            status_base = partes[0].strip()
            data = partes[1].strip() if len(partes) > 1 else None

            if status_base in aprovados:
                if data:
                    status_formatado += f"Aprovado em <b>{data}</b><br>"
                else:
                    status_formatado += "Aprovado<br>"
            elif status_base in reprovados:
                motivo = status_base.split('-')[1].strip() if '-' in status_base else status_base
                if data:
                    status_formatado += f"Reprovado por <b>{motivo}</b> em <b>{data}</b><br>"
                else:
                    status_formatado += f"Reprovado por <b>{motivo}</b><br>"
            elif status_base in matriculado:
                if data:
                    status_formatado += f"Matriculado em <b>{data}</b><br>"
                else:
                    status_formatado += "Matriculado<br>"
            else:
                if data:
                    status_formatado += f"{status_base} em <b>{data}</b><br>"
                else:
                    status_formatado += f"{status_base}<br>"
        status_final = status_list[-1] if status_list else 'Indefinido'
        return (
            f"<b>Aluno:</b> {nome_aluno}<br>"
            f"<b>Disciplina:</b> {disciplina}<br>"
            f"<b>Histórico:</b><br>{status_formatado}"
            f"<b>Status Final:</b> <i>{status_final}</i>"
        )

    hover_text = df_matriz.apply(
        lambda row: [
            construir_tooltip(row.name, df_matriz.columns[j], row.iloc[j])
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
        )
    ))

    fig.update_layout(
        title='Desempenho Acadêmico por Matrícula e Disciplina',
        xaxis=dict(title='Disciplinas', tickangle=45, tickfont=dict(size=9)),
        yaxis=dict(title='Matrículas', tickfont=dict(size=9)),
        autosize=True,
        margin=dict(l=50, r=50, t=80, b=100),
        height=1200,
    )

    plot_div = fig.to_html(full_html=False)
    return render(request, 'heatmap_desempenho.html', {'plot_div': plot_div})