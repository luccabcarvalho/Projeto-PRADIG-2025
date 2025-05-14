import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output

# Leitura dos dados
caminho_hist = r'e:\Teste Plots\Semana 3 - Heat Maps\HistoricoEscolarSimplificado.csv'
caminho_alunos = r'e:\Teste Plots\Semana 3 - Heat Maps\alunosPorCurso.csv'

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

    # Agrupa por ANO_PERIODO
    df_grouped = df_aluno.groupby('ANO_PERIODO').agg({
        'CARGA HORARIA': 'sum',
        'APROVADO': lambda x: df_aluno.loc[x.index, 'CARGA HORARIA'][x].sum(),
        'REPROVADO': lambda x: df_aluno.loc[x.index, 'CARGA HORARIA'][x].sum()
    }).reset_index()

    # Ordena cronologicamente
    def ordenar_periodo(periodo_str):
        ano, per = periodo_str.split(' - ')
        num = 1 if '1' in per else 2
        return int(ano) * 10 + num

    df_grouped['ORD'] = df_grouped['ANO_PERIODO'].apply(ordenar_periodo)
    df_grouped = df_grouped.sort_values('ORD').reset_index(drop=True)

    # Cálculo da base acumulada
    df_grouped['BASE'] = df_grouped['APROVADO'].cumsum().shift(fill_value=0)

    fig = go.Figure()

    # Barras de aprovado começam a partir da base acumulada
    fig.add_trace(go.Bar(
        x=df_grouped['ANO_PERIODO'],
        y=df_grouped['APROVADO'],
        base=df_grouped['BASE'],
        name='Aprovado',
        marker_color='green'
    ))

    # Barras de reprovado empilhadas em cima do aprovado no mesmo período
    fig.add_trace(go.Bar(
        x=df_grouped['ANO_PERIODO'],
        y=df_grouped['REPROVADO'],
        base=df_grouped['BASE'] + df_grouped['APROVADO'],
        name='Reprovado',
        marker_color='red'
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
