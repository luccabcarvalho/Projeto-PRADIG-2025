from pathlib import Path
import os
import re
import unicodedata

import pandas as pd
from django.conf import settings


USER_ID = 'user1'
DEFAULT_CURRICULO_VERSION = '20232'
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


def first_existing(paths):
    for path in paths:
        if path and os.path.exists(path):
            return path
    return None


def normalize_text(value):
    if pd.isna(value):
        return ''
    text = unicodedata.normalize('NFKD', str(value))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().strip()
    text = re.sub(r'^[a-z]{3}\d{4}\s*-\s*', '', text)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()


def extract_name(value):
    value = '' if pd.isna(value) else str(value).strip()
    if ' - ' in value:
        return value.split(' - ', 1)[1].strip()
    return value


def extract_sigla(value):
    value = '' if pd.isna(value) else str(value).strip()
    if ' - ' in value:
        return value.split(' - ', 1)[0].strip()
    return value


def version_key(value):
    return re.sub(r'\D', '', '' if pd.isna(value) else str(value)) or DEFAULT_CURRICULO_VERSION


def load_base_data():
    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)

    alunos_path = first_existing([
        media_root / USER_ID / 'alunosPorCurso.csv',
        base_dir / 'visualizacoes' / 'data' / 'alunosPorCurso.csv',
    ])
    historico_path = first_existing([
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
        df_historico['SITUACAO_ITEM_NUM'] = pd.to_numeric(
            df_historico['SITUACAO ITEM'],
            errors='coerce'
        ).fillna(0).astype(int)
    else:
        df_historico['SITUACAO_ITEM_NUM'] = 0

    df_historico['ANO_PERIODO'] = df_historico['ANO_NUM'].astype(str) + ' - ' + df_historico.get('PERIODO', '').astype(str)
    return df_alunos, df_historico, None


def build_alunos_options(df_alunos):
    return [
        {'id': matricula, 'label': f"{matricula} - {nome}"}
        for matricula, nome in df_alunos[['MATR ALUNO', 'NOME PESSOA']]
        .drop_duplicates()
        .sort_values('NOME PESSOA')
        .values
    ]


def resolve_selected_id(request, valid_ids, param_name='matr_aluno'):
    selected_id = request.GET.get(param_name, '').strip()
    if not selected_id:
        username = (request.user.username or '').strip()
        selected_id = username if username in valid_ids else ''
    if selected_id not in valid_ids:
        selected_id = next(iter(valid_ids), '')
    return selected_id


def load_curriculo(version):
    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)
    curriculo_file = CURRICULO_FILES.get(version_key(version), CURRICULO_FILES[DEFAULT_CURRICULO_VERSION])
    curriculo_path = first_existing([
        media_root / 'curriculos_bsi' / curriculo_file,
        base_dir / 'visualizacoes' / 'data' / curriculo_file,
    ])
    if not curriculo_path:
        return None

    df = pd.read_csv(curriculo_path)
    if 'COD DISCIPLINA' in df.columns:
        df['COD DISCIPLINA'] = df['COD DISCIPLINA'].astype(str).str.strip()
    if 'NOME DISCIPLINA' in df.columns:
        df['NOME LIMPO'] = df['NOME DISCIPLINA'].apply(extract_name)
        df['NOME NORMALIZADO'] = df['NOME LIMPO'].apply(normalize_text)
    else:
        df['NOME LIMPO'] = ''
        df['NOME NORMALIZADO'] = ''
    if 'PERIODO IDEAL' in df.columns:
        df['PERIODO IDEAL_NUM'] = pd.to_numeric(df['PERIODO IDEAL'], errors='coerce').fillna(999).astype(int)
    else:
        df['PERIODO IDEAL_NUM'] = 999
    return df


def build_historico_concluido(df_historico, matricula):
    df_historico_aluno = df_historico[df_historico['MATR ALUNO'] == matricula].copy()
    if df_historico_aluno.empty:
        return set()

    df_historico_aluno = df_historico_aluno.sort_values(
        by=['COD ATIV CURRIC', 'ANO_NUM', 'PERIODO_NUM', 'SITUACAO_ITEM_NUM'],
        ascending=[True, True, True, True],
    )
    df_historico_ultimo = df_historico_aluno.drop_duplicates(subset=['COD ATIV CURRIC'], keep='last')
    df_historico_ultimo['STATUS_CONCLUIDO'] = df_historico_ultimo['DESCR SITUACAO'].astype(str).str.strip().isin(STATUS_CONCLUIDAS)
    return set(
        df_historico_ultimo[df_historico_ultimo['STATUS_CONCLUIDO']]['COD ATIV CURRIC'].astype(str).str.strip()
    )


def status_info(status):
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


def is_tipo_obrigatoria(tipo_disciplina):
    return str(tipo_disciplina or '').strip().casefold() == 'obrigatória'.casefold()


def filtrar_disciplinas(disciplinas, apenas_obrigatorias=False, apenas_pendentes=False):
    disciplinas_filtradas = list(disciplinas or [])
    if apenas_obrigatorias:
        disciplinas_filtradas = [item for item in disciplinas_filtradas if item.get('obrigatoria')]
    if apenas_pendentes:
        disciplinas_filtradas = [item for item in disciplinas_filtradas if not item.get('concluida')]
    return disciplinas_filtradas


def filtrar_resultado_comparacao(resultado_comparacao, apenas_obrigatorias=False, apenas_pendentes=False):
    comparacao_filtrada = filtrar_disciplinas(
        resultado_comparacao.get('comparacao', []),
        apenas_obrigatorias=apenas_obrigatorias,
        apenas_pendentes=apenas_pendentes,
    )

    disciplinas_reaproveitadas = [
        item for item in comparacao_filtrada if item.get('reaproveitada') and item.get('concluida')
    ]
    disciplinas_nao_reaproveitadas = [
        item for item in comparacao_filtrada if not item.get('reaproveitada')
    ]

    return {
        'comparacao': comparacao_filtrada,
        'disciplinas_reaproveitadas': disciplinas_reaproveitadas,
        'disciplinas_nao_reaproveitadas': disciplinas_nao_reaproveitadas,
    }


def compare_curriculos(df_curriculo_atual, df_curriculo_novo, historico_concluido):
    novo_por_nome = {
        row['NOME NORMALIZADO']: row
        for _, row in df_curriculo_novo.drop_duplicates(subset=['NOME NORMALIZADO'], keep='first').iterrows()
    }

    comparacao = []
    ordenado_atual = df_curriculo_atual.sort_values(['PERIODO IDEAL_NUM', 'COD DISCIPLINA']).drop_duplicates(subset=['NOME NORMALIZADO'], keep='first')

    for _, row in ordenado_atual.iterrows():
        nome_norm = row['NOME NORMALIZADO']
        equivalente = novo_por_nome.get(nome_norm)
        codigo_atual = str(row.get('COD DISCIPLINA', '')).strip()
        nome_atual = row.get('NOME LIMPO', '')
        concluida = codigo_atual in historico_concluido
        tipo_disciplina = str(row.get('TIPO DISCIPLINA', '')).strip()
        obrigatoria = is_tipo_obrigatoria(tipo_disciplina)

        item = {
            'codigo_atual': codigo_atual,
            'nome_atual': nome_atual,
            'periodo_atual': row.get('PERIODO IDEAL_NUM', ''),
            'concluida': concluida,
            'tipo_disciplina': tipo_disciplina,
            'obrigatoria': obrigatoria,
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

    return {
        'comparacao': comparacao,
        'disciplinas_reaproveitadas': disciplinas_reaproveitadas,
        'disciplinas_nao_reaproveitadas': disciplinas_nao_reaproveitadas,
        'resumo': {
            'total_atual': total_atual,
            'total_novo': total_novo,
            'reaproveitadas': reaproveitadas,
            'aproveitamento': aproveitamento,
        },
    }