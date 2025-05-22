import pandas as pd
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output

# Leitura dos dados
CAMINHO_HISTORICO = r'docs\HistoricoEscolarSimplificado.csv'
CAMINHO_ALUNOS = r'docs\alunosPorCurso.csv'

df_historico = pd.read_csv(CAMINHO_HISTORICO)
df_alunos = pd.read_csv(CAMINHO_ALUNOS)

# Mapas de status e cores
status_aprovados = {
    'APV - Aprovado': 0,
    'APV- Aprovado': 0,
    'APV - Aprovado sem nota': 1,
    'ADI - Aproveitamento': 2,
    'ADI - Aproveitamento de créditos da disciplina': 2,
    'ADI - Dispensa com nota': 3,
    'DIS - Dispensa sem nota': 4
}
status_reprovados = {
    'REP - Reprovado por nota/conceito': 0,
    'REF - Reprovado por falta': 1,
    'ASC - Reprovado sem nota': 2,
    'TRA - Trancamento de disciplina': 2
}
cores_aprovados = ['#006400', '#228B22', '#32CD32', '#7CFC00', '#ADFF2F']
cores_reprovados = ['#8B0000', '#CD5C5C', '#FFA07A']

# Pré-processamento
df_historico['PERIODO_NUM'] = df_historico['PERIODO'].str.extract(r'(\d)')[0].astype(float)
df_historico = df_historico.sort_values(['ID ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_NUM'])
df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
df_historico['ANO_PERIODO'] = df_historico['ANO'].astype(str) + ' - ' + df_historico['PERIODO']

# App Dash
app = Dash(__name__)

app.layout = html.Div([
    html.H2("Desempenho Acadêmico por Aluno"),
    dcc.Dropdown(
        id='aluno-dropdown',
        options=[
            {'label': nome, 'value': id_pessoa}
            for nome, id_pessoa in zip(df_alunos['NOME PESSOA'], df_alunos['ID PESSOA'])
        ],
        placeholder="Selecione um aluno",
        style={'width': '60%'}
    ),
    dcc.Graph(id='grafico-desempenho')
])

@app.callback(
    Output('grafico-desempenho', 'figure'),
    Input('aluno-dropdown', 'value')
)
def atualizar_grafico(id_aluno):
    if id_aluno is None:
        return go.Figure()

    dados_aluno = df_historico[df_historico['ID PESSOA'] == id_aluno].copy()
    dados_aluno['STATUS'] = dados_aluno['DESCR SITUACAO'].str.strip()
    dados_aluno['CARGA'] = dados_aluno['TOTAL CARGA HORARIA']
    dados_aluno['DISCIPLINA'] = dados_aluno['NOME ATIV CURRIC'] + ' (' + dados_aluno['CARGA'].astype(str) + 'h)'

    def ordenar_periodo(periodo):
        ano, per = periodo.split(' - ')
        return int(ano) * 10 + (1 if '1' in per else 2)

    dados_aluno['ORDEM'] = dados_aluno['ANO_PERIODO'].apply(ordenar_periodo)
    periodos = sorted(dados_aluno['ANO_PERIODO'].unique(), key=ordenar_periodo)

    cores_status = {}
    for status, idx in status_aprovados.items():
        cores_status[status] = cores_aprovados[idx]
    for status, idx in status_reprovados.items():
        cores_status[status] = cores_reprovados[idx]

    barras = []
    base_aprovada = pd.Series(0, index=periodos)

    # Plotar barras de aprovados primeiro, acumulando base
    for status in status_aprovados.keys():
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
            base=base_aprovada,
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)

        base_aprovada += y

    # Plotar barras de reprovados acima da base acumulada de aprovados
    for status in status_reprovados.keys():
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
            base=base_aprovada,
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)

    fig = go.Figure(barras)
    fig.update_layout(
        barmode='stack',
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária',
        title='Desempenho por Período com Acúmulo de Aprovados',
        height=600
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)
