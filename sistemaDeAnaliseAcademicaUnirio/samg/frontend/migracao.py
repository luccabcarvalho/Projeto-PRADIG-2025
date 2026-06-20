from pathlib import Path
import os
import re
import unicodedata

import pandas as pd
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render


USER_ID = 'user1'
CURRICULO_FILES = ['curriculo-20002.csv', 'curriculo-20052.csv', 'curriculo-20081.csv', 'curriculo-20232.csv']
LATEST_CURRICULO_FILE = 'curriculo-20232.csv'

STATUS_CONCLUIDAS = {
    'APV - Aprovado',
    'APV- Aprovado',
    'APV - Aprovado sem nota',
    'ADI - Aproveitamento',
    'ADI - Aproveitamento de créditos da disciplina',
    'ADI - Dispensa com nota',
    'DIS - Dispensa sem nota',
}


def _first_existing(paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


def _normalize_text(value):
    if pd.isna(value):
        return ''
    text = unicodedata.normalize('NFKD', str(value))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r'^[a-z]{3}\d{4}\s*-\s*', '', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def _extract_name(value):
    value = '' if pd.isna(value) else str(value).strip()
    if ' - ' in value:
        return value.split(' - ', 1)[1].strip()
    return value


def _version_key(value):
    return re.sub(r'\D', '', '' if pd.isna(value) else str(value)) or '20232'


def _load_base_data():
    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)

    alunos_path = _first_existing([
        media_root / USER_ID / 'alunosPorCurso.csv',
        base_dir / 'visualizacoes' / 'data' / 'alunosPorCurso.csv',
    ])
    historico_path = _first_existing([
        media_root / USER_ID / 'historicoEscolar.csv',
        base_dir / 'visualizacoes' / 'data' / 'HistoricoEscolarSimplificado.csv',
    ])

    if not alunos_path or not historico_path:
        return None, None, 'Não foi possível localizar os arquivos de alunos e histórico.'

    df_alunos = pd.read_csv(alunos_path, dtype={'MATR ALUNO': str})
    df_historico = pd.read_csv(historico_path, dtype={'MATR ALUNO': str})

    df_alunos['MATR ALUNO'] = df_alunos['MATR ALUNO'].astype(str).str.strip()
    df_historico['MATR ALUNO'] = df_historico['MATR ALUNO'].astype(str).str.strip()
    if 'COD ATIV CURRIC' in df_historico.columns:
        df_historico['COD ATIV CURRIC'] = df_historico['COD ATIV CURRIC'].astype(str).str.strip()

    for col in ['ANO', 'PERIODO', 'SITUACAO ITEM']:
        if col in df_historico.columns:
            if col == 'PERIODO':
                df_historico['PERIODO_NUM'] = pd.to_numeric(
                    df_historico[col].astype(str).str.extract(r'(\d+)')[0],
                    errors='coerce'
                ).fillna(0).astype(int)
            else:
                df_historico[f'{col}_NUM'] = pd.to_numeric(df_historico[col], errors='coerce').fillna(0).astype(int)

    df_historico['ANO_NUM'] = df_historico.get('ANO_NUM', 0)
    df_historico['PERIODO_NUM'] = df_historico.get('PERIODO_NUM', 0)
    df_historico['SITUACAO_ITEM_NUM'] = df_historico.get('SITUACAO_ITEM_NUM', 0)
    return df_alunos, df_historico, None


def _load_curriculo(version):
    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)
    curriculo_file = f'curriculo-{version}.csv'
    curriculo_path = _first_existing([
        media_root / 'curriculos_bsi' / curriculo_file,
        base_dir / 'visualizacoes' / 'data' / curriculo_file,
    ])
    if not curriculo_path:
        return None
    df = pd.read_csv(curriculo_path)
    df['COD DISCIPLINA'] = df['COD DISCIPLINA'].astype(str).str.strip()
    df['NOME LIMPO'] = df['NOME DISCIPLINA'].apply(_extract_name)
    df['NOME NORMALIZADO'] = df['NOME LIMPO'].apply(_normalize_text)
    if 'PERIODO IDEAL' in df.columns:
        df['PERIODO IDEAL_NUM'] = pd.to_numeric(df['PERIODO IDEAL'], errors='coerce').fillna(999).astype(int)
    else:
        df['PERIODO IDEAL_NUM'] = 999
    return df


@login_required
def migracao(request):
    df_alunos, df_historico, erro_base = _load_base_data()
    if erro_base:
        return render(request, 'migracao.html', {
            'message': erro_base,
            'alunos_options': [],
            'selected_id': '',
            'aluno_nome': '',
            'curriculo_atual': '',
            'curriculo_novo': '20232',
            'resumo': {'total_atual': 0, 'total_novo': 0, 'reaproveitadas': 0, 'aproveitamento': 0},
            'disciplinas_reaproveitadas': [],
            'disciplinas_nao_reaproveitadas': [],
        })

    alunos_options = [
        {'id': matricula, 'label': f"{matricula} - {nome}"}
        for matricula, nome in df_alunos[['MATR ALUNO', 'NOME PESSOA']]
        .drop_duplicates()
        .sort_values('NOME PESSOA')
        .values
    ]
    matriculas_validas = {item['id'] for item in alunos_options}

    selected_id = request.GET.get('matr_aluno', '').strip()
    if not selected_id:
        username = (request.user.username or '').strip()
        selected_id = username if username in matriculas_validas else ''
    if selected_id not in matriculas_validas:
        selected_id = alunos_options[0]['id'] if alunos_options else ''

    if not selected_id:
        return render(request, 'migracao.html', {
            'message': 'Não há alunos disponíveis para a comparação.',
            'alunos_options': [],
            'selected_id': '',
            'aluno_nome': '',
            'curriculo_atual': '',
            'curriculo_novo': '20232',
            'resumo': {'total_atual': 0, 'total_novo': 0, 'reaproveitadas': 0, 'aproveitamento': 0},
            'disciplinas_reaproveitadas': [],
            'disciplinas_nao_reaproveitadas': [],
        })

    aluno_row = df_alunos[df_alunos['MATR ALUNO'] == selected_id].copy()
    if aluno_row.empty:
        return render(request, 'migracao.html', {
            'message': 'Não foi possível localizar o aluno selecionado.',
            'alunos_options': alunos_options,
            'selected_id': selected_id,
            'aluno_nome': '',
            'curriculo_atual': '',
            'curriculo_novo': '20232',
            'resumo': {'total_atual': 0, 'total_novo': 0, 'reaproveitadas': 0, 'aproveitamento': 0},
            'disciplinas_reaproveitadas': [],
            'disciplinas_nao_reaproveitadas': [],
        })

    aluno_row = aluno_row.iloc[0]
    aluno_nome = str(aluno_row.get('NOME PESSOA', '')).strip()
    curriculo_atual_label = str(aluno_row.get('NUM VERSAO', '')).strip() or '20232'
    curriculo_atual = _version_key(aluno_row.get('NUM VERSAO', '20232'))

    df_curriculo_atual = _load_curriculo(curriculo_atual)
    df_curriculo_novo = _load_curriculo('20232')
    if df_curriculo_atual is None or df_curriculo_novo is None:
        return render(request, 'migracao.html', {
            'message': 'Não foi possível carregar um dos currículos necessários para a comparação.',
            'alunos_options': alunos_options,
            'selected_id': selected_id,
            'aluno_nome': aluno_nome,
            'curriculo_atual': curriculo_atual_label_label_label_label,
            'curriculo_novo': '20232',
            'resumo': {'total_atual': 0, 'total_novo': 0, 'reaproveitadas': 0, 'aproveitamento': 0},
            'disciplinas_reaproveitadas': [],
            'disciplinas_nao_reaproveitadas': [],
        })

    df_historico_aluno = df_historico[df_historico['MATR ALUNO'] == selected_id].copy()
    if df_historico_aluno.empty:
        historico_concluido = set()
    else:
        df_historico_aluno = df_historico_aluno.sort_values(
            by=['COD ATIV CURRIC', 'ANO_NUM', 'PERIODO_NUM', 'SITUACAO_ITEM_NUM'],
            ascending=[True, True, True, True],
        )
        df_historico_ultimo = df_historico_aluno.drop_duplicates(subset=['COD ATIV CURRIC'], keep='last')
        df_historico_ultimo['STATUS_CONCLUIDO'] = df_historico_ultimo['DESCR SITUACAO'].astype(str).str.strip().isin(STATUS_CONCLUIDAS)
        historico_concluido = set(
            df_historico_ultimo[df_historico_ultimo['STATUS_CONCLUIDO']]['COD ATIV CURRIC'].astype(str).str.strip()
        )

    novo_por_nome = {}
    for _, row in df_curriculo_novo.drop_duplicates(subset=['NOME NORMALIZADO'], keep='first').iterrows():
        novo_por_nome[row['NOME NORMALIZADO']] = row

    comparacao = []
    for _, row in df_curriculo_atual.sort_values(['PERIODO IDEAL_NUM', 'COD DISCIPLINA']).drop_duplicates(subset=['NOME NORMALIZADO'], keep='first').iterrows():
        nome_norm = row['NOME NORMALIZADO']
        equivalente = novo_por_nome.get(nome_norm)
        codigo_atual = str(row.get('COD DISCIPLINA', '')).strip()
        nome_atual = row.get('NOME LIMPO', '')
        concluida = codigo_atual in historico_concluido

        item = {
            'codigo_atual': codigo_atual,
            'nome_atual': nome_atual,
            'periodo_atual': row.get('PERIODO IDEAL_NUM', ''),
            'concluida': concluida,
            'status_reaproveitamento': 'Reaproveitável' if equivalente is not None else 'Sem equivalente',
            'codigo_novo': '',
            'nome_novo': '',
            'periodo_novo': '',
            'reaproveitada': False,
        }
        if equivalente is not None:
            item['codigo_novo'] = str(equivalente.get('COD DISCIPLINA', '')).strip()
            item['nome_novo'] = equivalente.get('NOME LIMPO', '')
            item['periodo_novo'] = equivalente.get('PERIODO IDEAL_NUM', '')
            item['reaproveitada'] = True
        comparacao.append(item)

    disciplinas_reaproveitadas = [item for item in comparacao if item['reaproveitada'] and item['concluida']]
    disciplinas_nao_reaproveitadas = [item for item in comparacao if not item['reaproveitada']]

    total_atual = len(comparacao)
    total_novo = len(df_curriculo_novo.drop_duplicates(subset=['NOME NORMALIZADO']))
    reaproveitadas = len([item for item in comparacao if item['reaproveitada']])
    aproveitamento = round((reaproveitadas / total_atual) * 100, 1) if total_atual else 0

    return render(request, 'migracao.html', {
        'message': '',
        'alunos_options': alunos_options,
        'selected_id': selected_id,
        'aluno_nome': aluno_nome,
        'curriculo_atual': curriculo_atual,
        'curriculo_novo': '20232',
        'resumo': {
            'total_atual': total_atual,
            'total_novo': total_novo,
            'reaproveitadas': reaproveitadas,
            'aproveitamento': aproveitamento,
        },
        'disciplinas_reaproveitadas': disciplinas_reaproveitadas,
        'disciplinas_nao_reaproveitadas': disciplinas_nao_reaproveitadas,
        'comparacao_total': comparacao,
    })