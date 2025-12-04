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

def prazos_de_integralizacao(request):

    USER_DIR = os.path.join(settings.MEDIA_ROOT, USER_ID)
    alunos_path = os.path.join(USER_DIR, 'alunosPorCurso.csv')
    historico_path = os.path.join(USER_DIR, 'historicoEscolar.csv')
    df_alunos = pd.read_csv(alunos_path)
    df_historico = pd.read_csv(historico_path)

    # --- Filtros ---
    if not request.GET:
        return redirect(f"{reverse('prazos_de_integralizacao')}?ativos=ativos")
    
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

    df_alunos = df_alunos.sort_values('PERIODO INGRESSO')
    alunos = df_historico['MATR ALUNO'].unique().tolist()

    alunos_dict = {}
    for idx, row in enumerate(df_historico[['MATR ALUNO', 'NOME PESSOA']].drop_duplicates().itertuples(index=False)):
        alunos_dict[idx] = {
            'MATR ALUNO': row[0],
            'NOME PESSOA': row[1]
        }

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

    matriculas_validas = set(alunos_dict[idx]['MATR ALUNO'] for idx in alunos_dict)
    periodos_validos = set((periodos_dict[idx]['ANO'], periodos_dict[idx]['PERIODO']) for idx in periodos_dict)

    matriz_geral = {}

    total_iteracoes_estrutura = 0
    total_adicoes_matr = 0
    total_adicoes_periodo = 0

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

    plot_div = fig.to_html(full_html=False)
    filtros_options = [
        {'name': 'ativos', 'label': 'Alunos ativos', 'selected': filtro_ativos == 'ativos'},
    ]
    return render(request, 'prazos_de_integralizacao.html', {
        'plot_div': plot_div,
        'filtros_options': filtros_options,
        'periodos_options': periodos_options,
    })