from pathlib import Path
import os
import re
import unicodedata

import pandas as pd
from django.conf import settings


USER_ID = 'user1'
CURRICULO_FILE = 'curriculos-bsi.csv'

# Mapeamento entre código de versão (20232) e NUM VERSAO no arquivo consolidado (2023/2)
VERSION_MAPPING = {
    '20232': '2023/2',
    '20052': '2005/2',
    '20002': '2000/2',
    '20081': '2008/1',
}

def obter_versoes_disponiveis():
    
    # Ordena as versões com base no mapeamento de NUM VERSAO para código de versão
    return sorted(VERSION_MAPPING.keys())


def obter_proxima_versao(versao_atual):

    # Obtém a lista de versões disponíveis
    versoes = obter_versoes_disponiveis()
    
    if versao_atual not in versoes:
        return None, False
    
    indice_atual = versoes.index(versao_atual)
    
    # Verifica se existe uma próxima versão
    if indice_atual + 1 < len(versoes):
        return versoes[indice_atual + 1], True
    else:
        return None, True  # Versão atual encontrada, mas é a última


STATUS_CONCLUIDAS = {
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


def versaoCurriculo(value):
    return re.sub(r'\D', '', '' if pd.isna(value) else str(value))


def carregaBD():
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


def geraListaAlunos(df_alunos):
    return [
        {'id': matricula, 'label': f"{matricula} - {nome}"}
        for matricula, nome in df_alunos[['MATR ALUNO', 'NOME PESSOA']]
        .drop_duplicates()
        .sort_values('NOME PESSOA')
        .values
    ]


def getMatriculaAluno(request, valid_ids, param_name='matr_aluno'):
    selected_id = request.GET.get(param_name, '').strip()
    if not selected_id:
        username = (request.user.username or '').strip()
        selected_id = username if username in valid_ids else ''
    if selected_id not in valid_ids:
        selected_id = next(iter(valid_ids), '')
    return selected_id


def carregaCurriculo(version):
    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)
    curriculo_path = first_existing([
        media_root / 'curriculos_bsi' / CURRICULO_FILE,
        base_dir / 'visualizacoes' / 'data' / CURRICULO_FILE,
    ])
    if not curriculo_path:
        return None
    df = None
    # 1) tentativa padrão com utf-8-sig
    try:
        df = pd.read_csv(curriculo_path, encoding='utf-8-sig')
    except Exception as e1:
        # tenta com separador ";"
        try:
            df = pd.read_csv(curriculo_path, sep=';', engine='python', encoding='utf-8-sig')
        except Exception as e2:
            # tenta com latin-1 
            try:
                df = pd.read_csv(curriculo_path, sep=';', engine='python', encoding='latin-1')
            except Exception:
                # Falha ao ler o CSV
                return None
    versao_codigo = versaoCurriculo(version)
    # Mapeia código de versão para NUM VERSAO no arquivo consolidado
    versao_num = VERSION_MAPPING.get(versao_codigo, versao_codigo)
    if 'NUM VERSAO' in df.columns:
        df = df[df['NUM VERSAO'].astype(str).str.strip() == versao_num]
    if df.empty:
        return None
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


def carregaEquivalencias():
    """Carrega o arquivo de equivalências entre currículos.
    
    Arquivo: "Relação de equivalência dos currículos.csv"
    Estrutura: separado por ";"
    - NUM_VERSAO: versão DESTINO (ex: 2023/2)
    - NOME_DISCIPLINA: código + nome da disciplina na versão DESTINO
    - NOME_DISC_EQUIV: código + nome da disciplina equivalente em versão ANTERIOR
    
    Exemplo de linha:
    2023/2;...;TIN0223 - Introdução à Lógica Computacional;TIN0105 - INTRODUÇÃO À LÓGICA COMPUTACIONAL;...
    
    Retorna um DataFrame com mapeamento de (código_antigo, versão_novo) → código_novo
    """
    media_root = Path(settings.MEDIA_ROOT)
    base_dir = Path(settings.BASE_DIR)
    
    # Procura o arquivo de equivalências
    equivalencias_path = first_existing([
        media_root / 'curriculos_bsi' / 'Relação de equivalência dos currículos.csv',
        base_dir / 'visualizacoes' / 'data' / 'Relação de equivalência dos currículos.csv',
    ])
    
    if not equivalencias_path:
        return None
    
    try:
        # Carrega com separador ";" e encoding correto para acentos
        df = pd.read_csv(equivalencias_path, sep=';', encoding='utf-8-sig')
        
        # Normaliza nomes de colunas se necessário
        df.columns = df.columns.str.strip()
        
        # Remove linhas onde NOME_DISC_EQUIV está vazio (sem equivalência)
        df = df.dropna(subset=['NOME_DISC_EQUIV'])
        df = df[df['NOME_DISC_EQUIV'].astype(str).str.strip() != '']
        
        # Extrai os códigos das disciplinas
        # NOME_DISCIPLINA e NOME_DISC_EQUIV têm format: "TINU0XXX - Nome da Disciplina"
        df['COD_NOVO'] = df['NOME_DISCIPLINA'].astype(str).str.extract(r'^([A-Z]+\d{4})', expand=False)
        df['COD_ANTIGO'] = df['NOME_DISC_EQUIV'].astype(str).str.extract(r'^([A-Z]+\d{4})', expand=False)
        df['NUM_VERSAO'] = df['NUM_VERSAO'].astype(str).str.strip()
        
        # Remove linhas onde não foi possível extrair os códigos
        df = df.dropna(subset=['COD_NOVO', 'COD_ANTIGO'])
        
        return df[['COD_ANTIGO', 'COD_NOVO', 'NUM_VERSAO']].copy()
    except Exception as e:
        print(f"Erro ao carregar equivalências: {e}")
        return None


def build_historico_concluido(df_historico, matricula):
    df_historico_aluno = df_historico[df_historico['MATR ALUNO'] == matricula].copy()
    if df_historico_aluno.empty:
        return set()

    df_historico_aluno = df_historico_aluno.sort_values(
        by=['COD ATIV CURRIC', 'ANO_NUM', 'PERIODO_NUM', 'SITUACAO_ITEM_NUM'],
        ascending=[True, True, True, False],
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


def filtrar_resultado_comparacao(
    resultado_comparacao,
    apenas_obrigatorias=False,
    apenas_pendentes=False,
    mostrar_eletivas=False,
    mostrar_optativas=False,
    mostrar_demais=False,
):
    comparacao_filtrada = []
    for item in resultado_comparacao.get('comparacao', []):
        if item.get('obrigatoria'):
            comparacao_filtrada.append(item)
        elif item.get('eletiva') and mostrar_eletivas:
            comparacao_filtrada.append(item)
        elif item.get('optativa') and mostrar_optativas:
            comparacao_filtrada.append(item)
        elif item.get('demais') and mostrar_demais:
            comparacao_filtrada.append(item)

    if apenas_obrigatorias:
        comparacao_filtrada = [item for item in comparacao_filtrada if item.get('obrigatoria')]
    if apenas_pendentes:
        comparacao_filtrada = [item for item in comparacao_filtrada if not item.get('concluida')]

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


def compare_curriculos(df_curriculo_atual, df_curriculo_novo, historico_concluido, df_equivalencias=None):
    """Compara dois currículos e identifica disciplinas equivalentes.
    
    A equivalência é buscada em ordem de prioridade:
    1. Arquivo de equivalências explícitas (equivalencias-disciplinas.csv)
    2. Matching por nome normalizado (fallback)
    
    Args:
        df_curriculo_atual: DataFrame com disciplinas do currículo anterior
        df_curriculo_novo: DataFrame com disciplinas do currículo novo
        historico_concluido: Set com códigos de disciplinas já concluídas
        df_equivalencias: DataFrame com equivalências mapeadas (opcional)
    """
    # Se não passar o DataFrame de equivalências, carrega automaticamente
    if df_equivalencias is None:
        df_equivalencias = carregaEquivalencias()
    
    # Indexa novo currículo por nome normalizado como fallback
    novo_por_nome = {
        row['NOME NORMALIZADO']: row
        for _, row in df_curriculo_novo.drop_duplicates(subset=['NOME NORMALIZADO'], keep='first').iterrows()
    }

    # Indexa novo currículo por código para busca rápida
    novo_por_codigo = {
        row['COD DISCIPLINA']: row
        for _, row in df_curriculo_novo.iterrows()
    }
    
    # Extrai versão do currículo novo para busca no arquivo de equivalências
    versao_novo = None
    if not df_curriculo_novo.empty:
        versao_novo = str(df_curriculo_novo.iloc[0].get('NUM VERSAO', '')).strip()
    
    # Mapeia equivalências do arquivo CSV
    # Formato esperado: COD_ANTIGO, COD_NOVO, NUM_VERSAO (versão novo)
    equivalencias_mapa = {}
    if df_equivalencias is not None and not df_equivalencias.empty and versao_novo:
        # Filtra equivalências para a versão do currículo novo
        df_equiv_filtrado = df_equivalencias[
            df_equivalencias['NUM_VERSAO'] == versao_novo
        ]
        
        # Cria mapeamento COD_ANTIGO → COD_NOVO
        for _, equiv_row in df_equiv_filtrado.iterrows():
            cod_antigo = str(equiv_row.get('COD_ANTIGO', '')).strip()
            cod_novo = str(equiv_row.get('COD_NOVO', '')).strip()
            
            if cod_antigo and cod_novo:
                equivalencias_mapa[cod_antigo] = cod_novo

    comparacao = []
    ordenado_atual = df_curriculo_atual.sort_values(['PERIODO IDEAL_NUM', 'COD DISCIPLINA']).drop_duplicates(subset=['NOME NORMALIZADO'], keep='first')

    for _, row in ordenado_atual.iterrows():
        codigo_atual = str(row.get('COD DISCIPLINA', '')).strip()
        nome_atual = row.get('NOME LIMPO', '')
        concluida = codigo_atual in historico_concluido
        tipo_disciplina = str(row.get('TIPO DISCIPLINA', '')).strip()
        tipo_norm = normalize_text(tipo_disciplina)
        obrigatoria = tipo_norm == 'obrigatoria'
        eletiva = tipo_norm == 'eletiva'
        optativa = tipo_norm == 'optativa'
        demais = not (obrigatoria or eletiva or optativa)

        # Procura equivalência primeiro no arquivo de equivalências
        equivalente = None
        
        if codigo_atual in equivalencias_mapa:
            # Encontrou uma equivalência explícita para este código
            cod_novo_equiv = equivalencias_mapa[codigo_atual]
            if cod_novo_equiv in novo_por_codigo:
                equivalente = novo_por_codigo[cod_novo_equiv]
        
        # Se não encontrou no arquivo de equivalências, tenta por nome normalizado (fallback)
        if equivalente is None:
            nome_norm = row['NOME NORMALIZADO']
            equivalente = novo_por_nome.get(nome_norm)

        item = {
            'codigo_atual': codigo_atual,
            'nome_atual': nome_atual,
            'periodo_atual': row.get('PERIODO IDEAL_NUM', ''),
            'concluida': concluida,
            'tipo_disciplina': tipo_disciplina,
            'obrigatoria': obrigatoria,
            'eletiva': eletiva,
            'optativa': optativa,
            'demais': demais,
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
    equivalencias_possiveis_grade = len([item for item in comparacao if item['reaproveitada']])
    aproveitadas_pelo_aluno = len([item for item in comparacao if item['reaproveitada'] and item['concluida']])
    reaproveitadas = equivalencias_possiveis_grade
    aproveitamento = round((reaproveitadas / total_atual) * 100, 1) if total_atual else 0
    aproveitamento_pelo_aluno = round((aproveitadas_pelo_aluno / equivalencias_possiveis_grade) * 100, 1) if equivalencias_possiveis_grade else 0

    return {
        'comparacao': comparacao,
        'disciplinas_reaproveitadas': disciplinas_reaproveitadas,
        'disciplinas_nao_reaproveitadas': disciplinas_nao_reaproveitadas,
        'resumo': {
            'total_atual': total_atual,
            'total_novo': total_novo,
            'reaproveitadas': reaproveitadas,
            'aproveitamento': aproveitamento,
            'equivalencias_possiveis_grade': equivalencias_possiveis_grade,
            'aproveitadas_pelo_aluno': aproveitadas_pelo_aluno,
            'aproveitamento_pelo_aluno': aproveitamento_pelo_aluno,
        },
    }