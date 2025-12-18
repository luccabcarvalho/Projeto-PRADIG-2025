from django.shortcuts import render
from django.conf import settings
import os
import pandas as pd
import plotly.graph_objects as go
import glob


USER_ID = 'user1'

def progressao_individual(request):
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
        return render(request, 'progressao_individual.html', {
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
        return render(request, 'progressao_individual.html', {
            'plot_div': '',
            'alunos_options': alunos_options,
            'selected_id': str(matr_aluno),
            'mensagem': mensagem,
        })

    status_aprovados = {
        'APV - Aprovado': '#006400',
        'APV- Aprovado': '#006400',
        'APV - Aprovado sem nota': '#32CD32',
    }
    status_excepcional = {
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
    cores_status = {**status_aprovados, **status_excepcional, **status_reprovados}

    # --- Equivalências ---
    def carregar_equivalencias():
        """Carrega e concatena todos os arquivos de equivalências em um único DataFrame."""
        equivalencias_dir = os.path.join(settings.BASE_DIR, 'visualizacoes', 'user_uploads', 'equivalencias_bsi')
        equivalencias_files = glob.glob(os.path.join(equivalencias_dir, '*.csv'))
        frames = [pd.read_csv(eq_file) for eq_file in equivalencias_files]
        if frames:
            return pd.concat(frames, ignore_index=True)
        return pd.DataFrame()

    def extrair_codigo(nome_disc):
        if pd.isna(nome_disc):
            return None
        return str(nome_disc).split(' - ')[0].strip()

    def construir_mapa_equivalencias(df_equivalencias):
        """Constrói o dicionário de equivalências: código novo -> código antigo."""
        if df_equivalencias.empty:
            return {}
        cod_novos = df_equivalencias['NOME_DISCIPLINA'].map(extrair_codigo)
        cod_antigos = df_equivalencias['NOME_DISC_EQUIV'].map(extrair_codigo)
        return {novo: antigo for novo, antigo in zip(cod_novos, cod_antigos) if novo and antigo}

    def processar_equivalencias_aluno(dados_aluno, equival_map, status_aprovados, status_excepcional):
        """Processa as equivalências para o aluno, ajustando cargas horárias e removendo linhas duplicadas."""
        dados_proc = dados_aluno.copy()
        # Identifica linhas de equivalência excepcional
        mask_excepcional = dados_proc['STATUS'].isin(status_excepcional.keys())
        if not mask_excepcional.any() or not equival_map:
            return dados_proc

        # Para cada linha excepcional, verifica se existe cursada equivalente aprovada
        cod_novos = dados_proc.loc[mask_excepcional, 'COD ATIV CURRIC'].map(extrair_codigo)
        indices_excepcionais = dados_proc.loc[mask_excepcional].index.tolist()
        cod_antigos = [equival_map.get(cod) for cod in cod_novos]

        # Mapeia: idx_cursada -> {'carga_total': ..., 'indices_excepcionais': [...]}
        equivalencias_por_cursada = {}
        for idx_excepcional, cod_antigo in zip(indices_excepcionais, cod_antigos):
            if not cod_antigo:
                continue
            # Busca índice da linha aprovada equivalente
            mask_cursada = (
                (dados_proc['COD ATIV CURRIC'].astype(str).str.strip() == cod_antigo)
                & (dados_proc['STATUS'].isin(status_aprovados.keys()))
            )
            idx_cursada_list = dados_proc[mask_cursada].index.tolist()
            if not idx_cursada_list:
                continue
            idx_cursada = idx_cursada_list[0]
            if idx_cursada not in equivalencias_por_cursada:
                equivalencias_por_cursada[idx_cursada] = {
                    'carga_total': 0,
                    'indices_excepcionais': []
                }
            equivalencias_por_cursada[idx_cursada]['carga_total'] += dados_proc.at[idx_excepcional, 'CARGA']
            equivalencias_por_cursada[idx_cursada]['indices_excepcionais'].append(idx_excepcional)

        # Atualiza linhas e remove duplicidades
        linhas_remover = set()
        novas_linhas = []
        for idx_cursada, info in equivalencias_por_cursada.items():
            linha_cursada = dados_proc.loc[idx_cursada].copy()
            nova_carga = info['carga_total']
            linha_cursada['CARGA'] = nova_carga
            linha_cursada['DISCIPLINA'] = (
                str(linha_cursada['COD ATIV CURRIC']) + ' - ' +
                linha_cursada['NOME ATIV CURRIC'] + ' (' +
                str(nova_carga) + 'h)'
            )
            novas_linhas.append((idx_cursada, linha_cursada))
            linhas_remover.add(idx_cursada)
            linhas_remover.update(info['indices_excepcionais'])

        dados_proc = dados_proc.drop(index=list(linhas_remover))
        for _, linha in novas_linhas:
            dados_proc = pd.concat([dados_proc, pd.DataFrame([linha])], ignore_index=True)
        return dados_proc

    # Execução do fluxo de equivalências
    df_equivalencias = carregar_equivalencias()
    equival_map = construir_mapa_equivalencias(df_equivalencias)
    dados_aluno = processar_equivalencias_aluno(dados_aluno, equival_map, status_aprovados, status_excepcional)

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
        return render(request, 'progressao_individual.html', {
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
    return render(request, 'progressao_individual.html', {
        'plot_div': plot_div,
        'alunos_options': alunos_options,
        'selected_id': str(matr_aluno), 
    })