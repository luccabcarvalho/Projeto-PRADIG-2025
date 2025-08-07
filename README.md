# Projeto-PRADIG-2025

Este repositório reúne um conjunto de protótipos iniciais de visualizações de dados relacionados ao curso de Bacharelado em Sistemas de Informação (BSI). O objetivo é explorar diferentes formas de analisar e apresentar informações acadêmicas, como desempenho geral dos alunos, desempenho específico do aluno por carga horária, utilizando ferramentas modernas de visualização interativa.


## Visualizações Disponíveis

O projeto oferece duas formas principais de visualização dos dados acadêmicos:

### Protótipos Dash (executáveis diretamente)

- **Desempenho Acadêmico por Aluno**  
  Local: `prototiposVisualizacoes/desempenhoAlunoPeriodo/graficoDesempenhoPeriodo.py`  
  Visualização interativa do progresso dos alunos ao longo dos períodos, detalhando disciplinas aprovadas, reprovadas e carga horária acumulada.

- **Heatmap de Desempenho Acadêmico**  
  Local: `prototiposVisualizacoes/heatMaps/gerarGrafico.py`  
  Mapa de calor que mostra o status dos alunos em cada disciplina, facilitando a identificação de padrões de aprovação e reprovação.

- **Status de Integralização dos Alunos**  
  Local: `prototiposVisualizacoes/statusAlunosIntegralizacao/statusAlunosIntegralizacao.py`  
  Visualização do progresso dos alunos em relação à integralização curricular, destacando prazos e situações acadêmicas.

- **Status de Integralização**  
  Local: `prototiposVisualizacoes/statusAlunosIntegralizacao/statusAlunosIntegralizacaoPerformance.py`  
  Versão otimizada para análise de desempenho do status de integralização.

### Sistema Web Django

O sistema web centraliza as visualizações em uma interface única e interativa:

- **Página Inicial**: Visão geral do sistema.
- **Hub de Visualizações**: Acesso rápido a todas as visualizações disponíveis.
- **Desempenho Acadêmico por Aluno**: `/visualizacoes/desempenho/`
- **Heatmap de Desempenho Acadêmico**: `/visualizacoes/heatmap/`
- **Status de Integralização**: `/visualizacoes/integralizacao/`

Todas as visualizações Django utilizam os dados da pasta `sistemaDeAnaliseAcademicaUnirio/visualizacoes/data/`.


## Instalação dos Pacotes Necessários

1. **Clone o repositório:**
   ```sh
   git clone <url-do-repositorio>
   cd Projeto-PRADIG-2025
   ```

2. **Crie e ative o ambiente virtual (opcional, mas recomendado):**
   ```sh
   python -m venv pradigEnv2025
   .\pradigEnv2025\Scripts\activate
   ```

3. **Instale as dependências:**
   ```sh
   pip install -r requirements.txt
   ```


## Como Rodar as Visualizações


### 1. Sistema Django

Se você nunca rodou uma aplicação Django, siga este passo a passo detalhado:

1. **Instale o Python (recomendado 3.10 ou superior):**
   - Baixe em: https://www.python.org/downloads/

2. **Verifique se o Python e o pip estão instalados:**
   ```sh
   python --version
   pip --version
   ```
   Ambos devem exibir a versão instalada.

3. **Instale o Django:**
   ```sh
   pip install django
   ```

4. **Acesse a pasta do sistema:**
   ```sh
   cd sistemaDeAnaliseAcademicaUnirio
   ```

5. **Execute as migrações do banco de dados (apenas na primeira vez):**
   ```sh
   ..\pradigEnv2025\Scripts\python.exe manage.py migrate
   ```

6. **Inicie o servidor de desenvolvimento:**
   ```sh
   ..\pradigEnv2025\Scripts\python.exe manage.py runserver
   ```

7. **Acesse no navegador:**
   - Página inicial: http://127.0.0.1:8000/visualizacoes/
   - Hub de visualizações: http://127.0.0.1:8000/visualizacoes/hub/
   - Desempenho Acadêmico: http://127.0.0.1:8000/visualizacoes/desempenho/
   - Heatmap: http://127.0.0.1:8000/visualizacoes/heatmap/
   - Status de Integralização: http://127.0.0.1:8000/visualizacoes/integralizacao/

**Dica:** Sempre ative o ambiente virtual antes de rodar os comandos acima, caso tenha criado um.


### 2. Protótipos Dash (execução direta)

No terminal, execute:

- **Desempenho Acadêmico por Aluno:**
  ```sh
  python prototiposVisualizacoes/desempenhoAlunoPeriodo/graficoDesempenhoPeriodo.py
  ```

- **Heatmap de Desempenho Acadêmico:**
  ```sh
  python prototiposVisualizacoes/heatMaps/gerarGrafico.py
  ```

- **Status de Integralização:**
  ```sh
  python prototiposVisualizacoes/statusAlunosIntegralizacao/statusAlunosIntegralizacao.py
  ```

- **Status de Integralização (Performance):**
  ```sh
  python prototiposVisualizacoes/statusAlunosIntegralizacao/statusAlunosIntegralizacaoPerformance.py
  ```

O Dash abrirá um servidor local (por padrão em http://127.0.0.1:8050/) para cada visualização.


## Requisitos

Veja o arquivo [`requirements.txt`](requirements.txt) para a lista completa de dependências.

---

**Observações:**

- Os arquivos de dados necessários (CSV) para os protótipos Dash estão em `prototiposVisualizacoes/docs/`.
- Para o sistema Django, os dados devem estar em `sistemaDeAnaliseAcademicaUnirio/visualizacoes/data/`.
- Certifique-se de não alterar os nomes ou caminhos dos arquivos para garantir o funcionamento dos scripts.