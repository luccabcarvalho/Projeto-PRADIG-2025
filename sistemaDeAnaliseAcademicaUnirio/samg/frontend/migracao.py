from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from samg.frontend.common import (
    geraListaAlunos,
    build_historico_concluido,
    compare_curriculos,
    filtrar_resultado_comparacao,
    carregaBD,
    carregaCurriculo,
    carregaEquivalencias,
    getMatriculaAluno,
    versaoCurriculo,
)


DEFAULT_CURRICULO_VERSION = '20232'


USER_ID = 'user1'


@login_required
def migracao(request):
    apenas_pendentes = request.GET.get('apenas_pendentes') == '1'
    mostrar_eletivas = request.GET.get('mostrar_eletivas') == '1'
    mostrar_optativas = request.GET.get('mostrar_optativas') == '1'
    mostrar_demais = request.GET.get('mostrar_demais') == '1'

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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
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
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
        })

    if 'COD CURSO' in aluno_row.index:
        cod_curso = str(aluno_row.get('COD CURSO', '')).strip()
        if cod_curso and cod_curso != 'nan':
            if 'COD CURSO' in df_curriculo_atual.columns:
                df_curriculo_atual = df_curriculo_atual[
                    df_curriculo_atual['COD CURSO'].astype(str).str.strip() == cod_curso
                ]
            if 'COD CURSO' in df_curriculo_novo.columns:
                df_curriculo_novo = df_curriculo_novo[
                    df_curriculo_novo['COD CURSO'].astype(str).str.strip() == cod_curso
                ]

    if df_curriculo_atual.empty or df_curriculo_novo.empty:
        return render(request, 'migracao.html', {
            'message': 'Não foi possível filtrar os currículos por curso para a comparação.',
            'alunos_options': alunos_options,
            'selected_id': selected_id,
            'aluno_nome': aluno_nome,
            'curriculo_atual': curriculo_atual_label,
            'curriculo_novo': DEFAULT_CURRICULO_VERSION,
            'resumo': {'total_atual': 0, 'total_novo': 0, 'reaproveitadas': 0, 'aproveitamento': 0},
            'disciplinas_reaproveitadas': [],
            'disciplinas_nao_reaproveitadas': [],
            'apenas_pendentes': apenas_pendentes,
            'mostrar_eletivas': mostrar_eletivas,
            'mostrar_optativas': mostrar_optativas,
            'mostrar_demais': mostrar_demais,
        })

    historico_concluido = build_historico_concluido(df_historico, selected_id)
    df_equivalencias = carregaEquivalencias()
    resultado_comparacao = compare_curriculos(df_curriculo_atual, df_curriculo_novo, historico_concluido, df_equivalencias)
    comparacao_filtrada = filtrar_resultado_comparacao(
        resultado_comparacao,
        apenas_obrigatorias=True,
        apenas_pendentes=apenas_pendentes,
        mostrar_eletivas=mostrar_eletivas,
        mostrar_optativas=mostrar_optativas,
        mostrar_demais=mostrar_demais,
    )

    resumo_total = resultado_comparacao['resumo']
    resumo_total = {
        'total_atual': resumo_total.get('total_atual', 0),
        'total_novo': resumo_total.get('total_novo', 0),
        'reaproveitadas': resumo_total.get('equivalencias_possiveis_grade', resumo_total.get('reaproveitadas', 0)),
        'aproveitamento': resumo_total.get('aproveitamento', 0),
        'aproveitadas_pelo_aluno': resumo_total.get('aproveitadas_pelo_aluno', 0),
        'aproveitamento_pelo_aluno': resumo_total.get('aproveitamento_pelo_aluno', 0),
    }

    total_filtrado = len(comparacao_filtrada['comparacao'])
    reaproveitadas_filtradas = len([
        item for item in comparacao_filtrada['comparacao'] if item.get('reaproveitada')
    ])
    aproveitadas_pelo_aluno_filtrado = len([
        item for item in comparacao_filtrada['comparacao'] if item.get('reaproveitada') and item.get('concluida')
    ])

    resumo_filtrado = {
        'total_atual': total_filtrado,
        'total_novo': resultado_comparacao['resumo']['total_novo'],
        'reaproveitadas': resumo_total['reaproveitadas'],
        'aproveitamento': resumo_total['aproveitamento'],
        'equivalencias_possiveis_grade': resumo_total['reaproveitadas'],
        'aproveitadas_pelo_aluno': resumo_total['aproveitadas_pelo_aluno'],
        'aproveitamento_pelo_aluno': resumo_total['aproveitamento_pelo_aluno'],
        'aproveitadas_pelo_aluno_filtrado': aproveitadas_pelo_aluno_filtrado,
    }

    return render(request, 'migracao.html', {
        'message': '',
        'alunos_options': alunos_options,
        'selected_id': selected_id,
        'aluno_nome': aluno_nome,
        'curriculo_atual': curriculo_atual_label,
        'curriculo_novo': DEFAULT_CURRICULO_VERSION,
        'resumo': resumo_filtrado,
        'disciplinas_reaproveitadas': comparacao_filtrada['disciplinas_reaproveitadas'],
        'disciplinas_nao_reaproveitadas': comparacao_filtrada['disciplinas_nao_reaproveitadas'],
        'comparacao_total': comparacao_filtrada['comparacao'],
        'apenas_pendentes': apenas_pendentes,
        'mostrar_eletivas': mostrar_eletivas,
        'mostrar_optativas': mostrar_optativas,
        'mostrar_demais': mostrar_demais,
    })