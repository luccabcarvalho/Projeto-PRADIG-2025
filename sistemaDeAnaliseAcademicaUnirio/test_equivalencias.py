"""
Script de teste para validar o sistema de equivalências de currículos.
Executar com: python test_equivalencias.py
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Adicionar o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistemaDeAnaliseAcademicaUnirio.settings')
import django
django.setup()

from samg.frontend.common import (
    carregaCurriculo,
    carregaEquivalencias,
    carregaBD,
    build_historico_concluido,
    compare_curriculos,
)


def test_equivalencias():
    """Testa o sistema de equivalências com um caso de uso real."""
    
    print("=" * 80)
    print("TESTE DO SISTEMA DE EQUIVALÊNCIAS DE CURRÍCULOS")
    print("=" * 80)
    
    # 1. Carregar equivalências
    print("\n1. Carregando arquivo de equivalências...")
    df_equivalencias = carregaEquivalencias()
    if df_equivalencias is None:
        print("   ❌ ERRO: Não foi possível carregar equivalências!")
        return False
    
    print(f"   ✓ Carregadas {len(df_equivalencias)} equivalências")
    print("\n   Primeiras 5 equivalências:")
    print(df_equivalencias.head().to_string(index=False))
    
    # 2. Carregar currículos
    print("\n2. Carregando currículos...")
    df_curr_2008 = carregaCurriculo('2008/1')
    df_curr_2023 = carregaCurriculo('2023/2')
    
    if df_curr_2008 is None or df_curr_2023 is None:
        print("   ❌ ERRO: Não foi possível carregar currículos!")
        return False
    
    print(f"   ✓ Currículo 2008/1: {len(df_curr_2008)} registros")
    print(f"   ✓ Currículo 2023/2: {len(df_curr_2023)} registros")
    
    # 3. Verificar exemplo específico do usuário
    print("\n3. Verificando exemplo específico: TIN0105 (2008/1) → TIN0223 (2023/2)")
    
    # Encontrar disciplina TIN0105 em 2008/1
    disc_2008 = df_curr_2008[df_curr_2008['COD DISCIPLINA'] == 'TIN0105'].iloc[0] if not df_curr_2008[df_curr_2008['COD DISCIPLINA'] == 'TIN0105'].empty else None
    
    if disc_2008 is not None:
        print(f"   Código: {disc_2008['COD DISCIPLINA']}")
        print(f"   Nome: {disc_2008['NOME DISCIPLINA']}")
        print(f"   Versão: {disc_2008['NUM VERSAO']}")
    else:
        print("   ❌ ERRO: TIN0105 não encontrado no currículo 2008/1!")
        return False
    
    # Encontrar disciplina TIN0223 em 2023/2
    disc_2023 = df_curr_2023[df_curr_2023['COD DISCIPLINA'] == 'TIN0223'].iloc[0] if not df_curr_2023[df_curr_2023['COD DISCIPLINA'] == 'TIN0223'].empty else None
    
    if disc_2023 is not None:
        print(f"   → Código: {disc_2023['COD DISCIPLINA']}")
        print(f"   → Nome: {disc_2023['NOME DISCIPLINA']}")
        print(f"   → Versão: {disc_2023['NUM VERSAO']}")
    else:
        print("   ❌ ERRO: TIN0223 não encontrado no currículo 2023/2!")
        return False
    
    # 4. Testar com aluno
    print("\n4. Testando com aluno real...")
    df_alunos, df_historico, erro = carregaBD()
    
    if erro:
        print(f"   ❌ ERRO: {erro}")
        return False
    
    # Selecionar primeiro aluno
    primeiro_aluno = df_alunos.iloc[0] if not df_alunos.empty else None
    if primeiro_aluno is None:
        print("   ❌ ERRO: Nenhum aluno encontrado!")
        return False
    
    matricula = str(primeiro_aluno.get('MATR ALUNO', '')).strip()
    nome_aluno = str(primeiro_aluno.get('NOME PESSOA', '')).strip()
    num_versao = str(primeiro_aluno.get('NUM VERSAO', '')).strip()
    
    print(f"   Aluno: {nome_aluno}")
    print(f"   Matrícula: {matricula}")
    print(f"   Currículo atual: {num_versao}")
    
    # 5. Executar comparação
    print("\n5. Executando comparação de currículos...")
    historico_concluido = build_historico_concluido(df_historico, matricula)
    resultado = compare_curriculos(df_curr_2008, df_curr_2023, historico_concluido, df_equivalencias)
    
    print(f"   Total de disciplinas no currículo atual: {resultado['resumo']['total_atual']}")
    print(f"   Total de disciplinas no currículo novo: {resultado['resumo']['total_novo']}")
    print(f"   Equivalências possíveis na grade: {resultado['resumo']['equivalencias_possiveis_grade']}")
    print(f"   Reaproveitadas pelo aluno: {resultado['resumo']['aproveitadas_pelo_aluno']}")
    print(f"   Aproveitamento: {resultado['resumo']['aproveitamento']}%")
    
    # 6. Verificar se TIN0105 foi mapeada corretamente
    print("\n6. Verificando mapeamento de TIN0105...")
    tin0105_items = [item for item in resultado['comparacao'] if item['codigo_atual'] == 'TIN0105']
    
    if tin0105_items:
        item = tin0105_items[0]
        print(f"   Código anterior: {item['codigo_atual']}")
        print(f"   Nome anterior: {item['nome_atual']}")
        
        if item['reaproveitada']:
            print(f"   ✓ Status: REAPROVEITÁVEL")
            print(f"   Código novo: {item['codigo_novo']}")
            print(f"   Nome novo: {item['nome_novo']}")
            
            if item['codigo_novo'] == 'TIN0223':
                print(f"\n   ✅ SUCESSO: TIN0105 foi mapeada para TIN0223 corretamente!")
                return True
            else:
                print(f"\n   ⚠️ AVISO: TIN0105 foi mapeada para {item['codigo_novo']}, esperado TIN0223")
                return False
        else:
            print(f"   ❌ ERRO: TIN0105 não foi mapeada como reaproveitável!")
            return False
    else:
        print(f"   ❌ ERRO: TIN0105 não encontrada na comparação!")
        return False


if __name__ == '__main__':
    sucesso = test_equivalencias()
    print("\n" + "=" * 80)
    if sucesso:
        print("✅ TODOS OS TESTES PASSARAM")
    else:
        print("❌ TESTES FALHARAM")
    print("=" * 80)
    
    sys.exit(0 if sucesso else 1)
