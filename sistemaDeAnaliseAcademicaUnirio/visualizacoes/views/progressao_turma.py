from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import plotly.graph_objects as go

USER_ID = 'user1'

def progressao_turma(request):
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID) # Definindo caminhos dos arquivos
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')

    df_historico = pd.read_csv(historico_path) # Carregamento dos dados
    df_alunos = pd.read_csv(alunos_path)

    df_historico['PERIODO_NUM'] = df_historico['PERIODO'].str.extract(r'(\d)')[0].astype(float) # Extrai o número do período
    df_historico = df_historico.sort_values(['MATR ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_NUM']) # Ordena o histórico por aluno, disciplina, ano e período
    df_alunos = df_alunos.sort_values('PERIODO INGRESSO') # Ordena os alunos por período de ingressão
    df_historico['ANO_PERIODO'] = df_historico['ANO'].astype(str) + ' - ' + df_historico['PERIODO'] # Cria uma nova coluna combinando ano e período
    df_alunos['TURMA'] = df_alunos['PERIODO INGRESSO'].str.split('°').str[0] # Cria o conceito de turma a partir do ano/período de ingresso
    
    turma_param = request.GET.get('turma') # Obtém o parâmetro da turma selecionada no dropdown
    if turma_param and turma_param in df_alunos['TURMA'].values:
            turma = turma_param # Como eu transformo turma em algo tipo 2002/2, não dá para tratar como int
    else:
        turma = df_alunos['TURMA'].iloc[0] # Se o parâmetro não for válido, seleciona a primeira turma disponível

    matriculas_turma = df_alunos[df_alunos['TURMA'] == turma]['ID PESSOA'] # Filtra os alunos das turmas selecionadas
    dados_turma = df_historico[df_historico['ID PESSOA'].isin(matriculas_turma)].copy() # O isin filtra o histórico, deixxando apenas ... entendeu né?
    if dados_turma.empty:
        turmas_options = [ # Cria as opções de turmas para o dropdown
            {'id': t, 'label': t}
            for t in df_alunos['TURMA'].unique()
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'progressao_turma.html', { # Renderiza a template com a mensagem de erro e as opções de turmas
            'plot_div': '',
            'turmas_options': turmas_options,
            'selected_id': str(turma),
            'mensagem': mensagem,
        })

    dados_turma['STATUS'] = dados_turma['DESCR SITUACAO'].str.strip() # Limpa os espaços em branco dos status para garantir que a comparação funcione corretamente
    dados_turma['CARGA'] = dados_turma['TOTAL CARGA HORARIA'] # Cria uma nova coluna para a carga horária, que vai ser usada para calcular carga acumulada

    def ordenar_periodo(periodo): # Função para ordenar os períodos corretamente, convertendo o formato "ANO - PERIODO" em um número que possa ser ordenado
        ano, per = periodo.split(' - ')
        return int(ano) * 10 + (1 if '1' in per else 2)

    periodos = sorted(dados_turma['ANO_PERIODO'].unique(), key=ordenar_periodo) # Ordena os períodos usando a função de ordenação personalizada
    if not periodos:
        turmas_options = [
            {'id': t, 'label': t}
            for t in df_alunos['TURMA'].unique()
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'progressao_turma.html', {
            'plot_div': '',
            'turmas_options': turmas_options,
            'selected_id': str(turma),
            'mensagem': mensagem,
        })
    
    status_aprovados = {
        'APV - Aprovado': '#006400',
        'APV- Aprovado': '#006400',
        'APV - Aprovado sem nota': '#32CD32',
        'ADI - Aproveitamento': '#7CFC00',
        'ADI - Aproveitamento de créditos da disciplina': '#ADFF2F',
        'ADI - Dispensa com nota': '#228B22',
        'DIS - Dispensa sem nota': '#32CD32',
    }

    linhas = []
    dados_aprovados = dados_turma[dados_turma['STATUS'].isin(status_aprovados.keys())] # Filtra os dados para incluir apenas os status de aprovação

    for matr, dados_aluno in dados_aprovados.groupby('ID PESSOA'): # Agrupa os dados por matrícula do aluno para criar uma linha para cada aluno
        nome = dados_aluno['NOME PESSOA'].iloc[0] # Obtém o nome do aluno para usar na legenda do gráfico
        carga_acumulada = (
            dados_aluno.groupby('ANO_PERIODO')['CARGA'].sum().reindex(periodos, fill_value=0).cumsum() # Agrupa por período, soma a carga horária, reindexa para garantir que todos os períodos estejam presentes e calcula a carga acumulada
        )
        linha = go.Scatter(  # Não existe nada como "go.Lines", o padrão é go.Scatter com mode='lines'
            x=periodos,
            y=carga_acumulada,
            mode='lines+markers',  # Mantenha a linha com marcadores
            name=f"{matr} - {nome}",
            )
        linhas.append(linha)  # Adiciona a linha à lista de linhas do gráfico
    if not linhas:
         turmas_options = [{'id': t, 'label': t} for t in df_alunos['TURMA'].unique()]
         return render(request, 'progressao_turma.html', {
            'plot_div': '',
            'turmas_options': turmas_options,
            'selected_id': str(turma),
            'mensagem': "Não há dados disponíveis para a turma selecionada.",
        })

    carga_referencia = 3240
    linha_referencia = go.Scatter(  # Cria uma linha de referência para a carga horária total
        x=periodos,
        y=[carga_referencia] * len(periodos),
        mode='lines',
        name='C.H. Total',
        line=dict(color='rgba(100,100,100,0.3)')
    )
    linhas.append(linha_referencia)

    # Cria a figura usando as linhas criadas anteriormente
    fig = go.Figure(linhas)
    fig.update_layout(  # Configurações de layout do gráfico
        font=dict(size=18),
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária',
        xaxis=dict(tickfont=dict(size=16)),
        yaxis=dict(tickfont=dict(size=16)),
        height=800,
        width=1800
    )

    turmas_options = [
        {'id': t, 'label': t}
        for t in df_alunos['TURMA'].unique()
    ]

    # Converte a figura para HTML para ser renderizada na template
    plot_div = fig.to_html(full_html=False)
    return render(request, 'progressao_turma.html', {
        'plot_div': plot_div,
        'turmas_options': turmas_options,
        'selected_id': str(turma),
    })
