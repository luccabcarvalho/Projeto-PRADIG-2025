from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from django.contrib import messages
import os
import time
import pandas as pd
import numpy as np
import plotly.graph_objects as go

USER_ID = 'user1'

def status_integralizacao(request):
    start_total = time.time()

    # Bloco 1: Leitura dos dados
    start = time.time()
    
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')
    df_alunos = pd.read_csv(alunos_path)
    df_historico = pd.read_csv(historico_path)
    print(f"Tempo leitura CSVs: {time.time() - start:.3f}s")

    # --- Filtros ---
    if not request.GET:
        return redirect(f"{reverse('status_integralizacao')}?ativos=ativos")
    
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
    # Exclui períodos "Curso de Férias" da matriz principal
    periodos_unicos = df_historico[df_historico['PERIODO'] != 'Curso de Férias'][['ANO', 'PERIODO']].drop_duplicates().reset_index(drop=True)
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
        ('Períodos Excepcionais', 6, '#ffe599'),
        ('Atividades Calendário Emergencial', 2, '#ffd966'),
        ('Trancamentos Totais (regulares)', 4, '#b7b7b7'),
        ('Trancamentos Totais (especiais)', 6, '#cccccc'),
    ]

    status_aprovados = {
        'APV - Aprovado': '#006400',
        'APV- Aprovado': '#006400',
        'APV - Aprovado sem nota': '#32CD32',
        'ADI - Aproveitamento': '#7CFC00',
        'ADI - Aproveitamento de créditos da disciplina': '#ADFF2F',
        'ADI - Dispensa com nota': '#228B22',
        'DIS - Dispensa sem nota': '#32CD32',
    }
    status_reprovados = {
        'REP - Reprovado por nota/conceito': '#8B0000',
        'REF - Reprovado por falta': '#CD5C5C',
        'ASC - Reprovado sem nota': '#FFA07A',
        'TRA - Trancamento de disciplina': '#8B0000',
    }
    status_matriculado = {'ASC - Matrícula'}
    cores_status = {**status_aprovados, **status_reprovados}

    # Bloco 4: Construção da matriz_geral

    matriculas_validas = set(alunos_dict[idx]['MATR ALUNO'] for idx in alunos_dict)
    periodos_validos = set((periodos_dict[idx]['ANO'], periodos_dict[idx]['PERIODO']) for idx in periodos_dict)

    matriz_geral = {}

    total_iteracoes_estrutura = 0
    total_adicoes_matr = 0
    total_adicoes_periodo = 0

    start = time.time()
    curso_ferias_dict = {}  # {matr: [disciplinas]}
    for mt, an, pr in zip(df_historico['MATR ALUNO'], df_historico['ANO'], df_historico['PERIODO']):
        total_iteracoes_estrutura += 1
        matr = mt
        periodo = (an, pr)
        if matr not in matriculas_validas:
            continue
        if pr == 'Curso de Férias':
            # Armazena para tooltip do próximo período regular
            if matr not in curso_ferias_dict:
                curso_ferias_dict[matr] = []
            curso_ferias_dict[matr].append({
                'ANO': an,
                'PERIODO': pr,
                'INDEX': total_iteracoes_estrutura
            })
            continue
        if periodo not in periodos_validos:
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

    # Para cada matrícula, obter lista de períodos regulares ordenados
    periodos_regulares_por_matr = {}
    for matr in matriz_geral:
        periodos_regulares_por_matr[matr] = sorted(matriz_geral[matr].keys(), key=lambda x: (int(x[0]), 1 if '1' in x[1] else 2))

    for i in range(len(df_historico)):
        total_iteracoes_preenchimento += 1
        matr = matr_aluno[i]
        an = anos[i]
        pr = periodos[i]
        periodo = (an, pr)
        nome = nomes_pessoa[i]
        status = descr_situacao[i]
        nome_disc = nome_ativ_curric[i]
        cod_disc = cod_ativ_curric[i]
        nota = nota_ativ_curric[i]
        if matr not in matriculas_validas or pr == 'Curso de Férias' or periodo not in periodos_validos:
            continue
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
                'nome': nome_disc,
                'status': status,
                'codigo': cod_disc,
                'nota': nota if pd.notna(nota) else 'N/A',
                'cor': status_aprovados[status]
            })
        elif status in status_reprovados:
            celula['reprovacoes'].append({
                'nome': nome_disc,
                'status': status,
                'codigo': cod_disc,
                'nota': nota if pd.notna(nota) else 'N/A',
                'cor': status_reprovados[status]
            })
        else:
            celula['outros'].append({
                'nome': nome_disc,
                'status': status,
                'codigo': cod_disc,
                'nota': nota if pd.notna(nota) else 'N/A'
            })
    for matr, ferias_list in curso_ferias_dict.items():
        periodos_ord = periodos_regulares_por_matr.get(matr, [])
        for ferias in ferias_list:
            ano_ferias = ferias['ANO']
            idx = None
            for i, p in enumerate(periodos_ord):
                if int(p[0]) > int(ano_ferias):
                    idx = i
                    break
            if idx is None and periodos_ord:
                idx = len(periodos_ord) - 1  
            if idx is not None:
                periodo_dest = periodos_ord[idx]
                celula = matriz_geral[matr][periodo_dest]
                if 'outros' not in celula:
                    celula['outros'] = []
                celula['outros'].append({
                    'nome': '(Curso de Férias)',
                    'status': 'Disciplina cursada em Curso de Férias',
                    'codigo': '',
                    'nota': '',
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

    # Definição dos períodos excepcionais
    periodo_excepcional_inicio = (2020, '1')
    periodo_excepcional_fim = (2022, '2')
    def periodo_tuple_to_int(ano, periodo):
        return int(ano) * 10 + int(str(periodo)[0])
    periodo_excepcional_inicio_int = periodo_tuple_to_int(*periodo_excepcional_inicio)
    periodo_excepcional_fim_int = periodo_tuple_to_int(*periodo_excepcional_fim)

    n_excepcionais = [b[1] for b in blocos if b[0] == 'Períodos Excepcionais'][0]
    idx_excepcionais = sum([b[1] for b in blocos if blocos.index(b) < [i for i, bl in enumerate(blocos) if bl[0] == 'Períodos Excepcionais'][0]])
    n_situacao_irregular = [b[1] for b in blocos if b[0] == 'Situação Irregular'][0]
    idx_situacao_irregular = sum([b[1] for b in blocos if blocos.index(b) < [i for i, bl in enumerate(blocos) if bl[0] == 'Situação Irregular'][0]])
    last_situacao_irregular_col = idx_situacao_irregular + n_situacao_irregular - 1

    for matr in matriculas:
        periodos_ordenados = sorted(
            matriz_geral[matr].keys(),
            key=lambda x: (int(x[0]), 1 if '1' in x[1] else 2)
        )
        linha = [''] * n_periodos
        linha_tooltip = [''] * n_periodos
        normais_idx = 0
        excepcionais_idx = idx_excepcionais
        regulares_tranc_idx = sum([b[1] for b in blocos if blocos.index(b) < [i for i, bl in enumerate(blocos) if bl[0] == 'Trancamentos Totais (regulares)'][0]])
        especiais_tranc_idx = sum([b[1] for b in blocos if blocos.index(b) < [i for i, bl in enumerate(blocos) if bl[0] == 'Trancamentos Totais (especiais)'][0]])
        regulares_tranc_count = 0
        especiais_tranc_count = 0
        excedentes = []
        excedentes_tooltip = []
        for periodo in periodos_ordenados:
            ano, per = periodo
            periodo_int = periodo_tuple_to_int(ano, per)
            celula = matriz_geral[matr][periodo]
            todas_disciplinas = (
                celula.get('aprovacoes', []) +
                celula.get('reprovacoes', []) +
                celula.get('outros', [])
            )
            tooltip = "Nenhuma disciplina cursada"
            if todas_disciplinas:
                disciplinas_tooltip = [
                    f"{disc['nome']}<br>    Nota: {disc.get('nota', '')}<br>    Situação: {disc['status']}"
                    for disc in todas_disciplinas
                ]
                tooltip = "<br>".join(disciplinas_tooltip)
            # Trancamento total (regular)
            nomes_ativ = [disc['nome'] for disc in todas_disciplinas]
            if "Trancamento Total" in nomes_ativ:
                if regulares_tranc_count < [b[1] for b in blocos if b[0] == 'Trancamentos Totais (regulares)'][0]:
                    linha[regulares_tranc_idx + regulares_tranc_count] = formatar_periodo(ano, per)
                    linha_tooltip[regulares_tranc_idx + regulares_tranc_count] = tooltip
                    regulares_tranc_count += 1
                else:
                    excedentes.append(formatar_periodo(ano, per))
                    excedentes_tooltip.append(tooltip)
                continue
            # Trancamento total (especial)
            if "Trancamento Total PERÍODO ESPECIAL" in nomes_ativ:
                if especiais_tranc_count < [b[1] for b in blocos if b[0] == 'Trancamentos Totais (especiais)'][0]:
                    linha[especiais_tranc_idx + especiais_tranc_count] = formatar_periodo(ano, per)
                    linha_tooltip[especiais_tranc_idx + especiais_tranc_count] = tooltip
                    especiais_tranc_count += 1
                else:
                    excedentes.append(formatar_periodo(ano, per))
                    excedentes_tooltip.append(tooltip)
                continue
            # Período excepcional
            if periodo_excepcional_inicio_int <= periodo_int <= periodo_excepcional_fim_int:
                if excepcionais_idx < idx_excepcionais + n_excepcionais:
                    linha[excepcionais_idx] = formatar_periodo(ano, per)
                    linha_tooltip[excepcionais_idx] = tooltip
                    excepcionais_idx += 1
                else:
                    excedentes.append(formatar_periodo(ano, per))
                    excedentes_tooltip.append(tooltip)
            # Período normal
            else:
                if normais_idx < idx_excepcionais:
                    linha[normais_idx] = formatar_periodo(ano, per)
                    linha_tooltip[normais_idx] = tooltip
                    normais_idx += 1
                elif normais_idx >= idx_excepcionais + n_excepcionais and normais_idx < n_periodos:
                    linha[normais_idx] = formatar_periodo(ano, per)
                    linha_tooltip[normais_idx] = tooltip
                    normais_idx += 1
                else:
                    excedentes.append(formatar_periodo(ano, per))
                    excedentes_tooltip.append(tooltip)
        if excedentes:
            linha[last_situacao_irregular_col] = '+'
            linha_tooltip[last_situacao_irregular_col] = f"Períodos posteriores: {', '.join(excedentes)}<br>" + '<br><br>'.join(excedentes_tooltip)
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
        textfont=dict(size=15, color='black'),
    )

    fig.update_layout(
        font=dict(size=18),
        xaxis=dict(
            tickmode='array',
            tickvals=list(range(n_periodos)),
            ticktext=[f'{colunas[i]}' for i in range(n_periodos)],
            tickangle=20,
            side='top',
            tickfont=dict(size=18),
            fixedrange=True
        ),
        yaxis=dict(
            automargin=True,
            tickfont=dict(size=16),
            range=[0, 10], 
        ),
        autosize=False,
        width=2200,
        height=850,
        margin=dict(l=10, r=10, t=60, b=10),
        dragmode="pan"
    )

    print(f"Tempo gráfico: {time.time() - start:.3f}s")

    print(f"Tempo total: {time.time() - start_total:.3f}s")

    plot_div = fig.to_html(full_html=False)
    filtros_options = [
        {'name': 'ativos', 'label': 'Alunos ativos', 'selected': filtro_ativos == 'ativos'},
    ]
    return render(request, 'status_integralizacao.html', {
        'plot_div': plot_div,
        'filtros_options': filtros_options,
        'periodos_options': periodos_options,
    })

def desempenho_aluno_periodo(request):
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')

    df_historico = pd.read_csv(historico_path)
    df_alunos = pd.read_csv(alunos_path)

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
    if dados_aluno.empty:
        alunos_options = [
            {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
            for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'desempenho_aluno_periodo.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
            'mensagem': mensagem,
        })

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
    if not periodos:
        alunos_options = [
            {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
            for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'desempenho_aluno_periodo.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
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
    status_reprovados = {
        'REP - Reprovado por nota/conceito': '#8B0000',
        'REF - Reprovado por falta': '#CD5C5C',
        'ASC - Reprovado sem nota': '#FFA07A',
        'TRA - Trancamento de disciplina': '#8B0000',
    }
    cores_status = {**status_aprovados, **status_reprovados}

    carga_aprovada_acumulada = (
        dados_aluno[dados_aluno['STATUS'].isin(status_aprovados.keys())]
        .groupby('ANO_PERIODO')['CARGA']
        .sum()
        .reindex(periodos, fill_value=0)
        .cumsum()
        .shift(fill_value=0)
    )

    barras = []
    for status, cor in status_reprovados.items():
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
            base=(carga_aprovada_acumulada - y).tolist(),
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)

    base_aprovada = carga_aprovada_acumulada.copy()
    for status, cor in status_aprovados.items():
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
            base=base_aprovada.tolist(),
            name=status,
            marker_color=cor,
            hoverinfo='text',
            hovertext=hover
        )
        barras.append(barra)
        base_aprovada += y

    if not barras:
        alunos_options = [
            {'id': str(matr_aluno), 'label': f"{matr_aluno} - {nome_pessoa}"}
            for matr_aluno, nome_pessoa in df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().values
        ]
        mensagem = "Não há dados disponíveis para o aluno selecionado."
        return render(request, 'desempenho_aluno_periodo.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
            'mensagem': mensagem,
        })

    carga_referencia = 3240
    linha_referencia = go.Scatter(
        x=periodos,
        y=[carga_referencia] * len(periodos),
        mode='lines',
        name='C.H. Total',
        line=dict(color='rgba(100,100,100,0.3)')
    )
    barras.append(linha_referencia)

    fig = go.Figure(barras)
    fig.update_layout(
        font=dict(size=18),
        barmode='stack',
        xaxis_title='Ano - Período',
        yaxis_title='Carga Horária',
        xaxis=dict(tickfont=dict(size=16)),
        yaxis=dict(tickfont=dict(size=16)),
        height=800,
        width=1800
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
    if not request.GET:
        return redirect(f"{reverse('heatmap_desempenho')}?curriculos=20232&tipo_disciplina=obrigatoria")

    USER_ID = 'user1'
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')

    df_alunos = pd.read_csv(alunos_path)
    df_historico = pd.read_csv(historico_path)

    df_disciplinas_20232 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20232.csv'))
    df_disciplinas_20052 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20052.csv'))
    df_disciplinas_20002 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20002.csv'))
    df_disciplinas_20081 = pd.read_csv(os.path.join(CURRICULOS_DIR, 'curriculo-20081.csv'))

    # --- Filtros ---
    filtro_ativos = request.GET.get('ativos', 'todos')
    filtro_curriculos = request.GET.getlist('curriculos')
    filtro_tipo_disciplina = request.GET.get('tipo_disciplina', 'obrigatoria')
    curriculos_map = {
        '20232': df_disciplinas_20232,
        '20052': df_disciplinas_20052,
        '20002': df_disciplinas_20002,
        '20081': df_disciplinas_20081,
    }
    curriculos_options = [
        {'value': '20232', 'label': 'Currículo 2023/2', 'selected': '20232' in filtro_curriculos},
        {'value': '20052', 'label': 'Currículo 2005/2', 'selected': '20052' in filtro_curriculos},
        {'value': '20002', 'label': 'Currículo 2000/2', 'selected': '20002' in filtro_curriculos},
        {'value': '20081', 'label': 'Currículo 2008/1', 'selected': '20081' in filtro_curriculos},
    ]
    tipo_disciplina_options = [
        {'value': 'todas', 'label': 'Todas', 'selected': filtro_tipo_disciplina == 'todas'},
        {'value': 'obrigatoria', 'label': 'Obrigatórias', 'selected': filtro_tipo_disciplina == 'obrigatoria'},
        {'value': 'optativa', 'label': 'Optativas', 'selected': filtro_tipo_disciplina == 'optativa'},
    ]

    # Filtrar alunos ativos
    if filtro_ativos == 'ativos':
        alunos_ativos = df_alunos[df_alunos['FORMA EVASAO'] == 'Sem evasão']['ID PESSOA'].unique()
        df_historico = df_historico[df_historico['ID PESSOA'].isin(alunos_ativos)]
        df_alunos = df_alunos[df_alunos['ID PESSOA'].isin(alunos_ativos)]

    # Filtrar currículos e tipo de disciplina
    def filtrar_disciplinas(df, curriculo, tipo):
        if tipo == 'todas':
            if curriculo == '20002':
                return df['COD DISCIPLINA']
            else:
                return df['COD DISCIPLINA']
        elif tipo == 'obrigatoria':
            if curriculo == '20002':
                return df[df['DESCR ESTRUTURA'] == 'Disciplinas obrigatórias']['COD DISCIPLINA']
            else:
                return df[df['TIPO DISCIPLINA'] == 'Obrigatória']['COD DISCIPLINA']
        elif tipo == 'optativa':
            if curriculo == '20002':
                return df[df['DESCR ESTRUTURA'] == 'Disciplinas optativas']['COD DISCIPLINA']
            else:
                return df[df['TIPO DISCIPLINA'] == 'Optativa']['COD DISCIPLINA']
        else:
            return df['COD DISCIPLINA']

    def ordenar_disciplinas_por_periodo(df, codigos):
        # Tenta ordenar pelo PERIODO IDEAL, se existir
        if 'PERIODO IDEAL' in df.columns:
            # Filtra apenas as disciplinas presentes em codigos
            df_filtrado = df[df['COD DISCIPLINA'].isin(codigos)].copy()
            df_filtrado['PERIODO IDEAL'] = pd.to_numeric(df_filtrado['PERIODO IDEAL'], errors='coerce').fillna(9999)
            df_filtrado = df_filtrado.sort_values(['PERIODO IDEAL', 'COD DISCIPLINA'])
            return df_filtrado['COD DISCIPLINA'].tolist()
        else:
            return sorted(list(codigos))

    if filtro_curriculos:
        disciplinas_set = set()
        disciplinas_periodo = []
        for curr in filtro_curriculos:
            df = curriculos_map.get(curr)
            if df is not None:
                disciplinas = filtrar_disciplinas(df, curr, filtro_tipo_disciplina)
                disciplinas_set.update(disciplinas)
        df_ord = curriculos_map.get(filtro_curriculos[0], df_disciplinas_20232)
        disciplinas_list = ordenar_disciplinas_por_periodo(df_ord, disciplinas_set)
    else:
        disciplinas_set = set()
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20232, '20232', filtro_tipo_disciplina))
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20052, '20052', filtro_tipo_disciplina))
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20002, '20002', filtro_tipo_disciplina))
        disciplinas_set.update(filtrar_disciplinas(df_disciplinas_20081, '20081', filtro_tipo_disciplina))
        disciplinas_list = ordenar_disciplinas_por_periodo(df_disciplinas_20232, disciplinas_set)

    df_alunos['MATR ALUNO'] = df_alunos['MATR ALUNO'].astype(str)
    df_alunos = df_alunos.drop_duplicates(subset=['MATR ALUNO'])
    df_alunos = df_alunos.sort_values('MATR ALUNO').reset_index(drop=True)
    df_historico['MATR ALUNO'] = df_historico['MATR ALUNO'].astype(str)

    alunos_dict = dict((matricula, idx) for idx, matricula in enumerate(df_alunos['MATR ALUNO']))
    disciplinas_dict = dict((cod_disciplina, idx) for idx, cod_disciplina in enumerate(disciplinas_list))

    n_alunos = len(alunos_dict)
    n_disciplinas = len(disciplinas_dict)
    matriz_geral = [['' for _ in range(n_disciplinas)] for _ in range(n_alunos)]
    matriz_tooltips = [[{} for _ in range(n_disciplinas)] for _ in range(n_alunos)]

    for matricula, cod_disciplina, status in zip(df_historico['MATR ALUNO'], df_historico['COD ATIV CURRIC'], df_historico['DESCR SITUACAO']):
        idx_aluno = alunos_dict.get(str(matricula))
        idx_disc = disciplinas_dict.get(cod_disciplina)
        if idx_aluno is not None and idx_disc is not None:
            matriz_geral[idx_aluno][idx_disc] = status

    for matricula, nome_aluno, cod_disciplina, status, media_final, ano, periodo, nome, nome_disciplina in zip(
        df_historico['MATR ALUNO'],
        df_historico['NOME PESSOA'],
        df_historico['COD ATIV CURRIC'],
        df_historico['DESCR SITUACAO'],
        df_historico['MEDIA FINAL'],
        df_historico['ANO'],
        df_historico['PERIODO'],
        df_historico['NOME PESSOA'],
        df_historico['NOME ATIV CURRIC']
    ):
        idx_aluno = alunos_dict.get(str(matricula))
        idx_disc = disciplinas_dict.get(cod_disciplina)
        if (
            idx_aluno is not None and idx_disc is not None
            and 0 <= idx_aluno < n_alunos
            and 0 <= idx_disc < n_disciplinas
        ):
            matriz_geral[idx_aluno][idx_disc] = status
            if 'status_list' not in matriz_tooltips[idx_aluno][idx_disc]:
                matriz_tooltips[idx_aluno][idx_disc]['status_list'] = []
            matriz_tooltips[idx_aluno][idx_disc]['status_list'].append({
                'nome_disciplina': nome_disciplina,
                'status': status,
                'media_final': media_final,
                'ano_periodo': f"{ano}.{periodo}",
                'nome_aluno': nome_aluno
            })

    alunos_labels = [
        f"{matricula} - {df_alunos.loc[df_alunos['MATR ALUNO'] == matricula, 'NOME PESSOA'].values[0]}"
        if not df_alunos.loc[df_alunos['MATR ALUNO'] == matricula, 'NOME PESSOA'].empty else str(matricula)
        for matricula in df_alunos['MATR ALUNO']
    ]
    def get_nome_disciplina(cod):
        for df in [df_disciplinas_20232, df_disciplinas_20052, df_disciplinas_20002, df_disciplinas_20081]:
            nome = df.loc[df['COD DISCIPLINA'] == cod, 'NOME DISCIPLINA']
            if not nome.empty:
                nome_val = nome.values[0]
                if ' - ' in nome_val:
                    return nome_val.split(' - ', 1)[1].strip()
                return nome_val.strip()
        return str(cod)

    disciplinas_labels = [get_nome_disciplina(cod) for cod in disciplinas_list]

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

    def status_to_num(status):
        if status in aprovados:
            return 1
        if status in matriculado:
            return 0
        if status in reprovados:
            return -1
        return np.nan

    matriz_numerica = [
        [status_to_num(cell) for cell in row]
        for row in matriz_geral
    ]

    def tooltip_format(cell_tooltip):
        if not cell_tooltip or 'status_list' not in cell_tooltip:
            return ""
        status_list = cell_tooltip['status_list']
        if len(status_list) == 1:
            s = status_list[0]
            nome_aluno = s.get('nome_aluno', '')
            nome_disciplina = s.get('nome_disciplina', '')
            status = s.get('status', '')
            media = s.get('media_final', '')
            periodo = s.get('ano_periodo', '')
            nota_str = f"{media}" if pd.notna(media) else ""
            return (
                f"{nome_aluno}<br>"
                f"{nome_disciplina}<br>"
                f"  Status: {status}<br>"
                f"      {periodo}<br>"
                f"      {nota_str}<br>"
            )
        else:
            s0 = status_list[0]
            nome_aluno = s0.get('nome_aluno', '')
            nome_disciplina = s0.get('nome_disciplina', '')
            historico = []
            for s in sorted(status_list, key=lambda x: x.get('ano_periodo', ''), reverse=True):
                status = s.get('status', '')
                media = s.get('media_final', '')
                periodo = s.get('ano_periodo', '')
                nota_str = f"{media}" if pd.notna(media) else ""
                historico.append(f"{status} ({periodo}) {nota_str}")
            return (
                f"{nome_aluno}<br>"
                f"{nome_disciplina}<br>"
                f"Histórico: <br>" + "<br>".join(historico)
            )

    matriz_tooltips_str = [
        [tooltip_format(cell) for cell in row]
        for row in matriz_tooltips
    ]

    fig = go.Figure(data=go.Heatmap(
        z=matriz_numerica,
        x=disciplinas_labels,
        y=alunos_labels,
        text=matriz_tooltips_str,
        hoverinfo='text',
        colorscale=[
            [0.0, 'red'],
            [0.5, 'yellow'],
            [1.0, 'green']
        ],
        showscale=False
    ))

    fig.update_layout(
        font=dict(size=18),
        xaxis=dict(
            tickangle=330,
            tickfont=dict(size=16),
            fixedrange=True  
        ),
        yaxis=dict(
            tickfont=dict(size=16),
        ),
        autosize=True,
        hovermode="x unified",
        margin=dict(l=10, r=10, t=10, b=10),
        height=880,
        width=2200,
        dragmode="pan"  
    )

    plot_div = fig.to_html(full_html=False)
    filtros_options = [
        {'name': 'ativos', 'label': 'Alunos ativos', 'selected': filtro_ativos == 'ativos'},
    ]
    return render(request, 'heatmap_desempenho.html', {
        'plot_div': plot_div,
        'curriculos_options': curriculos_options,
        'periodos_options': [],
        'filtros_options': filtros_options,
        'curriculos_selecionados': filtro_curriculos,
        'tipo_disciplina_options': tipo_disciplina_options,
        'tipo_disciplina_selecionado': filtro_tipo_disciplina,
    })

def home(request):
    return render(request, 'home.html')

# Upload de arquivos

USER_ID = 'user1'
USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)

CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')

def ensure_user_dirs():
    os.makedirs(USER_DIR, exist_ok=True)
    os.makedirs(CURRICULOS_DIR, exist_ok=True)

def checar_arquivos_necessarios(request):
    """
    Recebe via GET o parâmetro 'visualizacao' e retorna JSON com arquivos faltantes.
    """
    visualizacao = request.GET.get('visualizacao')
    USER_ID = 'user1' 
    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    CURRICULOS_DIR = os.path.join(settings.MEDIA_ROOT, 'curriculos_bsi')
    faltando = []
    if visualizacao == 'desempenho_aluno_periodo':
        if not os.path.exists(os.path.join(USER_DIR, 'alunosPorCurso.csv')):
            faltando.append('alunosPorCurso.csv')
        if not os.path.exists(os.path.join(USER_DIR, 'historicoEscolar.csv')):
            faltando.append('historicoEscolar.csv')
    elif visualizacao == 'status_integralizacao':
        if not os.path.exists(os.path.join(USER_DIR, 'alunosPorCurso.csv')):
            faltando.append('alunosPorCurso.csv')
        if not os.path.exists(os.path.join(USER_DIR, 'historicoEscolar.csv')):
            faltando.append('historicoEscolar.csv')
    elif visualizacao == 'heatmap_desempenho':
        if not os.path.exists(os.path.join(USER_DIR, 'alunosPorCurso.csv')):
            faltando.append('alunosPorCurso.csv')
        if not os.path.exists(os.path.join(USER_DIR, 'historicoEscolar.csv')):
            faltando.append('historicoEscolar.csv')
        curriculos = [
            'curriculo-20002.csv',
            'curriculo-20052.csv',
            'curriculo-20081.csv',
            'curriculo-20232.csv',
        ]
        curriculos_faltando = [c for c in curriculos if not os.path.exists(os.path.join(CURRICULOS_DIR, c))]
        faltando.extend(curriculos_faltando)
    return JsonResponse({'faltando': faltando})

def gerenciar_arquivos(request):
    ensure_user_dirs()
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')
    curriculos = []
    curriculos_padrao = [
        'curriculo-20002.csv',
        'curriculo-20052.csv',
        'curriculo-20081.csv',
        'curriculo-20232.csv',
    ]
    if os.path.exists(CURRICULOS_DIR):
        curriculos = [c for c in curriculos_padrao if os.path.exists(os.path.join(CURRICULOS_DIR, c))]
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        if tipo in ['alunos', 'historico']:
            f = request.FILES.get('arquivo')
            if f:
                filename = 'alunosPorCurso.csv' if tipo == 'alunos' else 'historicoEscolar.csv'
                with open(os.path.join(USER_DIR, filename), 'wb+') as dest:
                    for chunk in f.chunks():
                        dest.write(chunk)
                messages.success(request, f'Arquivo {filename} enviado com sucesso!')
                return redirect('gerenciar_arquivos')
        elif tipo == 'curriculo':
            f = request.FILES.get('arquivo')
            if f:
                curriculos_existentes = [c for c in curriculos_padrao if os.path.exists(os.path.join(CURRICULOS_DIR, c))]
                if len(curriculos_existentes) >= 4:
                    messages.error(request, 'Limite de 4 currículos atingido. Remova um currículo antes de enviar outro.')
                    return redirect('gerenciar_arquivos')
                for curriculo_nome in curriculos_padrao:
                    curriculo_path = os.path.join(CURRICULOS_DIR, curriculo_nome)
                    if not os.path.exists(curriculo_path):
                        with open(curriculo_path, 'wb+') as dest:
                            for chunk in f.chunks():
                                dest.write(chunk)
                        messages.success(request, f'Currículo enviado como {curriculo_nome}!')
                        break
                return redirect('gerenciar_arquivos')
        elif 'remover' in request.POST:
            arquivo = request.POST.get('remover')
            if arquivo == 'alunosPorCurso.csv':
                os.remove(alunos_path)
            elif arquivo == 'historicoEscolar.csv':
                os.remove(historico_path)
            elif arquivo in curriculos_padrao:
                os.remove(os.path.join(CURRICULOS_DIR, arquivo))
            messages.success(request, f'Arquivo removido com sucesso!')
            return redirect('gerenciar_arquivos')
    context = {
        'alunos': os.path.exists(alunos_path),
        'historico': os.path.exists(historico_path),
        'curriculos': [c for c in curriculos_padrao if os.path.exists(os.path.join(CURRICULOS_DIR, c))],
    }
    return render(request, 'gerenciar_arquivos.html', context)