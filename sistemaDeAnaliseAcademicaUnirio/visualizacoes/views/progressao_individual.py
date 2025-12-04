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
    equivalencias_dir = os.path.join(settings.BASE_DIR, 'visualizacoes', 'user_uploads', 'equivalencias_bsi')
    equivalencias_files = glob.glob(os.path.join(equivalencias_dir, '*.csv'))
    equivalencias = []
    for eq_file in equivalencias_files:
        df_eq = pd.read_csv(eq_file)
        equivalencias.append(df_eq)
    if equivalencias:
        df_equivalencias = pd.concat(equivalencias, ignore_index=True)
    else:
        df_equivalencias = pd.DataFrame()

    # Mapeamento: código novo (currículo novo) -> código antigo (currículo antigo)
    def extrair_codigo(nome_disc):
        if pd.isna(nome_disc):
            return None
        return nome_disc.split(' - ')[0].strip()

    equival_map = {}
    if not df_equivalencias.empty:
        for _, row in df_equivalencias.iterrows():
            cod_novo = extrair_codigo(row.get('NOME_DISCIPLINA', ''))
            cod_antigo = extrair_codigo(row.get('NOME_DISC_EQUIV', ''))
            if cod_novo and cod_antigo:
                equival_map[cod_novo] = cod_antigo

    # Processar status_excepcional: para cada disciplina com status_excepcional, se houver equivalente cursada, substituir
    dados_aluno_proc = dados_aluno.copy()
    linhas_remover = []
    novas_linhas = []
    for idx, row in dados_aluno.iterrows():
        status = row['STATUS']
        if status in status_excepcional:
            cod_novo = extrair_codigo(row['COD ATIV CURRIC'])
            cod_antigo = equival_map.get(cod_novo)
            if cod_antigo:
                # Procurar se o aluno cursou a disciplina equivalente (antiga)
                mask_cursada = (
                    (dados_aluno['COD ATIV CURRIC'].astype(str).str.strip() == cod_antigo)
                    & (dados_aluno['STATUS'].isin(status_aprovados.keys()))
                )
                if mask_cursada.any():
                    idx_cursada = dados_aluno[mask_cursada].index[0]
                    # Substituir a linha da cursada pela da equivalente, mas mantendo o período da cursada
                    linha_cursada = dados_aluno.loc[idx_cursada].copy()
                    linha_cursada['COD ATIV CURRIC'] = cod_novo
                    linha_cursada['NOME ATIV CURRIC'] = row['NOME ATIV CURRIC']
                    linha_cursada['CARGA'] = row['CARGA']
                    linha_cursada['DISCIPLINA'] = row['DISCIPLINA']
                    # Atualiza status para o da cursada (aprovado)
                    # linha_cursada['STATUS'] = linha_cursada['STATUS']
                    novas_linhas.append((idx_cursada, linha_cursada))
                    # Marcar para remover a linha da cursada e a da excepcional
                    linhas_remover.extend([idx_cursada, idx])
    # Remover duplicidades
    linhas_remover = list(set(linhas_remover))
    dados_aluno_proc = dados_aluno_proc.drop(index=linhas_remover)
    # Adicionar as linhas substituídas
    for idx_cursada, linha in novas_linhas:
        dados_aluno_proc = pd.concat([dados_aluno_proc, pd.DataFrame([linha])], ignore_index=True)
    # Atualizar dados_aluno para o processamento do gráfico
    dados_aluno = dados_aluno_proc

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