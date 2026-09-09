import pandas as pd
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from samg.frontend.common import (
    geraListaAlunos,
    extract_name,
    extract_sigla,
    filtrar_disciplinas,
    is_tipo_obrigatoria,
    normalize_text,
    carregaBD,
    carregaCurriculo,
    getMatriculaAluno,
    status_info,
    versaoCurriculo,
)


DEFAULT_CURRICULO_VERSION = '20232'


def normaliza_media_final(value):
    if pd.isna(value):
        return ''
    text = str(value).strip()
    if text.lower() in {'nan', 'none', 'null'}:
        return ''
    return text


def exibe_media_final(value):
    text = normaliza_media_final(value)
    return text if text else 'Aprovado sem nota'


def normaliza_carga_horaria(value):
    if pd.isna(value):
        return None
    text = str(value).strip().replace(',', '.')
    try:
        number = float(text)
    except ValueError:
        return None
    if number.is_integer():
        return int(number)
    return round(number, 1)


def exibe_carga_horaria(value):
    carga = normaliza_carga_horaria(value)
    return '' if carga is None else f'{carga}h'


@login_required
def progresso(request):
    apenas_pendentes = request.GET.get('apenas_pendentes') == '1'
    mostrar_eletivas = request.GET.get('mostrar_eletivas') == '1'
    mostrar_optativas = request.GET.get('mostrar_optativas') == '1'
    mostrar_demais = request.GET.get('mostrar_demais') == '1'
    df_alunos, df_historico, erro_base = carregaBD()
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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
        })

    alunos_options = geraListaAlunos(df_alunos)

    matriculas_validas = {item['id'] for item in alunos_options}
    matricula_selecionada = getMatriculaAluno(request, matriculas_validas)

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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
        })

    aluno_base = aluno_base.iloc[0]
    aluno_nome = str(aluno_base.get('NOME PESSOA', '')).strip()
    historico_aluno = df_historico[df_historico['MATR ALUNO'] == matricula_selecionada].copy()
    versao_curriculo = ''
    if not historico_aluno.empty and 'NUM VERSAO' in historico_aluno.columns:
        versoes_historico = historico_aluno['NUM VERSAO'].astype(str).str.strip()
        versoes_historico = versoes_historico[versoes_historico.notna() & (versoes_historico != '') & (versoes_historico != 'nan')]
        if not versoes_historico.empty:
            versao_curriculo = versaoCurriculo(versoes_historico.mode().iat[0])
    if not versao_curriculo:
        versao_curriculo = versaoCurriculo(aluno_base.get('NUM VERSAO'))

    df_curriculo = carregaCurriculo(versao_curriculo)
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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
        })

    if 'COD CURSO' in df_curriculo.columns and 'COD CURSO' in aluno_base.index:
        cod_curso = str(aluno_base.get('COD CURSO', '')).strip()
        if cod_curso and cod_curso != 'nan':
            df_curriculo = df_curriculo[df_curriculo['COD CURSO'].astype(str).str.strip() == cod_curso]

    if 'TOTAL CH' in df_curriculo.columns:
        total_ch_curriculo = pd.to_numeric(df_curriculo['TOTAL CH'], errors='coerce').dropna()
        carga_total_curriculo = float(total_ch_curriculo.iloc[0]) if not total_ch_curriculo.empty else 0
    else:
        carga_total_curriculo = 0
    if not carga_total_curriculo and 'CH TOTAL' in df_curriculo.columns:
        carga_total_curriculo = pd.to_numeric(df_curriculo['CH TOTAL'], errors='coerce').fillna(0).sum()

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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
        })

    historico_map = (
        historico_aluno.sort_values(
            by=['COD ATIV CURRIC', 'ANO_NUM', 'PERIODO_NUM', 'SITUACAO_ITEM_NUM'],
            ascending=[True, True, True, False],
        )
        .drop_duplicates(subset=['COD ATIV CURRIC'], keep='last')
        .set_index('COD ATIV CURRIC')
        .to_dict('index')
    )

    historico_carga_total = pd.to_numeric(
        historico_aluno.drop_duplicates(subset=['COD ATIV CURRIC'], keep='last')['TOTAL CARGA HORARIA'],
        errors='coerce'
    ).fillna(0).sum()

    historico_aprovado = historico_aluno[
        historico_aluno['DESCR SITUACAO'].astype(str).str.strip() == 'APV- Aprovado'
    ].copy()
    historico_carga_cursada = pd.to_numeric(
        historico_aprovado.drop_duplicates(subset=['COD ATIV CURRIC'], keep='last')['TOTAL CARGA HORARIA'],
        errors='coerce'
    ).fillna(0).sum()

    curriculo_grade = []
    disciplinas_concluidas = []

    def obter_carga_horaria(row):
        if 'CH TOTAL' in row.index:
            carga = normaliza_carga_horaria(row.get('CH TOTAL'))
            if carga is not None:
                return carga
        return None

    for periodo_ideal, df_periodo in df_curriculo.sort_values(['PERIODO IDEAL_NUM', 'COD DISCIPLINA']).groupby('PERIODO IDEAL_NUM'):
        disciplinas_periodo = []
        for _, row in df_periodo.drop_duplicates(subset=['COD DISCIPLINA'], keep='first').iterrows():
            codigo = str(row.get('COD DISCIPLINA', '')).strip()
            nome_curto = extract_name(row.get('NOME DISCIPLINA', '')) or codigo
            sigla = extract_sigla(codigo)
            tipo_raw = str(row.get('TIPO DISCIPLINA', '')).strip()
            tipo_norm = normalize_text(tipo_raw)
            obrigatoria = tipo_norm == 'obrigatoria'
            eletiva = tipo_norm == 'eletiva'
            optativa = tipo_norm == 'optativa'
            demais = not (obrigatoria or eletiva or optativa)
            historico = historico_map.get(codigo)
            status_raw = '' if not historico else str(historico.get('DESCR SITUACAO', '')).strip()
            status_label, status_badge, concluida, cursando, reprovada = status_info(status_raw)
            periodo_real = ''
            media_final = ''
            carga_horaria = obter_carga_horaria(row)
            if historico:
                ano = historico.get('ANO_NUM', '')
                periodo_txt = historico.get('PERIODO', '')
                periodo_real = f"{ano} - {periodo_txt}" if ano else str(periodo_txt)
                media_final = exibe_media_final(historico.get('MEDIA FINAL', ''))

            disciplina = {
                'codigo': codigo,
                'sigla': sigla,
                'nome': nome_curto,
                'tipo_disciplina': tipo_raw,
                'obrigatoria': obrigatoria,
                'eletiva': eletiva,
                'optativa': optativa,
                'demais': demais,
                'status_raw': status_raw,
                'status_label': status_label,
                'status_badge': status_badge,
                'concluida': concluida,
                'cursando': cursando,
                'reprovada': reprovada,
                'periodo_real': periodo_real,
                'media_final': media_final,
                'carga_horaria': carga_horaria,
                'carga_horaria_label': exibe_carga_horaria(carga_horaria),
            }
            disciplinas_periodo.append(disciplina)
            if concluida:
                disciplinas_concluidas.append(disciplina)

        concluidas = int(sum(1 for disciplina in disciplinas_periodo if disciplina['concluida']))
        pendentes = int(len(disciplinas_periodo) - concluidas)
        percentual = round((concluidas / len(disciplinas_periodo)) * 100, 1) if disciplinas_periodo else 0
        carga_total = int(sum((d['carga_horaria'] or 0) for d in disciplinas_periodo))
        carga_cursada = int(sum((d['carga_horaria'] or 0) for d in disciplinas_periodo if d['status_raw'] == 'APV- Aprovado'))
        carga_concluida = int(sum((d['carga_horaria'] or 0) for d in disciplinas_periodo if d['concluida']))

        curriculo_grade.append({
            'periodo': int(periodo_ideal) if pd.notna(periodo_ideal) else periodo_ideal,
            'periodo_label': f"{int(periodo_ideal)}º período" if pd.notna(periodo_ideal) else 'Período não definido',
            'total': len(disciplinas_periodo),
            'concluidas': concluidas,
            'pendentes': pendentes,
            'percentual': percentual,
            'carga_horaria_total': carga_total,
            'carga_horaria_cursada': carga_cursada,
            'carga_horaria_concluida': carga_concluida,
            'carga_horaria_pendente': int(max(carga_total - carga_cursada, 0)),
            'disciplinas': disciplinas_periodo,
            'disciplinas_concluidas': [d for d in disciplinas_periodo if d['concluida']],
            'disciplinas_pendentes': [d for d in disciplinas_periodo if not d['concluida']],
        })

    filtered_curriculo_grade = []
    for periodo in curriculo_grade:
        disciplinas_filtradas = []
        for disciplina in periodo['disciplinas']:
            if disciplina.get('obrigatoria'):
                disciplinas_filtradas.append(disciplina)
            elif disciplina.get('eletiva') and mostrar_eletivas:
                disciplinas_filtradas.append(disciplina)
            elif disciplina.get('optativa') and mostrar_optativas:
                disciplinas_filtradas.append(disciplina)
            elif disciplina.get('demais') and mostrar_demais:
                disciplinas_filtradas.append(disciplina)

        disciplinas_filtradas = filtrar_disciplinas(
            disciplinas_filtradas,
            apenas_obrigatorias=False,
            apenas_pendentes=apenas_pendentes,
        )
        if not disciplinas_filtradas:
            continue

        concluidas_filtradas = [d for d in disciplinas_filtradas if d['concluida']]
        pendentes_filtradas = [d for d in disciplinas_filtradas if not d['concluida']]
        total_filtrado = len(disciplinas_filtradas)
        total_concluidas_filtrado = len(concluidas_filtradas)
        percentual_filtrado = round((total_concluidas_filtrado / total_filtrado) * 100, 1) if total_filtrado else 0
        carga_total_filtrada = int(sum((d['carga_horaria'] or 0) for d in disciplinas_filtradas))
        carga_cursada_filtrada = int(sum((d['carga_horaria'] or 0) for d in disciplinas_filtradas if d['status_raw'] == 'APV- Aprovado'))
        carga_concluida_filtrada = sum((d['carga_horaria'] or 0) for d in disciplinas_filtradas if d['concluida'])

        filtered_curriculo_grade.append({
            'periodo': periodo['periodo'],
            'periodo_label': periodo['periodo_label'],
            'total': total_filtrado,
            'concluidas': total_concluidas_filtrado,
            'pendentes': len(pendentes_filtradas),
            'percentual': percentual_filtrado,
            'carga_horaria_total': carga_total_filtrada,
            'carga_horaria_cursada': carga_cursada_filtrada,
            'carga_horaria_concluida': carga_concluida_filtrada,
            'carga_horaria_pendente': int(max(carga_total_filtrada - carga_cursada_filtrada, 0)),
            'disciplinas': disciplinas_filtradas,
            'disciplinas_concluidas': concluidas_filtradas,
            'disciplinas_pendentes': pendentes_filtradas,
        })

    total_curriculo = sum(periodo['total'] for periodo in filtered_curriculo_grade)
    total_concluidas = sum(periodo['concluidas'] for periodo in filtered_curriculo_grade)
    total_pendentes = total_curriculo - total_concluidas
    percentual_geral = round((total_concluidas / total_curriculo) * 100, 1) if total_curriculo else 0
    carga_total_geral = carga_total_curriculo
    carga_cursada_geral = int(historico_carga_cursada)
    carga_concluida_geral = sum(periodo.get('carga_horaria_concluida', 0) for periodo in filtered_curriculo_grade)
    carga_pendente_geral = int(max(carga_total_geral - carga_cursada_geral, 0))

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
            'carga_horaria_total': carga_total_geral,
            'carga_horaria_cursada': carga_cursada_geral,
            'carga_horaria_concluida': carga_concluida_geral,
            'carga_horaria_pendente': carga_pendente_geral,
        },
        'apenas_pendentes': apenas_pendentes,
        'mostrar_eletivas': mostrar_eletivas,
        'mostrar_optativas': mostrar_optativas,
        'mostrar_demais': mostrar_demais,
    })