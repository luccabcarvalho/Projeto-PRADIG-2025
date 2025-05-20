import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output

# Leitura dos dados
caminho_hist = r'docs\HistoricoEscolarSimplificado.csv'
caminho_alunos = r'docs\alunosPorCurso.csv'

df = pd.read_csv(caminho_hist)
df_alunos = pd.read_csv(caminho_alunos)

# Status
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

# Processamento dos dados

df['PERIODO_ORD'] = df['PERIODO'].str.extract(r'(\d)')[0].astype(float)
df = df.sort_values(['ID ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_ORD'])

df_alunos = df_alunos.sort_values('PERIODO INGRESSO')

# Criar coluna ANO_PERIODO
df['ANO_PERIODO'] = df['ANO'].astype(str) + ' - ' + df['PERIODO']

# App
app = Dash(__name__)

app.layout = html.Div([
    html.H2("Desempenho Acadêmico por Aluno"),
    dcc.Dropdown(
        id='aluno-dropdown',
        options=[{'label': nome, 'value': aid} for nome, aid in zip(df_alunos['NOME PESSOA'], df_alunos['ID PESSOA'])],
        placeholder="Selecione um aluno",
        style={'width': '60%'}
    ),
    dcc.Graph(id='grafico-desempenho')
])

@app.callback(
    Output('grafico-desempenho', 'figure'),
    Input('aluno-dropdown', 'value')
)
def atualizar_grafico(aluno_id):
    if aluno_id is None:
        return go.Figure()

    df_aluno = df[df['ID PESSOA'] == aluno_id].copy()
    df_aluno['SITUACAO'] = df_aluno['DESCR SITUACAO'].str.strip()
    df_aluno['APROVADO'] = df_aluno['SITUACAO'].isin(aprovados)
    df_aluno['REPROVADO'] = df_aluno['SITUACAO'].isin(reprovados)
    df_aluno['CARGA HORARIA'] = df_aluno['TOTAL CARGA HORARIA']
    df_aluno['DISC_CARGA'] = df_aluno['NOME ATIV CURRIC'] + ' (' + df_aluno['CARGA HORARIA'].astype(str) + 'h)'

    def ordenar_periodo(periodo_str):
        ano, per = periodo_str.split(' - ')
        num = 1 if '1' in per else 2
        return int(ano) * 10 + num

    df_aluno['ORD'] = df_aluno['ANO_PERIODO'].apply(ordenar_periodo)

    grupos = df_aluno.groupby('ANO_PERIODO')
    lista_periodos = []
    lista_aprovado = []
    lista_reprovado = []
    lista_hover = []

    carga_acumulada = 0
    for nome, grupo in sorted(grupos, key=lambda x: ordenar_periodo(x[0])):
        aprovados_periodo = grupo[grupo['APROVADO']]
        reprovados_periodo = grupo[grupo['REPROVADO']]

        carga_aprovada = aprovados_periodo['CARGA HORARIA'].sum()
        carga_reprovada = reprovados_periodo['CARGA HORARIA'].sum()

        lista_periodos.append(nome)
        lista_aprovado.append(carga_aprovada)
        lista_reprovado.append(carga_reprovada)

        carga_acumulada += carga_aprovada

        texto_aprovado = "<br>".join(aprovados_periodo['DISC_CARGA']) if not aprovados_periodo.empty else "Nenhuma disciplina aprovada"
        texto_reprovado = "<br>".join(reprovados_periodo['DISC_CARGA']) if not reprovados_periodo.empty else "Nenhuma disciplina reprovada"

        texto = (
            f"<b>APROVADO</b><br>{texto_aprovado}<br><b>Total acumulado: {carga_acumulada}h</b><br><br>"
            f"<b>REPROVADO</b><br>{texto_reprovado}"
        )
        lista_hover.append(texto)

    base_aprovado = np.cumsum([0] + lista_aprovado[:-1])

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=lista_periodos,
        y=lista_aprovado,
        base=base_aprovado,
        name='Aprovado',
        marker_color='green',
        hoverinfo='text',
        hovertext=lista_hover
    ))

    fig.add_trace(go.Bar(
        x=lista_periodos,
        y=lista_reprovado,
        base=base_aprovado + np.array(lista_aprovado),
        name='Reprovado',
        marker_color='red',
        hoverinfo='text',
        hovertext=lista_hover
    ))

    fig.update_layout(
        barmode='overlay',
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária Acumulada',
        title='Desempenho por Período (Empilhado Acumulativo)',
        height=600
    )

    return fig


if __name__ == '__main__':
    app.run(debug=True)
