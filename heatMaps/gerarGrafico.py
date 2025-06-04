import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, html, dcc

df = pd.read_csv(r'docs/HistoricoEscolarSimplificado.csv')
df_alunos = pd.read_csv(r'docs/alunosPorCurso.csv')

df_alunos.columns = df_alunos.columns.str.strip()

df_alunos = df_alunos.sort_values('PERIODO INGRESSO')

df['PERIODO_ORD'] = df['PERIODO'].str.extract(r'(\d)')[0].astype(float)

df = df.sort_values(['ID ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_ORD'], ascending=[True, True, True, True])

disciplinas = sorted(df['COD ATIV CURRIC'].unique())
disciplinas_dict = dict(zip(df['COD ATIV CURRIC'], df['NOME ATIV CURRIC']))

mapa_disciplinas = {cod: j for j, cod in enumerate(disciplinas)}
mapa_alunos = {aid: i for i, aid in enumerate(df_alunos['ID PESSOA'])}

n_alunos = len(df_alunos)
n_disciplinas = len(disciplinas)
matriz = [[[] for _ in range(n_disciplinas)] for _ in range(n_alunos)]

for _, row in df.iterrows():
    i = mapa_alunos[row['ID PESSOA']]
    j = mapa_disciplinas[row['COD ATIV CURRIC']]
    matriz[i][j].append(row['DESCR SITUACAO'])

df_matriz = pd.DataFrame(
    [[', '.join(attempts) if attempts else '' for attempts in linha] for linha in matriz],
    index=df_alunos['NOME PESSOA'].tolist(),
    columns=[disciplinas_dict[cod] for cod in disciplinas]
)

with open('matriz_status.txt', 'w', encoding='utf-8') as f:
    for _, row in df_matriz.iterrows():
        f.write('\t'.join(str(cell) if cell else '-' for cell in row) + '\n')

df_matriz.to_csv('matriz.csv', encoding='utf-8', sep=';', index=True)



df_matriz = pd.read_csv('matriz.csv', sep=';', index_col=0, low_memory=False)

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
    elif all(s in matriculado for s in status_list):
        return 0
    elif all(s in reprovados for s in status_list):
        return -1
    else:
        return 0  # estado misto, indefinido → amarelo por padrão

def construir_tooltip(nome_aluno, disciplina, status_str):
    if pd.isna(status_str) or not status_str.strip():
        return f'Aluno: {nome_aluno}<br>Disciplina: {disciplina}<br>Status: Nenhum'
    status_list = [s.strip() for s in status_str.split(',') if s.strip()]
    status_final = status_list[-1] if status_list else 'Indefinido'
    status_formatado = '<br>'.join(status_list)
    return (
        f"<b>Aluno:</b> {nome_aluno}<br>"
        f"<b>Disciplina:</b> {disciplina}<br>"
        f"<b>Status:</b><br>{status_formatado}<br>"
        f"<b>Status Final:</b> {status_final}"
    )

df_numerico = df_matriz.map(classificar_status)


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
        [0.0, 'red'],      # -1 → Reprovado/Trancado
        [0.5, 'yellow'],   #  0 → Apenas matriculado
        [1.0, 'green']     #  1 → Aprovado
    ],
    colorbar=dict(
        title='Status',
        tickvals=[-1, 0, 1],
        ticktext=['Reprovado/Trancado', 'Matriculado', 'Aprovado']
    )
))

fig.update_layout(
        title='Desempenho Acadêmico por Aluno e Disciplina',
        xaxis=dict(title='Disciplinas', tickangle=45, tickfont=dict(size=9)),
        yaxis=dict(title='Alunos', tickfont=dict(size=9)),
        autosize=True,
        margin=dict(l=50, r=50, t=80, b=100),
        height=1200,
    )


# Cria o app
app = Dash(__name__)

app.layout = html.Div([
    html.H2("Heatmap de Desempenho Acadêmico"),
    dcc.Graph(figure=fig, style={'width': '100vw', 'height': '100vh'})
])

if __name__ == '__main__':
    app.run(debug=True)
