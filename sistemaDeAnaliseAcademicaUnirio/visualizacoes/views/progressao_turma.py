from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import plotly.graph_objects as go

USER_ID = 'user1'

# Conjuntos que classificam a forma de evasão para determinar a cor do marcador final
EVASAO_BOA = {'CON - Curso concluído'}   # verde
EVASAO_SEM = {'Sem evasão'}              # sem destaque (aluno ainda ativo)

def dicionario_de_equivalencias():
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    equivalencias_path = os.path.join(USER_DIR, 'relacaoEquivalenciaDisciplinas.csv')
    df = pd.read_csv(equivalencias_path, encoding='latin1', sep=';')
    df_validos = df[df['NOME_DISC_EQUIV'].notna()][['NOME_DISCIPLINA', 'NOME_DISC_EQUIV']]
    # Extrai apenas o código (parte antes do ' - ')
    codigos_novos   = df_validos['NOME_DISCIPLINA'].str.split(' - ').str[0].str.strip()
    codigos_antigos = df_validos['NOME_DISC_EQUIV'].str.split(' - ').str[0].str.strip()
    mapeamento = {} # Dicionário vazio
    for antigo, novo in zip(codigos_antigos, codigos_novos): # Itera sobre os códigos formando pares
        if novo not in mapeamento: # Se o código novo ainda não tiver sido adicionado ao dicionário
            mapeamento[novo] = [] # Inicia uma lista vazia para armazenar códigos equivalentes
        mapeamento[novo].append(antigo) # Anexa o código antigo na lista do código novo equivalente
    return mapeamento

def dicionario_ch_curriculos():
    # Mapeia cada currículo (NUM VERSAO) para sua carga horária total de curso (CH TOTAL CURSO)
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    curriculos_path = os.path.join(USER_DIR, 'curriculos-bsi.csv')
    df = pd.read_csv(curriculos_path, encoding='utf-8', sep=';')
    # O arquivo tem uma linha por disciplina cadastrada em cada currículo, então NUM VERSAO se repete várias
    # vezes; CH TOTAL CURSO é constante dentro do mesmo NUM VERSAO, então basta a primeira ocorrência de cada versão
    ch_map = (
        df[['NUM VERSAO', 'CH TOTAL CURSO']]
        .drop_duplicates(subset='NUM VERSAO')
        .set_index('NUM VERSAO')['CH TOTAL CURSO']
        .to_dict()
    )
    return ch_map

def progressao_turma(request):
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID) # Definindo caminhos dos arquivos
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')

    equiv_map = dicionario_de_equivalencias() # Carrega o dicionário de equivalências
    ch_curriculos = dicionario_ch_curriculos() # Carrega a CH total de cada currículo (NUM VERSAO -> CH TOTAL CURSO)
    
    equiv_map_reverso = {}
    for novo, antigos in equiv_map.items():
        for antigo in antigos:
            if antigo not in equiv_map_reverso:
                equiv_map_reverso[antigo] = []
            equiv_map_reverso[antigo].append(novo)

    df_historico = pd.read_csv(historico_path, sep=None, engine='python') # Carregamento dos dados
    df_alunos = pd.read_csv(alunos_path, sep=None, engine='python')

    df_historico['PERIODO_NUM'] = df_historico['PERIODO'].str.extract(r'(\d)')[0].astype(float) # Extrai o número do período
    df_historico = df_historico.sort_values(['MATR ALUNO', 'COD ATIV CURRIC', 'ANO', 'PERIODO_NUM']) # Ordena o histórico por aluno, disciplina, ano e período
    df_alunos = df_alunos.sort_values('PERIODO INGRESSO') # Ordena os alunos por período de ingressão
    df_historico['ANO_PERIODO'] = df_historico['ANO'].astype(str) + ' - ' + df_historico['PERIODO'] # Cria uma nova coluna combinando ano e período
    df_alunos['TURMA'] = df_alunos['PERIODO INGRESSO'].str.split('°').str[0] # Cria o conceito de turma a partir do ano/período de ingresso

    # Converte o formato "2009/2°. semestre" (PERIODO EVASAO) para "2009 - 2°. semestre" (mesmo formato de ANO_PERIODO)
    def evasao_para_ano_periodo(periodo_evasao):
        if pd.isna(periodo_evasao) or not str(periodo_evasao).strip(): # Verifica NA
            return None
        partes = str(periodo_evasao).split('/') # Divide a string em /
        if len(partes) < 2: # Caso dê ruim, retorna None
            return None
        return f"{partes[0]} - {partes[1]}" # Retorna no formato da coluna ANO_PERIODO

    # Monta um dicionário de evasão indexado por ID PESSOA para consulta rápida dentro do loop
    df_evasao = (
        df_alunos[['ID PESSOA', 'FORMA EVASAO', 'PERIODO EVASAO']] # Colunas relevantes
        .drop_duplicates(subset='ID PESSOA') # Garante singularidade
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
    # Currículos (NUM VERSAO) que os alunos dessa turma efetivamente cursaram, usados para desenhar
    # uma linha de CH de referência por currículo (turmas mistas podem ter mais de um)
    curriculos_da_turma = sorted(df_alunos.loc[df_alunos['TURMA'] == turma, 'NUM VERSAO'].dropna().unique())
    dados_turma = df_historico[df_historico['ID PESSOA'].isin(matriculas_turma)].copy() # O isin filtra o histórico, deixando apenas os registros da turma selecionada
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

    # Status que representam aproveitamento/dispensa e precisam ser verificados no dicionário de equivalências
    status_adi = {
        'ADI - Aproveitamento',
        'ADI - Aproveitamento de créditos da disciplina',
        'ADI - Dispensa com nota',
        'DIS - Dispensa sem nota',
    }

    # Monta um dicionário (ID PESSOA, ANO_PERIODO) → label de trancamento para identificar quais períodos foram trancados e hoverizar essas infos
    CODIGOS_TRANCAMENTO = {
        'TRT0001': 'Período trancado',
        'TRT0002': 'Período trancado (Pandemia)',
    }
    trancamentos_df = dados_turma[dados_turma['COD ATIV CURRIC'].isin(CODIGOS_TRANCAMENTO)][
        ['ID PESSOA', 'ANO_PERIODO', 'COD ATIV CURRIC'] # Filtra disciplinas trancadas
    ].drop_duplicates(subset=['ID PESSOA', 'ANO_PERIODO'])
    trancamentos_map = {
        (row['ID PESSOA'], row['ANO_PERIODO']): CODIGOS_TRANCAMENTO[row['COD ATIV CURRIC']]
        for _, row in trancamentos_df.iterrows()
    }

    linhas = []
    dados_aprovados = dados_turma[dados_turma['STATUS'].isin(status_aprovados.keys())] # Filtra os dados para incluir apenas os status de aprovação

    # Remove entradas duplicadas de aproveitamento de um mesmo aluno, mantendo só a primeira cronologicamente
    dados_aprovados = dados_aprovados.drop_duplicates(subset=['ID PESSOA', 'COD ATIV CURRIC'], keep='first')

    # O groupby passou de 'MATR ALUNO' para 'ID PESSOA' porque o trancamentos_map usa ID PESSOA como chave
    for pessoa_id, dados_aluno in dados_aprovados.groupby('ID PESSOA'):
        nome = dados_aluno['NOME PESSOA'].iloc[0] # Obtém o nome do aluno para usar na legenda do gráfico
        matr = dados_aluno['MATR ALUNO'].iloc[0]  # Extrai a matrícula do dataframe (antes vinha direto do groupby)

        # Busca forma e período de evasão do aluno no dicionário montado anteriormente
        info_ev = evasao_map.get(pessoa_id, {})
        forma_evasao = info_ev.get('FORMA EVASAO', 'Sem evasão') or 'Sem evasão'
        periodo_evasao_ap = info_ev.get('ANO_PERIODO_EVASAO')  # já convertido para o formato "ANO - PERIODO"

        periodos_com_dados = sorted(dados_aluno['ANO_PERIODO'].unique(), key=ordenar_periodo) # Cria uma lista com todos os períodos cursados do aluno
        if not periodos_com_dados: # Verifica se lista vazia
            continue
        primeiro_periodo = periodos_com_dados[0] # Primeiro período cursado pelo aluno

        if forma_evasao not in EVASAO_SEM and periodo_evasao_ap and periodo_evasao_ap in periodos:
            ultimo_periodo = periodo_evasao_ap # Se o aluno evadiu, o último período é o de evasão
        else:
            ultimo_periodo = periodos_com_dados[-1] # Se não evadiu, é o último período com dados

        if primeiro_periodo not in periodos or ultimo_periodo not in periodos: # Se primeiro ou último período não existirem, pula aluno
            continue

        idx_primeiro = periodos.index(primeiro_periodo)
        idx_ultimo = periodos.index(ultimo_periodo)
        if idx_primeiro > idx_ultimo:
            continue

        x_linha = periodos[idx_primeiro:idx_ultimo + 1] # Eixo x limitado ao primeiro até o último período do aluno

        # Contabiliza as horas por período e coleta info de ADI para o hover
        horas_por_periodo = {p: 0.0 for p in x_linha} # Inicializa todas as horas como zero
        hover_adi = {p: [] for p in x_linha} # Inicializa as strings de hover ADI como listas vazias

        # Identifica disciplinas antigas substituídas e aloca a carga horária nova diretamente nos períodos passados
        disciplinas_substituidas = set()
        aproveitamentos_alocados_no_passado = set()
        aproveitamentos_ignorados = set() 
        
        for _, row in dados_aluno.iterrows(): # Busca disciplinas que são aproveitamentos e que possuem equivalência
            if row['STATUS'] in status_adi:
                cod_dispensa = row['COD ATIV CURRIC']
                carga_nova = row['CARGA']

                if cod_dispensa in equiv_map:
                    codigos_antigos = equiv_map[cod_dispensa]
                    
                    # Encontra em qual período do passado o aluno de fato realizou a disciplina antiga
                    reg_antigos = dados_turma[
                        (dados_turma['ID PESSOA'] == pessoa_id) &
                        (dados_turma['COD ATIV CURRIC'].isin(codigos_antigos))
                    ]
                    
                    # Só adiciona a carga quando existir um registro antigo no histórico
                    if not reg_antigos.empty:
                        periodo_destino = reg_antigos['ANO_PERIODO'].iloc[0]
                        if periodo_destino in horas_por_periodo:
                            horas_por_periodo[periodo_destino] += carga_nova
                            aproveitamentos_alocados_no_passado.add(cod_dispensa)

                        # Guarda os códigos antigos para ignorar suas cargas originais mais abaixo
                        for c_antigo in codigos_antigos:
                            disciplinas_substituidas.add(c_antigo)
                
                elif cod_dispensa in equiv_map_reverso:
                    codigos_novos = equiv_map_reverso[cod_dispensa]
                    reg_novos = dados_aluno[
                        (dados_aluno['COD ATIV CURRIC'].isin(codigos_novos))
                    ]
                    if not reg_novos.empty:
                        aproveitamentos_ignorados.add(cod_dispensa)

        for _, row in dados_aluno.iterrows(): # Percorre cada disciplina do aluno
            periodo = row['ANO_PERIODO']
            if periodo not in horas_por_periodo: # Ignora períodos fora do intervalo do aluno
                continue

            # Condições para controle do fluxo de soma
            e_dispensa = row['STATUS'] in status_adi # Verifica se é qualquer tipo de dispensa
            cod_atual = row['COD ATIV CURRIC']
            
            foi_materia_antiga_substituida = cod_atual in disciplinas_substituidas
            foi_dispensa_alocada_passado = cod_atual in aproveitamentos_alocados_no_passado
            foi_dispensa_ignorada = cod_atual in aproveitamentos_ignorados 

            # Só soma a carga no período atual se NÃO for NENHUMA dispensa e NÃO for a matéria antiga substituída
            if not foi_materia_antiga_substituida and not foi_dispensa_ignorada:
                if not e_dispensa or (e_dispensa and not foi_dispensa_alocada_passado):
                    horas_por_periodo[periodo] += row['CARGA'] # Acumula a carga horária no período

            if e_dispensa:
                if cod_atual in equiv_map:
                    reg_antigos = dados_turma[
                        (dados_turma['ID PESSOA'] == pessoa_id) &
                        (dados_turma['COD ATIV CURRIC'].isin(equiv_map[cod_atual]))
                    ]
                    # Só inclui a relação no hover quando houver registro antigo no histórico
                    if not reg_antigos.empty:
                        equivalentes = equiv_map[cod_atual]
                        hover_adi[periodo].append(f"<br>↔ {cod_atual} ← {', '.join(equivalentes)}") # Guarda a relação novo ← antigo(s) para o hover
                
                elif cod_atual in equiv_map_reverso and cod_atual not in aproveitamentos_ignorados:
                    equivalentes = equiv_map_reverso[cod_atual]
                    hover_adi[periodo].append(f"<br>↔ {cod_atual} (Antiga) dispensa {', '.join(equivalentes)}")

        # Calcula a carga acumulada como lista, período a período
        # O ponto de cada período representa o total acumulado até chegar nele,
        # ou seja, a carga do próprio período só passa a contar a partir do próximo.
        y_linha = []
        total = 0.0
        for p in x_linha:
            total += horas_por_periodo[p]
            y_linha.append(total)

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

        # customdata assume uma lista de triplas que mostra no hover o nome, status do período e info de ADI
        customdata = []
        for periodo in x_linha:
            status_periodo = trancamentos_map.get((pessoa_id, periodo), 'Cursando')
            adi_str = ''.join(hover_adi[periodo]) # '' se não há ADI, ou '<br>↔ ...' para cada equivalência
            customdata.append([nome, status_periodo, adi_str])

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
                '%{customdata[2]}'   # vazio ou info de ADI com <br> embutido
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

    grupos_sobrepostos = {} # Cria dicionário vazio
    for i, linha in enumerate(linhas): # Itera sobre cada linha do gráfico (cada aluno)
        chave = tuple(zip(linha.x, tuple(round(v, 2) for v in linha.y))) # Cria uma chave única para cada combinação de pontos da linha
        grupos_sobrepostos.setdefault(chave, []).append(i) # Se a chave ainda não existir, cria uma lista vazia e adiciona o índice da linha atual.
        # Dessa forma, linhas com os mesmos pontos (mesmo x e y) serão agrupadas juntas.

    for indices in grupos_sobrepostos.values(): # Percorre os índices das linhas sobrepostas
        n = len(indices) 
        if n < 2: # Se não houver sobreposição, não precisa ajustar nada
            continue 
        for pos, i in enumerate(indices):
            linha = linhas[i]
            y_original = list(linha.y)
            offset = (pos - (n - 1) / 2) * 15
            linha.y = [v + offset for v in y_original]
            linha.customdata = [list(cd) + [y_original[j]] for j, cd in enumerate(linha.customdata)]
            linha.hovertemplate = linha.hovertemplate.replace('%{y}h', '%{customdata[3]}h')

    # Adiciona uma linha de CH total de referência para cada currículo que os alunos da turma cursaram
    # (turmas mistas, com alunos em currículos diferentes, mostram uma linha por currículo em vez de um valor fixo)
    CORES_REFERENCIA = [
        'rgba(100,100,100,0.6)',
        'rgba(31,119,180,0.6)',
        'rgba(214,39,40,0.6)',
        'rgba(148,103,189,0.6)',
        'rgba(255,127,14,0.6)',
    ]
    for i, versao in enumerate(curriculos_da_turma):
        carga_referencia = ch_curriculos.get(versao) # CH total cadastrada em curriculos-bsi.csv para esse currículo
        if carga_referencia is None: # Currículo sem CH total cadastrada em curriculos-bsi.csv: pula em vez de quebrar o gráfico
            continue
        linha_referencia = go.Scatter(  # Cria uma linha de referência para a carga horária total desse currículo
            x=periodos,
            y=[carga_referencia] * len(periodos),
            mode='lines',
            name=f'C.H. Total - {versao} ({carga_referencia}h)',
            line=dict(color=CORES_REFERENCIA[i % len(CORES_REFERENCIA)], dash='dash'),
            hovertemplate=f'C.H. Total - Currículo {versao}: %{{y}}h<extra></extra>', # Sem período: só CH total e o currículo a que ela pertence
        )
        linhas.append(linha_referencia)

    # Cria a figura usando as linhas criadas anteriormente
    fig = go.Figure(linhas)
    fig.update_layout(  # Configurações de layout do gráfico
        font=dict(size=18),
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária',
        xaxis=dict(tickfont=dict(size=16), categoryorder='array', categoryarray=periodos),
        yaxis=dict(tickfont=dict(size=16)),
        height=800,
        autosize=True,
        margin=dict(l=80, r=20, t=40, b=150)
    )

    turmas_options = [{'id': t, 'label': t} for t in df_alunos['TURMA'].unique()]
    
    # Converte a figura para HTML para ser renderizada na template
    plot_div = fig.to_html(full_html=False)
    return render(request, 'progressao_turma.html', {
        'plot_div': plot_div,
        'turmas_options': turmas_options,
        'selected_id': str(turma),
    })