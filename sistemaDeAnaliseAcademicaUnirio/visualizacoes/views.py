import pandas as pd
import numpy as np
import plotly.graph_objects as go
from django.shortcuts import render
from django.urls import reverse
import os

def status_integralizacao(request):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(BASE_DIR, 'visualizacoes', 'data')
    df_alunos = pd.read_csv(os.path.join(data_dir, 'alunosPorCurso.csv'))
    df_historico = pd.read_csv(os.path.join(data_dir, 'HistoricoEscolarSimplificado.csv'))

    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    alunos = df_historico['MATR ALUNO'].unique().tolist()

    alunos_dict = {}
    for idx, row in enumerate(df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().itertuples(index=False)):
        alunos_dict[idx] = {
            'MATR ALUNO': row[0],
            'NOME PESSOA': row[1]
        }

    periodos_unicos = df_historico[['ANO', 'PERIODO']].drop_duplicates().reset_index(drop=True)
    periodos_unicos = periodos_unicos[periodos_unicos['ANO'].astype(str).str.isnumeric()].reset_index(drop=True)

    periodos_dict = {}
    for idx, row in periodos_unicos.iterrows():
        periodos_dict[idx] = {
            'ANO': row['ANO'],
            'PERIODO': row['PERIODO']
        }

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

    matriculas_validas = set(alunos_dict[idx]['MATR ALUNO'] for idx in alunos_dict)
    periodos_validos = set((periodos_dict[idx]['ANO'], periodos_dict[idx]['PERIODO']) for idx in periodos_dict)

    matriz_geral = {}

    for _, row in df_historico.iterrows():
        matr = row['MATR ALUNO']
        periodo = (row['ANO'], row['PERIODO'])
        if matr not in matriculas_validas or periodo not in periodos_validos:
            continue
        if matr not in matriz_geral:
            matriz_geral[matr] = {}
        if periodo not in matriz_geral[matr]:
            matriz_geral[matr][periodo] = {}

    for _, row in df_historico.iterrows():
        matr = row['MATR ALUNO']
        periodo = (row['ANO'], row['PERIODO'])
        if matr not in matriculas_validas or periodo not in periodos_validos:
            continue
        nome = row['NOME PESSOA']
        status = row['DESCR SITUACAO']

        celula = matriz_geral[matr][periodo]
        if not celula:
            matriz_geral[matr][periodo] = {
                'nome': nome,
                'aprovacoes': [],
                'reprovacoes': [],
                'outros': []
            }
            celula = matriz_geral[matr][periodo]
        if status in status_aprovados:
            celula['aprovacoes'].append({
                'nome': row['NOME ATIV CURRIC'],
                'status': row['DESCR SITUACAO'],
                'codigo': row['COD ATIV CURRIC']
            })
        elif status in status_reprovados:
            celula['reprovacoes'].append({
                'nome': row['NOME ATIV CURRIC'],
                'status': row['DESCR SITUACAO'],
                'codigo': row['COD ATIV CURRIC']
            })
        else:
            celula['outros'].append({
                'nome': row['NOME ATIV CURRIC'],
                'status': row['DESCR SITUACAO'],
                'codigo': row['COD ATIV CURRIC']
            })

    colunas = []
    cores = []
    for nome, tam, cor in blocos:
        colunas += [nome] + [""] * (tam - 1)
        cores += [cor] * tam
    n_periodos = len(colunas)

    # Geração dos labels dos períodos para cada (ano, periodo)
    periodo_label_dict = {}
    for idx, row in periodos_unicos.iterrows():
        ano = str(row['ANO'])
        periodo = str(row['PERIODO']).replace('. semestre', '').strip()
        label = ano[-2:] + '/' + periodo
        periodo_label_dict[(row['ANO'], row['PERIODO'])] = label

    # Mapeamento matrícula -> nome
    mapa_matricula_nome = {alunos_dict[idx]['MATR ALUNO']: alunos_dict[idx]['NOME PESSOA'] for idx in alunos_dict}

    # Para cada aluno, lista de períodos ordenados
    aluno_periodos = {}
    for matr in matriz_geral:
        periodos = list(matriz_geral[matr].keys())
        periodos.sort()
        labels = [periodo_label_dict.get(p, '') for p in periodos]
        aluno_periodos[matr] = labels

    # Função para gerar tooltip a partir da célula já montada
    def gerar_tooltip_celula(matr, periodo):
        celula = matriz_geral[matr][periodo]
        nome = celula.get('nome', str(matr))
        periodo_label = periodo_label_dict.get(periodo, f"{periodo[0]}/{periodo[1]}")
        aprovadas = [f"{d['codigo']} - {d['nome']}" for d in celula.get('aprovacoes', [])]
        reprovadas = [f"{d['codigo']} - {d['nome']}" for d in celula.get('reprovacoes', [])]
        outros = [f"{d['codigo']} - {d['nome']} [{d['status']}]" for d in celula.get('outros', [])]
        tooltip = f"<b>Aluno:</b> {nome}<br><b>Período:</b> {periodo_label}<br>"
        if aprovadas:
            tooltip += "<b>Aprovadas:</b><br>" + "<br>".join(aprovadas) + "<br>"
        if reprovadas:
            tooltip += "<b>Reprovadas:</b><br>" + "<br>".join(reprovadas) + "<br>"
        if outros:
            tooltip += "<b>Outros:</b><br>" + "<br>".join(outros) + "<br>"
        return tooltip

    matriculas = list(matriz_geral.keys())
  
    matriz = np.full((len(matriculas), n_periodos), '', dtype=object)
    tooltip_matriz = np.full((len(matriculas), n_periodos), '', dtype=object)

    aluno_labels_tooltips = {}
    for matr in matriculas:
        periodos = sorted(matriz_geral[matr].keys())
        labels = [periodo_label_dict.get(p, '') for p in periodos]
        tooltips = [gerar_tooltip_celula(matr, p) for p in periodos]
        aluno_labels_tooltips[matr] = (labels, tooltips)

    # Preenche as matrizes em um único loop
    for idx, matr in enumerate(matriculas):
        labels, tooltips = aluno_labels_tooltips[matr]
        limite = min(len(labels), n_periodos)
        if limite > 0:
            matriz[idx, :limite] = labels[:limite]
            tooltip_matriz[idx, :limite] = tooltips[:limite]
        if len(labels) > n_periodos:
            matriz[idx, -1] = '+'
            excedentes = labels[n_periodos - 1:]
            tooltip_matriz[idx, -1] = 'Períodos excedentes: ' + ', '.join(excedentes)

    fig = go.Figure(data=go.Heatmap(
        z=[[i for i in range(n_periodos)] for _ in range(len(matriculas))],
        x=[f'{colunas[i]} {i+1}' for i in range(n_periodos)],
        y=[f"{matr} - {mapa_matricula_nome.get(matr, '')}" for matr in matriculas],
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
            tickangle=45,
            side='top',
            range=[-0.5, n_periodos-0.5]
        ),
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=12),
            scaleanchor="x",
            scaleratio=1,
            range=[-0.5, len(matriculas)-0.5]
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

    # Corrigir aqui: pegar o ID do aluno da request ou usar o primeiro como padrão
    id_aluno_param = request.GET.get('id_aluno')
    if id_aluno_param:
        try:
            id_aluno = int(id_aluno_param)
            # Verificar se o aluno existe nos dados
            if id_aluno not in df_alunos['ID PESSOA'].values:
                id_aluno = df_alunos['ID PESSOA'].iloc[0]
        except (ValueError, TypeError):
            id_aluno = df_alunos['ID PESSOA'].iloc[0]
    else:
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
        'selected_id': str(id_aluno),  # Converter para string para comparação no template
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

def home(request):
    return render(request, 'home.html')