from pathlib import Path
import os
import re

import pandas as pd
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


USER_ID = 'user1'

CURRICULO_FILES = {
    '20232': 'curriculo-20232.csv',
    '20052': 'curriculo-20052.csv',
    '20002': 'curriculo-20002.csv',
    '20081': 'curriculo-20081.csv',
}

STATUS_CONCLUIDAS = {
    'APV - Aprovado',
    'APV- Aprovado',
    'APV - Aprovado sem nota',
    'ADI - Aproveitamento',
    'ADI - Aproveitamento de créditos da disciplina',
    'ADI - Dispensa com nota',
    'DIS - Dispensa sem nota',
}

STATUS_EM_ANDAMENTO = {
    'ASC - Matrícula',
}

STATUS_REPROVADAS = {
    'REP - Reprovado por nota/conceito',
    'REF - Reprovado por falta',
    'ASC - Reprovado sem nota',
    'TRA - Trancamento de disciplina',
}


def _primeiro_arquivo_existente(caminhos):
    for caminho in caminhos:
        if caminho and os.path.exists(caminho):
            return caminho
    return None


def _normalizar_versao(valor):
    if pd.isna(valor):
        return ''
    return re.sub(r'\D', '', str(valor).strip())


def _extrair_sigla(codigo):
    codigo = str(codigo).strip()
    if ' - ' in codigo:
        return codigo.split(' - ', 1)[0].strip()
    return codigo


def _extrair_nome(codigo, nome):
    nome = '' if pd.isna(nome) else str(nome).strip()
    if nome and ' - ' in nome:
        return nome.split(' - ', 1)[1].strip()
    if nome:
        return nome
    return _extrair_sigla(codigo)


def _periodo_sort_key(valor):
    match = re.search(r'(\d+)', str(valor))
    return int(match.group(1)) if match else 999


def _status_info(status):
    status = '' if pd.isna(status) else str(status).strip()
    if status in STATUS_CONCLUIDAS:
        return 'Concluída', 'success', True, False, False
    if status in STATUS_EM_ANDAMENTO:
        return 'Cursando', 'info', False, True, False
    if status in STATUS_REPROVADAS:
        return 'Não concluída', 'danger', False, False, True
    if status:
        return status, 'secondary', False, False, False
    return 'Não cursada', 'light', False, False, False


def _carregar_dados_base():
    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)

    alunos_path = _primeiro_arquivo_existente([
        media_root / USER_ID / 'alunosPorCurso.csv',
        base_dir / 'visualizacoes' / 'data' / 'alunosPorCurso.csv',
    ])
    historico_path = _primeiro_arquivo_existente([
        media_root / USER_ID / 'historicoEscolar.csv',
        base_dir / 'visualizacoes' / 'data' / 'HistoricoEscolarSimplificado.csv',
    ])

    if not alunos_path or not historico_path:
        return None, None, 'Não foi possível localizar os arquivos de histórico e alunos.'

    df_alunos = pd.read_csv(alunos_path, dtype={'MATR ALUNO': str})
    df_historico = pd.read_csv(historico_path, dtype={'MATR ALUNO': str})

    if 'COD ATIV CURRIC' in df_historico.columns:
        df_historico['COD ATIV CURRIC'] = df_historico['COD ATIV CURRIC'].astype(str).str.strip()
    if 'PERIODO' in df_historico.columns:
        df_historico['PERIODO_NUM'] = pd.to_numeric(
            df_historico['PERIODO'].astype(str).str.extract(r'(\d+)')[0],
            errors='coerce'
        ).fillna(0).astype(int)
    else:
        df_historico['PERIODO_NUM'] = 0
    if 'ANO' in df_historico.columns:
        df_historico['ANO_NUM'] = pd.to_numeric(df_historico['ANO'], errors='coerce').fillna(0).astype(int)
    else:
        df_historico['ANO_NUM'] = 0
    if 'SITUACAO ITEM' in df_historico.columns:
        df_historico['SITUACAO_ITEM_NUM'] = pd.to_numeric(df_historico['SITUACAO ITEM'], errors='coerce').fillna(0).astype(int)
    else:
        df_historico['SITUACAO_ITEM_NUM'] = 0

    df_historico['ANO_PERIODO'] = df_historico['ANO_NUM'].astype(str) + ' - ' + df_historico.get('PERIODO', '').astype(str)
    return df_alunos, df_historico, None


@login_required
def progresso(request):
    df_alunos, df_historico, erro_base = _carregar_dados_base()
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
        })

    df_alunos['MATR ALUNO'] = df_alunos['MATR ALUNO'].astype(str).str.strip()
    df_historico['MATR ALUNO'] = df_historico['MATR ALUNO'].astype(str).str.strip()

    alunos_options = [
        {'id': matricula, 'label': f"{matricula} - {nome}"}
        for matricula, nome in df_alunos[['MATR ALUNO', 'NOME PESSOA']]
        .drop_duplicates()
        .sort_values('NOME PESSOA')
        .values
    ]

    matriculas_validas = {item['id'] for item in alunos_options}
    matricula_selecionada = request.GET.get('matr_aluno', '').strip()
    if not matricula_selecionada:
        matricula_selecionada = request.user.username.strip() if request.user.username and request.user.username.strip() in matriculas_validas else ''
    if matricula_selecionada not in matriculas_validas:
        matricula_selecionada = alunos_options[0]['id'] if alunos_options else ''

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
        })

    aluno_base = aluno_base.iloc[0]
    aluno_nome = str(aluno_base.get('NOME PESSOA', '')).strip()
    versao_curriculo = _normalizar_versao(aluno_base.get('NUM VERSAO')) or '20232'
    curriculo_file = CURRICULO_FILES.get(versao_curriculo, CURRICULO_FILES['20232'])

    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)
    curriculo_path = _primeiro_arquivo_existente([
        media_root / 'curriculos_bsi' / curriculo_file,
        base_dir / 'visualizacoes' / 'data' / curriculo_file,
    ])

    if not curriculo_path:
        return render(request, 'progresso.html', {
            'message': f'Não foi possível localizar o currículo da versão {versao_curriculo}.',
            'curriculoGrade': [],
            'filteredCurriculoGrade': [],
            'curriculoStats': {'total': 0, 'concluidas': 0, 'pendentes': 0, 'percentual': 0},
            'alunos_options': alunos_options,
            'selected_id': matricula_selecionada,
            'curriculoVersion': aluno_base.get('NUM VERSAO', versao_curriculo),
            'aluno_nome': aluno_nome,
        })

    df_curriculo = pd.read_csv(curriculo_path)
    if 'COD CURSO' in df_curriculo.columns and 'COD CURSO' in aluno_base.index:
        cod_curso = str(aluno_base.get('COD CURSO', '')).strip()
        if cod_curso and cod_curso != 'nan':
            df_curriculo = df_curriculo[df_curriculo['COD CURSO'].astype(str).str.strip() == cod_curso]

    if 'PERIODO IDEAL' in df_curriculo.columns:
        df_curriculo['PERIODO IDEAL_NUM'] = pd.to_numeric(df_curriculo['PERIODO IDEAL'], errors='coerce').fillna(999).astype(int)
    else:
        df_curriculo['PERIODO IDEAL_NUM'] = 999

    if 'COD DISCIPLINA' in df_curriculo.columns:
        df_curriculo['COD DISCIPLINA'] = df_curriculo['COD DISCIPLINA'].astype(str).str.strip()

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
        })

    historico_aluno = historico_aluno.sort_values(
        by=['COD ATIV CURRIC', 'ANO_NUM', 'PERIODO_NUM', 'SITUACAO_ITEM_NUM'],
        ascending=[True, True, True, True],
    )
    historico_ultimo_status = historico_aluno.drop_duplicates(subset=['COD ATIV CURRIC'], keep='last')
    historico_map = historico_ultimo_status.set_index('COD ATIV CURRIC').to_dict('index')

    curriculo_grade = []
    disciplinas_concluidas = []

    for periodo_ideal, df_periodo in df_curriculo.sort_values(['PERIODO IDEAL_NUM', 'COD DISCIPLINA']).groupby('PERIODO IDEAL_NUM'):
        disciplinas_periodo = []
        for _, row in df_periodo.drop_duplicates(subset=['COD DISCIPLINA'], keep='first').iterrows():
            codigo = str(row.get('COD DISCIPLINA', '')).strip()
            nome_curto = _extrair_nome(codigo, row.get('NOME DISCIPLINA', ''))
            sigla = _extrair_sigla(codigo)
            historico = historico_map.get(codigo)
            status_raw = '' if not historico else str(historico.get('DESCR SITUACAO', '')).strip()
            status_label, status_badge, concluida, cursando, reprovada = _status_info(status_raw)
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

    total_curriculo = sum(periodo['total'] for periodo in curriculo_grade)
    total_concluidas = sum(periodo['concluidas'] for periodo in curriculo_grade)
    total_pendentes = total_curriculo - total_concluidas
    percentual_geral = round((total_concluidas / total_curriculo) * 100, 1) if total_curriculo else 0

    return render(request, 'progresso.html', {
        'message': '',
        'alunos_options': alunos_options,
        'selected_id': matricula_selecionada,
        'aluno_nome': aluno_nome,
        'curriculoVersion': aluno_base.get('NUM VERSAO', versao_curriculo),
        'curriculoGrade': curriculo_grade,
        'filteredCurriculoGrade': curriculo_grade,
        'disciplinas_concluidas': disciplinas_concluidas,
        'curriculoStats': {
            'total': total_curriculo,
            'concluidas': total_concluidas,
            'pendentes': total_pendentes,
            'percentual': percentual_geral,
        },
    })