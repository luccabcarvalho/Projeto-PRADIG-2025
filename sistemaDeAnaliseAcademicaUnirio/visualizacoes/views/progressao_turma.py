from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import plotly.graph_objects as go

USER_ID = 'user1'

# Conjuntos que classificam a forma de evasão para determinar a cor do marcador final
EVASAO_BOA = {'CON - Curso concluído'}   # verde
EVASAO_SEM = {'Sem evasão'}              # sem destaque (aluno ainda ativo)

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

    # Converte o formato "2009/2°. semestre" (PERIODO EVASAO) para "2009 - 2°. semestre" (mesmo formato de ANO_PERIODO)
    def evasao_para_ano_periodo(periodo_evasao):
        if pd.isna(periodo_evasao) or not str(periodo_evasao).strip():
            return None
        partes = str(periodo_evasao).split('/')
        if len(partes) < 2:
            return None
        return f"{partes[0]} - {partes[1]}" # oiiii

    # Monta um dicionário de evasão indexado por ID PESSOA para consulta rápida dentro do loop
    df_evasao = (
        df_alunos[['ID PESSOA', 'FORMA EVASAO', 'PERIODO EVASAO']]
        .drop_duplicates(subset='ID PESSOA')
        .copy()
    )
    df_evasao['ANO_PERIODO_EVASAO'] = df_evasao['PERIODO EVASAO'].apply(evasao_para_ano_periodo)
    evasao_map = df_evasao.set_index('ID PESSOA').to_dict('index')

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

    # Monta um dicionário (ID PESSOA, ANO_PERIODO) → label de trancamento para identificar quais períodos foram trancados e hoverizar essas infos
    CODIGOS_TRANCAMENTO = {
        'TRT0001': 'Período trancado',
        'TRT0002': 'Período trancado (Pandemia)',
    }
    trancamentos_df = dados_turma[dados_turma['COD ATIV CURRIC'].isin(CODIGOS_TRANCAMENTO)][
        ['ID PESSOA', 'ANO_PERIODO', 'COD ATIV CURRIC']
    ].drop_duplicates(subset=['ID PESSOA', 'ANO_PERIODO'])
    trancamentos_map = {
        (row['ID PESSOA'], row['ANO_PERIODO']): CODIGOS_TRANCAMENTO[row['COD ATIV CURRIC']]
        for _, row in trancamentos_df.iterrows()
    }

    linhas = []
    dados_aprovados = dados_turma[dados_turma['STATUS'].isin(status_aprovados.keys())] # Filtra os dados para incluir apenas os status de aprovação

    # O groupby passou de 'MATR ALUNO' para 'ID PESSOA' porque o trancamentos_map usa ID PESSOA como chave
    for pessoa_id, dados_aluno in dados_aprovados.groupby('ID PESSOA'):
        nome = dados_aluno['NOME PESSOA'].iloc[0] # Obtém o nome do aluno para usar na legenda do gráfico
        matr = dados_aluno['MATR ALUNO'].iloc[0]  # Extrai a matrícula do dataframe (antes vinha direto do groupby)

        # Busca forma e período de evasão do aluno no dicionário montado anteriormente
        info_ev = evasao_map.get(pessoa_id, {})
        forma_evasao = info_ev.get('FORMA EVASAO', 'Sem evasão') or 'Sem evasão'
        periodo_evasao_ap = info_ev.get('ANO_PERIODO_EVASAO')  # já convertido para o formato "ANO - PERIODO"

        carga_acumulada = (
            dados_aluno.groupby('ANO_PERIODO')['CARGA'].sum().reindex(periodos, fill_value=0).cumsum() # Agrupa por período, soma a carga horária, reindexa para garantir que todos os períodos estejam presentes e calcula a carga acumulada
        )

        x_linha = list(periodos) # Cria cópia dos valores para poder modificar caso o aluno tenha saído do curso
        y_linha = list(carga_acumulada.values)

        # Trunca a linha no período de evasão usando PERIODO EVASAO do alunosPorCurso
        if forma_evasao not in EVASAO_SEM:
            if periodo_evasao_ap and periodo_evasao_ap in periodos:
                idx_ev = periodos.index(periodo_evasao_ap)
                x_linha = periodos[:idx_ev + 1]
                y_linha = list(carga_acumulada.values[:idx_ev + 1])
            else:
                # Período de evasão fora do range disponível no histórico:
                # limita ao último período em que o aluno registrou atividade
                periodos_com_dados = sorted(dados_aluno['ANO_PERIODO'].unique(), key=ordenar_periodo)
                if periodos_com_dados:
                    ultimo = periodos_com_dados[-1]
                    if ultimo in periodos:
                        idx_ultimo = periodos.index(ultimo)
                        x_linha = periodos[:idx_ultimo + 1]
                        y_linha = list(carga_acumulada.values[:idx_ultimo + 1])

        # Determina a cor do último marcador conforme o tipo de saída do aluno
        if forma_evasao in EVASAO_BOA:
            cor_ultimo = '#2ecc40'  
        elif forma_evasao in EVASAO_SEM:
            cor_ultimo = None        
        else:
            cor_ultimo = '#ff4136'   

        marker_color = ( # Transforma todos os pontos em cinza e o último na cor definida acima
            ['rgba(100,100,100,0.5)'] * (len(x_linha) - 1) + [cor_ultimo]
            if cor_ultimo and x_linha
            else None
        )

        # customdata agora é uma lista de pares que mostra no hover se o aluno tá cursando ou com período trancado
        customdata = []
        for periodo in x_linha:
            status_periodo = trancamentos_map.get((pessoa_id, periodo), 'Cursando')
            customdata.append([nome, status_periodo])

        if forma_evasao not in EVASAO_SEM and customdata: # Se saiu do curso, substitui o status do último ponto pelo motivo de saída
            customdata[-1][1] = forma_evasao

        linha = go.Scatter(  # Não existe nada como "go.Lines", o padrão é go.Scatter com mode='lines'
            x=x_linha,
            y=y_linha,
            mode='lines+markers',
            name=f"{matr} - {nome}",
            marker=dict(color=marker_color, size=8) if marker_color else dict(size=8),
            customdata=customdata,
            hovertemplate=( 
                '<b>%{customdata[0]}</b><br>'
                'Período: %{x}<br>'
                'Carga H. acumulada: %{y}h<br>'
                'Status: %{customdata[1]}'
                '<extra></extra>'
            ),
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
        autosize=True,
        margin=dict(l=80, r=20, t=40, b=150)
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