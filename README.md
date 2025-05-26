# Projeto-PRADIG-2025

Este repositório reúne um conjunto de protótipos iniciais de visualizações de dados relacionados ao curso de Bacharelado em Sistemas de Informação (BSI). O objetivo é explorar diferentes formas de analisar e apresentar informações acadêmicas, como desempenho geral dos alunos, desempenho específico do aluno por carga horária, utilizando ferramentas modernas de visualização interativa.

## Visualizações Disponíveis

- **Desempenho Acadêmico por Aluno**  
  Local: `desempenhoAlunoPeriodo/graficoDesempenhoPeriodo.py`  
  Visualização interativa do progresso dos alunos ao longo dos períodos, com detalhamento de disciplinas aprovadas, reprovadas e carga horária acumulada.

- **Heatmap de Desempenho Acadêmico**  
  Local: `heatMaps/gerarGrafico.py`  
  Mapa de calor que mostra o status dos alunos em cada disciplina, facilitando a identificação de padrões de aprovação e reprovação.

## Instalação dos Pacotes Necessários

1. **Clone o repositório**:
   ```sh
   git clone <url-do-repositorio>
   cd Projeto-PRADIG-2025
   ```

2. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```

## Como Rodar as Visualizações

### 1. Desempenho Acadêmico por Aluno

No terminal, execute:
```sh
python desempenhoAlunoPeriodo/graficoDesempenhoPeriodo.py
```
O Dash abrirá um servidor local (por padrão em http://127.0.0.1:8050/) onde você poderá interagir com a visualização no navegador.

### 2. Heatmap de Desempenho Acadêmico

No terminal, execute:
```sh
python heatMaps/gerarGrafico.py
```
O Dash abrirá um servidor local (por padrão em http://127.0.0.1:8050/) para visualização do heatmap.

## Requisitos

Veja o arquivo [`requirements.txt`](requirements.txt) para a lista completa de dependências.

---

**Observação:** Os arquivos de dados necessários (CSV) já estão presentes na pasta `docs/`. Certifique-se de não alterar os nomes ou caminhos dos arquivos para garantir o funcionamento dos scripts.