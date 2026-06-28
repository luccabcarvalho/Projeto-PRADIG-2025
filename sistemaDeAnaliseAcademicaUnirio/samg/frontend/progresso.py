import pandas as pd
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from samg.frontend.common import (
    build_alunos_options,
    extract_name,
    extract_sigla,
    filtrar_disciplinas,
    is_tipo_obrigatoria,
    load_base_data,
    load_curriculo,
    resolve_selected_id,
    status_info,
    version_key,
)


DEFAULT_CURRICULO_VERSION = '20232'


@login_required
def progresso(request):
    apenas_obrigatorias = request.GET.get('apenas_obrigatorias') == '1'
    apenas_pendentes = request.GET.get('apenas_pendentes') == '1'
    df_alunos, df_historico, erro_base = load_base_data()
    if erro_base:
        return render(request, 'progresso.html', {
            'message': erro_base,
            'curriculoGrade': [],
            'filteredCurriculoGrade': [],
            'curriculoStats': {'total': 0, 'concluidas': 0, 'pendentes': 0, 'percentual': 0},
            'alunos_options': [],
            'selected_id': '',
            'curriculoVersion': '',
            'aluno_nome': '',
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    alunos_options = build_alunos_options(df_alunos)

    matriculas_validas = {item['id'] for item in alunos_options}
    matricula_selecionada = resolve_selected_id(request, matriculas_validas)

    if not matricula_selecionada:
        return render(request, 'progresso.html', {
            'message': 'Não há alunos disponíveis para exibir.',
            'curriculoGrade': [],
            'filteredCurriculoGrade': [],
            'curriculoStats': {'total': 0, 'concluidas': 0, 'pendentes': 0, 'percentual': 0},
            'alunos_options': [],
            'selected_id': '',
            'curriculoVersion': '',
            'aluno_nome': '',
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    aluno_base = df_alunos[df_alunos['MATR ALUNO'] == matricula_selecionada].copy()
    if aluno_base.empty:
        return render(request, 'progresso.html', {
            'message': 'Não foi possível localizar o aluno selecionado.',
            'curriculoGrade': [],
            'filteredCurriculoGrade': [],
            'curriculoStats': {'total': 0, 'concluidas': 0, 'pendentes': 0, 'percentual': 0},
            'alunos_options': alunos_options,
            'selected_id': matricula_selecionada,
            'curriculoVersion': '',
            'aluno_nome': '',
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    aluno_base = aluno_base.iloc[0]
    aluno_nome = str(aluno_base.get('NOME PESSOA', '')).strip()
    versao_curriculo = version_key(aluno_base.get('NUM VERSAO'))

    df_curriculo = load_curriculo(versao_curriculo)
    if df_curriculo is None:
        return render(request, 'progresso.html', {
            'message': f'Não foi possível localizar o currículo da versão {versao_curriculo}.',
            'curriculoGrade': [],
            'filteredCurriculoGrade': [],
            'curriculoStats': {'total': 0, 'concluidas': 0, 'pendentes': 0, 'percentual': 0},
            'alunos_options': alunos_options,
            'selected_id': matricula_selecionada,
            'curriculoVersion': aluno_base.get('NUM VERSAO', versao_curriculo),
            'aluno_nome': aluno_nome,
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    if 'COD CURSO' in df_curriculo.columns and 'COD CURSO' in aluno_base.index:
        cod_curso = str(aluno_base.get('COD CURSO', '')).strip()
        if cod_curso and cod_curso != 'nan':
            df_curriculo = df_curriculo[df_curriculo['COD CURSO'].astype(str).str.strip() == cod_curso]

    historico_aluno = df_historico[df_historico['MATR ALUNO'] == matricula_selecionada].copy()
    if historico_aluno.empty:
        return render(request, 'progresso.html', {
            'message': 'Não há histórico disponível para o aluno selecionado.',
            'curriculoGrade': [],
            'filteredCurriculoGrade': [],
            'curriculoStats': {'total': 0, 'concluidas': 0, 'pendentes': 0, 'percentual': 0},
            'alunos_options': alunos_options,
            'selected_id': matricula_selecionada,
            'curriculoVersion': aluno_base.get('NUM VERSAO', versao_curriculo),
            'aluno_nome': aluno_nome,
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    historico_map = (
        historico_aluno.sort_values(
            by=['COD ATIV CURRIC', 'ANO_NUM', 'PERIODO_NUM', 'SITUACAO_ITEM_NUM'],
            ascending=[True, True, True, True],
        )
        .drop_duplicates(subset=['COD ATIV CURRIC'], keep='last')
        .set_index('COD ATIV CURRIC')
        .to_dict('index')
    )

    curriculo_grade = []
    disciplinas_concluidas = []

    for periodo_ideal, df_periodo in df_curriculo.sort_values(['PERIODO IDEAL_NUM', 'COD DISCIPLINA']).groupby('PERIODO IDEAL_NUM'):
        disciplinas_periodo = []
        for _, row in df_periodo.drop_duplicates(subset=['COD DISCIPLINA'], keep='first').iterrows():
            codigo = str(row.get('COD DISCIPLINA', '')).strip()
            nome_curto = extract_name(row.get('NOME DISCIPLINA', '')) or codigo
            sigla = extract_sigla(codigo)
            historico = historico_map.get(codigo)
            status_raw = '' if not historico else str(historico.get('DESCR SITUACAO', '')).strip()
            status_label, status_badge, concluida, cursando, reprovada = status_info(status_raw)
            periodo_real = ''
            media_final = ''
            if historico:
                ano = historico.get('ANO_NUM', '')
                periodo_txt = historico.get('PERIODO', '')
                periodo_real = f"{ano} - {periodo_txt}" if ano else str(periodo_txt)
                media_final = historico.get('MEDIA FINAL', '')

            disciplina = {
                'codigo': codigo,
                'sigla': sigla,
                'nome': nome_curto,
                'obrigatoria': is_tipo_obrigatoria(row.get('TIPO DISCIPLINA', '')),
                'status_raw': status_raw,
                'status_label': status_label,
                'status_badge': status_badge,
                'concluida': concluida,
                'cursando': cursando,
                'reprovada': reprovada,
                'periodo_real': periodo_real,
                'media_final': media_final,
            }
            disciplinas_periodo.append(disciplina)
            if concluida:
                disciplinas_concluidas.append(disciplina)

        concluidas = sum(1 for disciplina in disciplinas_periodo if disciplina['concluida'])
        pendentes = len(disciplinas_periodo) - concluidas
        percentual = round((concluidas / len(disciplinas_periodo)) * 100, 1) if disciplinas_periodo else 0

        curriculo_grade.append({
            'periodo': int(periodo_ideal) if pd.notna(periodo_ideal) else periodo_ideal,
            'periodo_label': f"{int(periodo_ideal)}º período" if pd.notna(periodo_ideal) else 'Período não definido',
            'total': len(disciplinas_periodo),
            'concluidas': concluidas,
            'pendentes': pendentes,
            'percentual': percentual,
            'disciplinas': disciplinas_periodo,
            'disciplinas_concluidas': [d for d in disciplinas_periodo if d['concluida']],
            'disciplinas_pendentes': [d for d in disciplinas_periodo if not d['concluida']],
        })

    filtered_curriculo_grade = []
    for periodo in curriculo_grade:
        disciplinas_filtradas = filtrar_disciplinas(
            periodo['disciplinas'],
            apenas_obrigatorias=apenas_obrigatorias,
            apenas_pendentes=apenas_pendentes,
        )
        if not disciplinas_filtradas:
            continue

        concluidas_filtradas = [d for d in disciplinas_filtradas if d['concluida']]
        pendentes_filtradas = [d for d in disciplinas_filtradas if not d['concluida']]
        total_filtrado = len(disciplinas_filtradas)
        total_concluidas_filtrado = len(concluidas_filtradas)
        percentual_filtrado = round((total_concluidas_filtrado / total_filtrado) * 100, 1) if total_filtrado else 0

        filtered_curriculo_grade.append({
            'periodo': periodo['periodo'],
            'periodo_label': periodo['periodo_label'],
            'total': total_filtrado,
            'concluidas': total_concluidas_filtrado,
            'pendentes': len(pendentes_filtradas),
            'percentual': percentual_filtrado,
            'disciplinas': disciplinas_filtradas,
            'disciplinas_concluidas': concluidas_filtradas,
            'disciplinas_pendentes': pendentes_filtradas,
        })

    total_curriculo = sum(periodo['total'] for periodo in filtered_curriculo_grade)
    total_concluidas = sum(periodo['concluidas'] for periodo in filtered_curriculo_grade)
    total_pendentes = total_curriculo - total_concluidas
    percentual_geral = round((total_concluidas / total_curriculo) * 100, 1) if total_curriculo else 0

    return render(request, 'progresso.html', {
        'message': '',
        'alunos_options': alunos_options,
        'selected_id': matricula_selecionada,
        'aluno_nome': aluno_nome,
        'curriculoVersion': aluno_base.get('NUM VERSAO', versao_curriculo),
        'curriculoGrade': curriculo_grade,
        'filteredCurriculoGrade': filtered_curriculo_grade,
        'disciplinas_concluidas': disciplinas_concluidas,
        'curriculoStats': {
            'total': total_curriculo,
            'concluidas': total_concluidas,
            'pendentes': total_pendentes,
            'percentual': percentual_geral,
        },
        'apenas_obrigatorias': apenas_obrigatorias,
        'apenas_pendentes': apenas_pendentes,
    })