from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from samg.frontend.common import (
    geraListaAlunos,
    build_historico_concluido,
    compare_curriculos,
    filtrar_resultado_comparacao,
    carregaBD,
    carregaCurriculo,
    getMatriculaAluno,
    versaoCurriculo,
)


DEFAULT_CURRICULO_VERSION = '20232'


USER_ID = 'user1'


@login_required
def migracao(request):
    apenas_obrigatorias = request.GET.get('apenas_obrigatorias') == '1'
    apenas_pendentes = request.GET.get('apenas_pendentes') == '1'

    df_alunos, df_historico, erro_base = carregaBD()
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
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    alunos_options = geraListaAlunos(df_alunos)
    matriculas_validas = {item['id'] for item in alunos_options}
    selected_id = getMatriculaAluno(request, matriculas_validas)

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
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
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
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    aluno_row = aluno_row.iloc[0]
    aluno_nome = str(aluno_row.get('NOME PESSOA', '')).strip()
    curriculo_atual_label = str(aluno_row.get('NUM VERSAO', '')).strip() or DEFAULT_CURRICULO_VERSION
    curriculo_atual = versaoCurriculo(aluno_row.get('NUM VERSAO', DEFAULT_CURRICULO_VERSION))

    df_curriculo_atual = carregaCurriculo(curriculo_atual)
    df_curriculo_novo = carregaCurriculo(DEFAULT_CURRICULO_VERSION)
    if df_curriculo_atual is None or df_curriculo_novo is None:
        return render(request, 'migracao.html', {
            'message': 'Não foi possível carregar um dos currículos necessários para a comparação.',
            'alunos_options': alunos_options,
            'selected_id': selected_id,
            'aluno_nome': aluno_nome,
            'curriculo_atual': curriculo_atual_label,
            'curriculo_novo': DEFAULT_CURRICULO_VERSION,
            'resumo': {'total_atual': 0, 'total_novo': 0, 'reaproveitadas': 0, 'aproveitamento': 0},
            'disciplinas_reaproveitadas': [],
            'disciplinas_nao_reaproveitadas': [],
            'apenas_obrigatorias': apenas_obrigatorias,
            'apenas_pendentes': apenas_pendentes,
        })

    historico_concluido = build_historico_concluido(df_historico, selected_id)
    resultado_comparacao = compare_curriculos(df_curriculo_atual, df_curriculo_novo, historico_concluido)
    comparacao_filtrada = filtrar_resultado_comparacao(
        resultado_comparacao,
        apenas_obrigatorias=apenas_obrigatorias,
        apenas_pendentes=apenas_pendentes,
    )

    return render(request, 'migracao.html', {
        'message': '',
        'alunos_options': alunos_options,
        'selected_id': selected_id,
        'aluno_nome': aluno_nome,
        'curriculo_atual': curriculo_atual_label,
        'curriculo_novo': DEFAULT_CURRICULO_VERSION,
        'resumo': resultado_comparacao['resumo'],
        'disciplinas_reaproveitadas': comparacao_filtrada['disciplinas_reaproveitadas'],
        'disciplinas_nao_reaproveitadas': comparacao_filtrada['disciplinas_nao_reaproveitadas'],
        'comparacao_total': comparacao_filtrada['comparacao'],
        'apenas_obrigatorias': apenas_obrigatorias,
        'apenas_pendentes': apenas_pendentes,
    })