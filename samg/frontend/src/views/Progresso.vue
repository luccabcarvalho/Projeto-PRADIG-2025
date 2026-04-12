<template>
  <v-container fluid class="progresso">
    <v-row justify="center">
      <strong class="warning text-h5 text-center">
        AVISO: Este simulador é informativo. Leia os anexos oficiais para mais detalhes.
      </strong>
    </v-row>

    <v-row v-if="loading" class="fill-screen" align: center justify="center">
      <v-col cols="auto" class="text-center">
        <v-progress-circular class="progresso-loading-spinner" indeterminate color="primary" size="32" width="5" />
        <div class="text-caption mt-3">Carregando progresso...</div>
      </v-col>
    </v-row>
  
    <v-row v-else justify="center">
      <v-col cols="12" md="10">
        <v-alert v-if="!user" type="info" border: left class="mb-4">Faça login para ver seu histórico e progresso automaticamente.</v-alert>
        <v-alert v-if="message" type="info" border: left class="mb-4">{{ message }}</v-alert>
        
        <div v-if="curriculoGrade.length && user" class="text-center my-6">
          <h2 class="mb-2">Grade Curricular</h2>
          <p v-if="user.matricula && curriculoVersion" class="text-caption mb-6">
            Matrícula: {{ user.matricula }} | Currículo: v{{ curriculoVersion }}
          </p>

          <v-row class="mb-4" justify="center">
            <v-col cols="6" sm="3">
              <v-card variant="outlined" class="pa-3 text-center">
                <div class="text-caption">Obrigatórias</div>
                <div class="text-h6 font-weight-bold">{{ curriculoStats.total }}</div>
              </v-card>
            </v-col>
            <v-col cols="6" sm="3">
              <v-card variant="outlined" class="pa-3 text-center">
                <div class="text-caption">Concluídas</div>
                <div class="text-h6 font-weight-bold text-success">{{ curriculoStats.vencidas }}</div>
              </v-card>
            </v-col>
            <v-col cols="6" sm="3">
              <v-card variant="outlined" class="pa-3 text-center">
                <div class="text-caption">Restantes</div>
                <div class="text-h6 font-weight-bold text-warning">{{ curriculoStats.pendentes }}</div>
              </v-card>
            </v-col>
            <v-col cols="6" sm="3">
              <v-card variant="outlined" class="pa-3 text-center">
                <div class="text-caption">Progresso</div>
                <div class="text-h6 font-weight-bold">{{ curriculoStats.percentual }}%</div>
              </v-card>
            </v-col>
          </v-row>

          <v-row justify="center" class="mb-2">
            <v-col cols="12" sm="auto" class="d-flex justify-center">
              <v-switch
                v-model="showOnlyPendentes"
                color="warning"
                hide-details
                inset
                label="Mostrar apenas pendentes"
              />
            </v-col>
            <v-col cols="12" sm="auto" class="d-flex justify-center">
              <v-switch
                v-model="showOnlyObrigatorias"
                color="primary"
                hide-details
                inset
                label="Mostrar apenas obrigatórias"
              />
            </v-col>
          </v-row>
          
          <v-row class="mt-6" justify="center">
            <v-col v-for="(periodo, idx) in filteredCurriculoGrade" :key="'periodo-'+idx" cols="12" md="6" lg="4" class="pa-4">
              <v-card class="elevation-4 periodo-card" style="min-height: 100%;">
                <v-card-title class="text-center" style="background-color: #2356a8;">
                  <div class="w-100">
                    <span class="text-h6 d-block periodo-card-title-text">{{ periodo.periodo }} período</span>
                    <span class="text-caption periodo-card-title-text">{{ periodo.vencidas }}/{{ periodo.total }} obrigatórias concluídas</span>
                  </div>
                </v-card-title>
                
                <v-card-text class="pa-4">
                  <v-progress-linear
                    :model-value="periodo.percentual"
                    color="success"
                    height="8"
                    rounded
                    class="mb-4"
                  />
                  <div
                    v-for="disc in periodo.disciplinas"
                    :key="disc.codigo"
                    class="mb-3 d-flex align-center gap-2"
                    :class="{ 'disc-nao-obrigatoria': !disc.obrigatoria }"
                  >
                    <v-btn
                      :color="statusColor(disc.status)"
                      :text-color="statusTextColor(disc.status)"
                      size="small"
                      class="flex-shrink-0"
                      style="min-width: 80px; font-weight: 600;"
                      :title="`${disc.codigo} - ${disc.nome}\nStatus: ${disc.status}`"
                    >
                      {{ sigla(disc.nome) }}
                    </v-btn>
                    <span class="text-caption flex-grow-1 text-left">{{ disc.nome }}</span>
                  </div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <v-row justify="center" class="mt-8">
            <v-col cols="auto">
              <div class="d-flex align-center gap-4">
                <div class="d-flex align-center gap-2">
                  <v-btn color="success" small disabled style="min-width: 60px;"></v-btn>
                  <span class="text-caption font-weight-600">Aprovado</span>
                </div>
                <div class="d-flex align-center gap-2">
                  <v-btn color="grey-lighten-2" small disabled style="min-width: 60px;"></v-btn>
                  <span class="text-caption font-weight-600">Não Cursado</span>
                </div>
                <div class="d-flex align-center gap-2">
                  <v-btn color="info" small disabled style="min-width: 60px;"></v-btn>
                  <span class="text-caption font-weight-600">Cursando</span>
                </div>
              </div>
            </v-col>
          </v-row>
        </div>

        <div v-else-if="user && !curriculoGrade.length" class="mt-6 text-center">
          <v-alert type="warning" border: left>
            Não foi possível carregar o currículo. Verifique sua matrícula ou tente fazer upload do histórico escolar.
          </v-alert>
        </div>
      </v-col>
    </v-row>
  </v-container>
</template>



<script>
import axios from "axios";
import instance from "@/api/instance";

// Importa todos os CSVs de docs e subpastas
const csvDocs = import.meta.glob('@docs/**/*.csv', { query: '?raw', import: 'default', eager: true });
function getCsvDocsDisponiveis() {
  const csvDisponiveis = {};
  for (const path in csvDocs) {
    // Extrai o nome do arquivo sem extensão
    const nome = path.split('/').pop().replace(/\.csv$/i, '');
    csvDisponiveis[nome] = csvDocs[path];
  }
  return csvDisponiveis;
}

const csvDisponiveis = getCsvDocsDisponiveis();
const historicoCsv = csvDisponiveis.HistoricoEscolarSimplificado || '';

export default {
  data() {
    return {
      grade: [],
      user: null,
      message: null,
      periodList: [],
      curriculoVersion: null,
      curriculoGrade: [],
      showOnlyPendentes: false,
      showOnlyObrigatorias: false,
      loading: true,
    };
  },
  computed: {
    curriculoStats() {
      const disciplinas = this.curriculoGrade
        .flatMap(p => p.disciplinas || [])
        .filter(d => d.obrigatoria);
      const total = disciplinas.length;
      const vencidas = disciplinas.filter(d => d.status === 'Vencido').length;
      const pendentes = Math.max(total - vencidas, 0);
      const percentual = total ? Math.round((vencidas / total) * 100) : 0;
      return { total, vencidas, pendentes, percentual };
    },
    filteredCurriculoGrade() {
      const order = {
        'Não Vencido': 0,
        'Matricula/Cursando': 1,
        'Vencido': 2,
      };

      return this.curriculoGrade
        .map((periodo) => {
          const disciplinasOrdenadas = [...(periodo.disciplinas || [])].sort((a, b) => {
            if (a.obrigatoria !== b.obrigatoria) return a.obrigatoria ? -1 : 1;
            const ao = order[a.status] ?? 99;
            const bo = order[b.status] ?? 99;
            if (ao !== bo) return ao - bo;
            return (a.nome || '').localeCompare(b.nome || '');
          });

          let disciplinas = disciplinasOrdenadas;
          if (this.showOnlyPendentes) disciplinas = disciplinas.filter(d => d.status !== 'Vencido');
          if (this.showOnlyObrigatorias) disciplinas = disciplinas.filter(d => d.obrigatoria);

          const obrigatoriasPeriodo = (periodo.disciplinas || []).filter(d => d.obrigatoria);
          const total = obrigatoriasPeriodo.length;
          const vencidas = obrigatoriasPeriodo.filter(d => d.status === 'Vencido').length;
          const percentual = total ? Math.round((vencidas / total) * 100) : 0;

          return {
            periodo: periodo.periodo,
            disciplinas,
            total,
            vencidas,
            percentual,
          };
        })
        .filter(p => p.disciplinas.length > 0);
    },
  },
  methods: {
    async yieldToUI() {
      await new Promise((resolve) => setTimeout(resolve, 0));
    },
    loadUser() {
      try {
        const raw = localStorage.getItem('samg_user');
        this.user = raw ? JSON.parse(raw) : null;
      } catch (e) {
        this.user = null;
      }
    },


    extrairVersaoCurriculoHistorico(text, matricula = null) {
      const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return null;

      const header = this.splitLinhaCsv(lines[0]).map(h =>
        String(h || '')
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '')
          .toLowerCase()
          .trim()
      );

      const idxOf = (names) => {
        for (const n of names) {
          const i = header.findIndex(h => h.includes(n));
          if (i >= 0) return i;
        }
        return -1;
      };

      const idxVersao = idxOf(['num versao', 'num_versao', 'versao curriculo', 'versao']);
      const idxMatricula = idxOf(['matr aluno', 'matr_aluno', 'matricula']);
      if (idxVersao < 0) return null;

      const freq = new Map();
      for (let i = 1; i < lines.length; i++) {
        const cols = this.splitLinhaCsv(lines[i]);

        if (matricula && idxMatricula >= 0) {
          const rowMat = String(cols[idxMatricula] || '').trim();
          if (String(rowMat) !== String(matricula)) continue;
        }

        const raw = String(cols[idxVersao] || '').trim();
        const versao = raw.replace(/\D/g, '');
        if (!versao) continue;
        freq.set(versao, (freq.get(versao) || 0) + 1);
      }

      if (!freq.size) return null;
      return [...freq.entries()]
        .sort((a, b) => (b[1] - a[1]) || (parseInt(b[0], 10) - parseInt(a[0], 10)))[0][0];
    },

    async loadHistoricoForUser() {
      this.loading = true;
      await this.$nextTick();
      await this.yieldToUI();
      try {
        if (!this.user || !this.user.matricula) {
          this.grade = [];
          this.curriculoGrade = [];
          this.message = null;
          return;
        }

        const text = historicoCsv;
        const matricula = String(this.user.matricula);
        const curriculoYear = this.extrairVersaoCurriculoHistorico(text, matricula);
        const disciplinas = await this.parseHistoricoCsv(text, matricula);
        
        if (!disciplinas.length) {
          this.message = 'Nenhum histórico encontrado para a matrícula ' + this.user.matricula;
          this.grade = [];
          this.curriculoGrade = [];
          return;
        }

        if (!curriculoYear) {
          this.message = 'Não foi possível identificar a versão do currículo (NUM VERSAO) no histórico.';
          this.curriculoGrade = [];
          return;
        }
        
        this.grade = await this.organizarPorPeriodo(disciplinas);
        this.periodList = this.grade.map(p => p.periodo);
        
        if (curriculoYear) {
          const curriculoRaw = this.getCurriculoPorAno(curriculoYear);
          if (curriculoRaw) {
            const currList = await this.parseCurriculoCsv(curriculoRaw.text);
            this.curriculoVersion = curriculoRaw.ver;
            this.curriculoGrade = await this.buildCurriculoProgresso(currList, disciplinas);
          } else {
            this.curriculoGrade = [];
          }
        }
        this.message = null; 
      } catch (err) {
        this.message = 'Erro ao carregar histórico';
        this.curriculoGrade = [];
      } finally {
        this.loading = false;
      }
    },

    onSamgUserChanged(e) {
      this.loadUser();
      this.loadHistoricoForUser();
    },
    statusColor(status) {
      if (status === 'Vencido') return 'success';
      if (status === 'Matricula/Cursando') return 'info';
      return 'grey-lighten-2';
    },
    statusTextColor(status) {
      if (status === 'Vencido' || status === 'Matricula/Cursando') return 'white';
      return 'black';
    },
    normalizarTipoCategoria(tipo) {
      const normalized = String(tipo || '')
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim();

      if (normalized.includes('obrig')) return 'obrigatoria';
      if (normalized.includes('elet')) return 'eletiva';
      if (normalized.includes('optat')) return 'optativa';
      if (normalized.includes('complement')) return 'complementar';
      return 'outros';
    },
    tipoCategoriaLabel(tipoCategoria) {
      const map = {
        obrigatoria: 'Obrigatória',
        eletiva: 'Eletiva',
        optativa: 'Optativa',
        complementar: 'Complementar',
        outros: 'Outros',
      };
      return map[tipoCategoria] || 'Outros';
    },
    sigla(nome) {
      if (!nome || typeof nome !== 'string') return '';
      let s = nome
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/[^A-Za-z0-9\s]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

      if (!s) return '';

      const stop = new Set([
        'de','da','do','das','dos','e','em','para','por','a','o','os','as',
        'ao','aos','na','no','nas','nos','um','uma','com','ou'
      ]);

      const tokens = s.split(/\s+/);
      const initials = [];
      const numerals = [];
      const romanRe = /^(?=[MDCLXVI]+$)M{0,4}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3})$/i;
      for (const t of tokens) {
        const lower = t.toLowerCase();
        if (stop.has(lower)) continue;
        if (romanRe.test(t)) {
          numerals.push(t.toUpperCase());
        } else if (/^\d+$/.test(t)) {
          initials.push(t[0]);
        } else {
          initials.push(t[0].toUpperCase());
        }
      }

      let base = initials.join('');
      if (!base && numerals.length) {
        return numerals.join(' ');
      }
      if (!base) {
        base = s.replace(/\s+/g, '').slice(0, 3).toUpperCase();
      }
      base = base.slice(0, 3);
      if (numerals.length) return `${base} ${numerals.join(' ')}`;
      return base;
    },
    async uploadPdf(event) {
      const file = event.target.files[0];
      if (!file) return;
      const name = (file.name || '').toLowerCase();
      if (name.endsWith('.csv') || file.type === 'text/csv') {
        try {
          const text = await this._readFileAsText(file);
          const disciplinas = await this.parseHistoricoCsv(text);
          this.grade = await this.organizarPorPeriodo(disciplinas);
        } catch (e) {
          alert('Erro ao processar CSV');
          this.grade = [];
        }
        return;
      }
    },
    _readFileAsText(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || ''));
        reader.onerror = reject;
        reader.readAsText(file, 'utf-8');
      });
    },

    splitLinhaCsv(line) {
      const cols = line.split(/,(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)/);
      return cols.map(c => {
        let v = c.trim();
        if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1).replace(/""/g, '"');
        return v;
      });
    },

    async parseHistoricoCsv(text, matricula = null) {
      const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return [];
      const header = this.splitLinhaCsv(lines[0]).map(h => h.toLowerCase());

      const idxOf = (names) => {
        for (const n of names) {
          const i = header.findIndex(h => h.includes(n));
          if (i >= 0) return i;
        }
        return -1;
      };

      const idxCodigo = idxOf(['cod ativ curric', 'cod ativ', 'codigo', 'cod']);
      const idxNome = idxOf(['nome ativ curric', 'nome ativ', 'nome ativ curric', 'nome ativ curric']);
      const idxSituacao = idxOf(['descr situacao', 'situacao', 'descr situacao']);
      const idxPeriodo = idxOf(['periodo']);
      const idxAno = idxOf(['ano']);
      const idxMatricula = idxOf(['matr aluno', 'matr_aluno', 'matricula', 'matr aluno']);

      const rows = [];
      for (let i = 1; i < lines.length; i++) {
        if (i % 500 === 0) await this.yieldToUI();
        const cols = this.splitLinhaCsv(lines[i]);
        if (matricula && idxMatricula >= 0) {
          const rowMat = (cols[idxMatricula] || '').trim();
          if (String(rowMat) !== String(matricula)) continue;
        }

        const codigo = idxCodigo >= 0 ? (cols[idxCodigo] || '').trim() : null;
        if (!codigo) continue;
        const nome = idxNome >= 0 ? (cols[idxNome] || '').trim() : '';
        const situacaoRaw = idxSituacao >= 0 ? (cols[idxSituacao] || '').trim() : '';
        const periodoRaw = idxPeriodo >= 0 ? (cols[idxPeriodo] || '').trim() : '';
        const anoRaw = idxAno >= 0 ? (cols[idxAno] || '').trim() : '';
        let periodo = 'Não informado';
        const rawPeriodo = (periodoRaw || '').trim();
        const matchNum = rawPeriodo.match(/(\d+)/);
        if (matchNum) {
          periodo = `${parseInt(matchNum[1], 10)}°`;
        } else if (rawPeriodo) {
          periodo = rawPeriodo;
        }

        rows.push({ codigo, nome, situacaoRaw, periodo, ano: parseInt(anoRaw, 10) || null });
      }
      const byCodePeriod = new Map();
      for (let i = 0; i < rows.length; i++) {
        if (i % 500 === 0) await this.yieldToUI();
        const r = rows[i];
        const key = `${r.codigo}|${r.periodo}`;
        const exist = byCodePeriod.get(key);
        if (!exist) {
          byCodePeriod.set(key, r);
          continue;
        }
        const situAprovado = str => /apv|aprovad/i.test(str || '');
        if (situAprovado(r.situacaoRaw) && !situAprovado(exist.situacaoRaw)) {
          byCodePeriod.set(key, r);
          continue;
        }
        if ((r.ano || 0) > (exist.ano || 0)) {
          byCodePeriod.set(key, r);
        }
      }

      const mapSituacao = (raw) => {
        if (!raw) return 'Não Vencido';
        if (/apv|aprovad/i.test(raw)) return 'Vencido';
        if (/matr|matr[ií]cula|matricula/i.test(raw)) return 'Matricula/Cursando';
        return 'Não Vencido';
      };

      const out = [];
      let outIndex = 0;
      for (const [key, r] of byCodePeriod.entries()) {
        outIndex++;
        if (outIndex % 500 === 0) await this.yieldToUI();
        out.push({ codigo: r.codigo.trim(), nome: r.nome || r.codigo.trim(), situacao: mapSituacao(r.situacaoRaw), periodo: r.periodo });
      }
      
      return out;
    },

    getCurriculoPorAno(ano) {
      const curriculosDisponiveis = Object.entries(csvDisponiveis).reduce((acc, [nomeArquivo, text]) => {
        const match = nomeArquivo.match(/^curriculo-?(\d+)$/i);
        if (!match) return acc;
        const ver = match[1];
        acc[ver] = { text, ver };
        return acc;
      }, {});
      
      if (!Object.keys(curriculosDisponiveis).length) {
        console.error('Nenhum currículo disponível');
        return null;
      }

      if (curriculosDisponiveis[ano]) {
        return curriculosDisponiveis[ano];
      }
      const yearNum = parseInt(ano, 10);
      const disponiveisOrdenados = Object.keys(curriculosDisponiveis)
        .map(k => ({ year: k, num: parseInt(k, 10) }))
        .filter(k => k.num <= yearNum)
        .sort((a, b) => b.num - a.num);
      
      if (disponiveisOrdenados.length > 0) {
        const melhorOpcao = disponiveisOrdenados[0].year;
        return curriculosDisponiveis[melhorOpcao];
      }
      const todosOrdenados = Object.keys(curriculosDisponiveis)
        .map(k => ({ year: k, num: parseInt(k, 10) }))
        .sort((a, b) => b.num - a.num);
      
      if (todosOrdenados.length > 0) {
        const ultimoRecurso = todosOrdenados[0].year;
        return curriculosDisponiveis[ultimoRecurso];
      }
      
      console.error('Nenhum currículo disponível');
      return null;
    },

    getUltimoCurriculo() {
      const candidates = Object.keys(csvDisponiveis).filter(nome => /^curriculo-?(\d+)$/i.test(nome));
      if (!candidates.length) return null;

      let best = null;
      let bestNum = -Infinity;
      for (const nome of candidates) {
        const m = nome.match(/^curriculo-?(\d+)$/i);
        if (!m) continue;
        const num = parseInt(m[1], 10);
        if (num > bestNum) { bestNum = num; best = nome; }
      }
      if (!best) return null;
      const text = csvDisponiveis[best];
      const ver = best.match(/^curriculo-?(\d+)$/i)?.[1] || best;
      return { text, ver };
    },

    async parseCurriculoCsv(text) {
      const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return [];
      const header = this.splitLinhaCsv(lines[0]).map(h => h.toLowerCase());

      const idxOf = (names) => {
        for (const n of names) {
          const i = header.findIndex(h => h.includes(n));
          if (i >= 0) return i;
        }
        return -1;
      };

      const idxCod = idxOf(['cod disciplina','cod_disciplina','cod disciplina','cod ativ curric','cod ativ']);
      const idxNome = idxOf(['nome disciplina','nome_disciplina','nome disciplina','nome ativ curric','nome ativ']);
      const idxPeriodo = idxOf(['periodo ideal','periodo_ideal','semestre ideal','semestre_ideal','periodo']);
      const idxCred = idxOf(['creditos','creditos']);
      const idxTipo = idxOf(['tipo disciplina','tipo','tipo_disciplina']);

      const dedup = new Map();
      
      for (let i = 1; i < lines.length; i++) {
        if (i % 500 === 0) await this.yieldToUI();
        const cols = this.splitLinhaCsv(lines[i]);
        const codigo = idxCod >= 0 ? (cols[idxCod] || '').trim() : null;
        if (!codigo) continue;
        
        const codUpper = codigo.toUpperCase();
        if (dedup.has(codUpper)) continue;
        
        const nome = idxNome >= 0 ? (cols[idxNome] || '').trim() : '';
        const rawPeriodo = idxPeriodo >= 0 ? (cols[idxPeriodo] || '').trim() : '';
        let periodo = 'Não informado';
        const matchNum = rawPeriodo.match(/(\d+)/);
        if (matchNum) periodo = `${parseInt(matchNum[1],10)}°`;
        else if (rawPeriodo) periodo = rawPeriodo;
        const creditos = idxCred >= 0 ? parseFloat((cols[idxCred] || '').replace(',', '.')) || null : null;
        const tipo = idxTipo >= 0 ? (cols[idxTipo] || '').trim() : null;
        const tipoCategoria = this.normalizarTipoCategoria(tipo);

        dedup.set(codUpper, {
          codigo: codUpper,
          nome,
          periodo,
          creditos,
          tipo,
          tipoCategoria,
          tipoLabel: this.tipoCategoriaLabel(tipoCategoria),
          obrigatoria: tipoCategoria === 'obrigatoria',
        });
      }

      const out = Array.from(dedup.values());
      return out;
    },

    async buildCurriculoProgresso(curriculoList, userDisciplinas) {
      const statusByCode = {};
      for (let i = 0; i < userDisciplinas.length; i++) {
        if (i % 500 === 0) await this.yieldToUI();
        const d = userDisciplinas[i];
        const cod = (d.codigo || '').toUpperCase();
        statusByCode[cod] = d.situacao || 'Não Vencido';
      }

      const periodMap = {};
      for (let i = 0; i < curriculoList.length; i++) {
        if (i % 500 === 0) await this.yieldToUI();
        const c = curriculoList[i];
        const periodo = c.periodo || 'Não informado';
        if (!periodMap[periodo]) periodMap[periodo] = [];
        
        const codUpper = (c.codigo || '').toUpperCase();
        const status = statusByCode[codUpper] || 'Não Vencido';
        
        periodMap[periodo].push({ 
          codigo: c.codigo, 
          nome: c.nome, 
          creditos: c.creditos, 
          tipo: c.tipo,
          tipoCategoria: c.tipoCategoria,
          tipoLabel: c.tipoLabel,
          obrigatoria: c.obrigatoria,
          status 
        });
      }

      return Object.keys(periodMap)
        .sort((a,b) => {
          if (a === 'Optativas/Complementares') return 1;
          if (b === 'Optativas/Complementares') return -1;
          const ma = (a||'').match(/\d+/); 
          const mb = (b||'').match(/\d+/);
          if (ma && mb) return parseInt(ma[0],10) - parseInt(mb[0],10);
          if (ma) return -1;
          if (mb) return 1;
          return a.localeCompare(b);
        })
        .map(p => ({ periodo: p, disciplinas: periodMap[p] }));
    },

    async organizarPorPeriodo(disciplinas) {
      const periodos = {};
      for (let i = 0; i < disciplinas.length; i++) {
        if (i % 500 === 0) await this.yieldToUI();
        const disc = disciplinas[i];
        const periodo = disc.periodo !== undefined && disc.periodo !== null
          ? disc.periodo
          : "Não informado";
        if (!periodos[periodo]) periodos[periodo] = [];
        periodos[periodo].push(disc);
      }
      return Object.keys(periodos)
        .sort((a, b) => {
          const ma = (a || '').match(/\d+/);
          const mb = (b || '').match(/\d+/);
          if (ma && mb) return parseInt(ma[0], 10) - parseInt(mb[0], 10);
          if (ma) return -1;
          if (mb) return 1;
          return a.localeCompare(b);
        })
        .map((periodo) => ({
          periodo,
          disciplinas: periodos[periodo],
        }));
    },

  },
  mounted() {
    this.loadUser();
    this.loadHistoricoForUser();
    window.addEventListener('samg_user_changed', this.onSamgUserChanged);
  },
  beforeUnmount() {
    window.removeEventListener('samg_user_changed', this.onSamgUserChanged);
  }
};
</script>
<style lang="css" scoped>
.progresso {
  min-width: 50vw;
  margin-bottom: 24px;
}

.warning {
  color: #ef5350;
}

.fill-screen {
  min-height: calc(100vh - 120px);
}

:deep(.progresso-loading-spinner.v-progress-circular--indeterminate) {
  animation: progress-circular-rotate 1.4s linear infinite !important;
}

:deep(.progresso-loading-spinner.v-progress-circular--indeterminate .v-progress-circular__overlay) {
  animation: progress-circular-dash 1.4s ease-in-out infinite !important;
}

.periodo-card {
  border-top: 4px solid #2356a8;
}

.gap-2 {
  gap: 8px;
}

.gap-4 {
  gap: 16px;
}

.text-left {
  text-align: left;
}

.disc-nao-obrigatoria {
  opacity: 0.75;
}

.bg-light-blue {
  background-color: #e3f2fd;
}

.periodo-card-title-text {
  color: #fff;
}
</style>