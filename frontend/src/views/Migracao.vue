<template>
  <v-container fluid class="historico">
    <v-row justify="center">
      <strong class="warning text-h5 text-center">
        AVISO: Este simulador é informativo. Leia os anexos oficiais para mais detalhes.
      </strong>
    </v-row>

    <v-row justify="center">
      <v-col cols="12" md="10">
        <v-alert v-if="!isLogado" type="info" border="left" class="mb-4">
          Faça login para ver sua migração curricular automaticamente.
        </v-alert>
        <v-alert v-if="message" type="info" border="left" class="mb-4">{{ message }}</v-alert>
      </v-col>
    </v-row>

    <v-row justify="center" v-if="user && grade.length">
      <v-col cols="12" md="10">
        <div class="text-center my-4">
          <h2 class="mb-2">Migração Curricular</h2>
          <p class="text-caption mb-4" v-if="user.matricula">
            Matrícula: {{ user.matricula }} | Currículo atual: v{{ curriculoAtual || '-' }} | Currículo novo: v{{ curriculoNovo || '-' }}
          </p>
        </div>

        <v-row class="mb-4" justify="center">
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-caption">Obrigatórias (novo)</div>
              <div class="text-h6 font-weight-bold">{{ migracaoStats.total }}</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-caption">Concluídas</div>
              <div class="text-h6 font-weight-bold text-success">{{ migracaoStats.vencidas }}</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-caption">Por equivalência</div>
              <div class="text-h6 font-weight-bold">{{ migracaoStats.equivalencias }}</div>
            </v-card>
          </v-col>
          <v-col cols="6" sm="3">
            <v-card variant="outlined" class="pa-3 text-center">
              <div class="text-caption">Pendentes</div>
              <div class="text-h6 font-weight-bold text-warning">{{ migracaoStats.pendentes }}</div>
            </v-card>
          </v-col>
        </v-row>

        <v-row class="mt-6" justify="center">
          <v-col v-for="(periodo, idx) in grade" :key="idx" cols="12" md="6" lg="4" class="pa-4">
            <v-card class="elevation-4 periodo-card" style="min-height: 100%;">
              <v-card-title class="text-center bg-light-blue" style="background-color: #e3f2fd;">
                <div class="w-100">
                  <span class="text-h6 d-block">{{ periodo.periodo }}º período</span>
                  <span class="text-caption">{{ periodo.vencidas }}/{{ periodo.total }} concluídas</span>
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
                  v-for="disciplina in periodo.disciplinas"
                  :key="disciplina.codigo"
                  class="mb-3 d-flex align-center gap-2"
                >
                  <v-btn
                    :color="disciplina.situacao === 'Vencido' ? 'success' : 'grey-lighten-2'"
                    :text-color="disciplina.situacao === 'Vencido' ? 'white' : 'black'"
                    size="small"
                    class="flex-shrink-0"
                    style="min-width: 80px; font-weight: 600;"
                    :title="`${disciplina.codigo} - ${disciplina.nome}`"
                  >
                    {{ sigla(disciplina.nome) }}
                  </v-btn>

                  <div class="d-flex flex-column text-left flex-grow-1">
                    <span class="text-caption">{{ disciplina.nome }}</span>
                    <span
                      v-if="disciplina.origem === 'equivalencia'"
                      class="text-caption text-info"
                    >
                      Equivalência: {{ disciplina.equivalenciasConcluidas.join(', ') }}
                    </span>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <v-row v-else-if="user" class="mt-8" justify="center">
      <em>Não foi possível montar a migração com os dados atuais.</em>
    </v-row>
  </v-container>
</template>

<script>
const csvDocs = import.meta.glob('../docs/**/*.csv', { query: '?raw', import: 'default', eager: true });

function normalizeText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}

function getCsvDocsDisponiveis() {
  const csvDisponiveis = {};
  for (const path in csvDocs) {
    const nome = path.split('/').pop().replace(/\.csv$/i, '');
    csvDisponiveis[nome] = csvDocs[path];
  }
  return csvDisponiveis;
}

const csvDisponiveis = getCsvDocsDisponiveis();
const historicoCsv = csvDisponiveis.HistoricoEscolarSimplificado || '';
const equivalenciasCsvNome = Object.keys(csvDisponiveis).find((nome) => normalizeText(nome).includes('equivalencia'));
const equivalenciasCsv = equivalenciasCsvNome ? csvDisponiveis[equivalenciasCsvNome] : '';

export default {
  data() {
    return {
      grade: [],
      user: null,
      message: null,
      curriculoAtual: null,
      curriculoNovo: null,
    };
  },
  computed: {
    isLogado() {
      if (this.user) return true;
      try {
        return !!localStorage.getItem('samg_user');
      } catch (e) {
        return false;
      }
    },
    migracaoStats() {
      const disciplinas = this.grade.flatMap((periodo) => periodo.disciplinas || []);
      const total = disciplinas.length;
      const vencidas = disciplinas.filter((d) => d.situacao === 'Vencido').length;
      const equivalencias = disciplinas.filter((d) => d.origem === 'equivalencia').length;
      const pendentes = Math.max(total - vencidas, 0);
      return { total, vencidas, equivalencias, pendentes };
    },
  },
  methods: {
    loadUser() {
      try {
        const raw = localStorage.getItem('samg_user');
        this.user = raw ? JSON.parse(raw) : null;
      } catch (e) {
        this.user = null;
      }
    },
    onStorageChanged(e) {
      if (e.key && e.key !== 'samg_user') return;
      this.loadUser();
      this.loadMigracao();
    },
    onSamgUserChanged() {
      this.loadUser();
      this.loadMigracao();
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
        'de', 'da', 'do', 'das', 'dos', 'e', 'em', 'para', 'por', 'a', 'o', 'os', 'as',
        'ao', 'aos', 'na', 'no', 'nas', 'nos', 'um', 'uma', 'com', 'ou'
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
    splitLinhaCsv(line, delimiter = ',') {
      const cols = String(line || '').split(new RegExp(`${delimiter}(?=(?:[^"]*"[^"]*")*[^"]*$)`));
      return cols.map(c => {
        let v = String(c || '').trim();
        if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1).replace(/""/g, '"');
        return v;
      });
    },
    extrairCodigoDisciplina(value) {
      const m = String(value || '').toUpperCase().match(/[A-Z]{3}\d{4}/);
      return m ? m[0] : null;
    },
    normalizarVersao(value) {
      return String(value || '').replace(/\D/g, '');
    },
    extrairVersaoCurriculoHistorico(text, matricula = null) {
      const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return null;

      const header = this.splitLinhaCsv(lines[0]).map(h => normalizeText(h));
      const idxOf = (names) => {
        for (const n of names) {
          const i = header.findIndex(h => h.includes(n));
          if (i >= 0) return i;
        }
        return -1;
      };

      const idxVersao = idxOf(['num versao', 'num_versao', 'versao']);
      const idxMatricula = idxOf(['matr aluno', 'matr_aluno', 'matricula']);
      if (idxVersao < 0) return null;

      const freq = new Map();
      for (let i = 1; i < lines.length; i++) {
        const cols = this.splitLinhaCsv(lines[i]);
        if (matricula && idxMatricula >= 0) {
          const rowMat = String(cols[idxMatricula] || '').trim();
          if (String(rowMat) !== String(matricula)) continue;
        }
        const versao = String(cols[idxVersao] || '').trim();
        if (!versao) continue;
        freq.set(versao, (freq.get(versao) || 0) + 1);
      }

      if (!freq.size) return null;
      return [...freq.entries()].sort((a, b) => b[1] - a[1])[0][0];
    },
    parseHistoricoAluno(text, matricula) {
      const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return { aprovadas: new Set() };

      const header = this.splitLinhaCsv(lines[0]).map(h => normalizeText(h));
      const idxOf = (names) => {
        for (const n of names) {
          const i = header.findIndex(h => h.includes(n));
          if (i >= 0) return i;
        }
        return -1;
      };

      const idxMatricula = idxOf(['matr aluno', 'matr_aluno', 'matricula']);
      const idxCodigo = idxOf(['cod ativ curric', 'cod ativ', 'cod disciplina', 'codigo']);
      const idxSituacao = idxOf(['descr situacao', 'situacao']);

      const aprovadas = new Set();
      for (let i = 1; i < lines.length; i++) {
        const cols = this.splitLinhaCsv(lines[i]);
        if (idxMatricula >= 0) {
          const rowMat = String(cols[idxMatricula] || '').trim();
          if (String(rowMat) !== String(matricula)) continue;
        }

        const codigo = String(cols[idxCodigo] || '').trim().toUpperCase();
        if (!codigo) continue;
        const situacao = String(cols[idxSituacao] || '');
        if (/apv|aprovad/i.test(situacao)) aprovadas.add(codigo);
      }

      return { aprovadas };
    },
    parseCurriculoCsv(text) {
      const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return [];

      const header = this.splitLinhaCsv(lines[0]).map(h => normalizeText(h));
      const idxOf = (names) => {
        for (const n of names) {
          const i = header.findIndex(h => h.includes(n));
          if (i >= 0) return i;
        }
        return -1;
      };

      const idxCod = idxOf(['cod disciplina', 'cod ativ curric', 'cod ativ', 'codigo']);
      const idxNome = idxOf(['nome disciplina', 'nome ativ curric', 'nome ativ']);
      const idxPeriodo = idxOf(['periodo ideal', 'semestre ideal', 'periodo']);
      const idxTipo = idxOf(['tipo disciplina', 'tipo']);

      const dedup = new Map();
      for (let i = 1; i < lines.length; i++) {
        const cols = this.splitLinhaCsv(lines[i]);
        const codigo = String(cols[idxCod] || '').trim().toUpperCase();
        if (!codigo || dedup.has(codigo)) continue;

        const nome = String(cols[idxNome] || codigo).trim();
        const periodoRaw = String(cols[idxPeriodo] || '').trim();
        const tipo = String(cols[idxTipo] || '').trim();
        const periodoMatch = periodoRaw.match(/\d+/);
        const periodo = periodoMatch ? parseInt(periodoMatch[0], 10) : null;
        const obrigatoria = normalizeText(tipo).includes('obrig');

        if (!obrigatoria) continue;
        dedup.set(codigo, { codigo, nome, periodo });
      }

      return [...dedup.values()];
    },
    parseEquivalenciasCsv(text, versaoDestino) {
      const out = new Map();
      const lines = String(text || '').split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return out;

      const header = this.splitLinhaCsv(lines[0], ';').map(h => normalizeText(h));
      const idxOf = (names) => {
        for (const n of names) {
          const i = header.findIndex(h => h.includes(n));
          if (i >= 0) return i;
        }
        return -1;
      };

      const idxVersao = idxOf(['num versao', 'num_versao', 'versao']);
      const idxNova = idxOf(['nome_disciplina', 'nome disciplina']);
      const idxEquiv = idxOf(['nome_disc_equiv', 'nome disc equiv', 'disc equiv']);
      const versaoDestinoNormalizada = this.normalizarVersao(versaoDestino);

      for (let i = 1; i < lines.length; i++) {
        const cols = this.splitLinhaCsv(lines[i], ';');
        const versaoLinha = String(cols[idxVersao] || '').trim();
        if (this.normalizarVersao(versaoLinha) !== versaoDestinoNormalizada) continue;

        const codigoNovo = this.extrairCodigoDisciplina(cols[idxNova]);
        const codigoEquiv = this.extrairCodigoDisciplina(cols[idxEquiv]);
        if (!codigoNovo || !codigoEquiv) continue;

        if (!out.has(codigoNovo)) out.set(codigoNovo, new Set());
        out.get(codigoNovo).add(codigoEquiv);
      }

      return out;
    },
    getUltimoCurriculo() {
      const curriculos = Object.entries(csvDisponiveis).reduce((acc, [nomeArquivo, text]) => {
        const match = nomeArquivo.match(/^curriculo-?(\d+)$/i);
        if (!match) return acc;
        const ver = match[1];
        acc[ver] = { text, ver };
        return acc;
      }, {});

      const versoes = Object.keys(curriculos)
        .map(v => ({ raw: v, num: parseInt(v, 10) }))
        .filter(v => !Number.isNaN(v.num))
        .sort((a, b) => b.num - a.num);

      if (!versoes.length) return null;
      return curriculos[versoes[0].raw];
    },
    buildGradeMigracao(curriculoNovoList, aprovadas, equivalenciasMap) {
      const porPeriodo = new Map();

      for (const disciplina of curriculoNovoList) {
        const codigo = disciplina.codigo;
        const equivalencias = [...(equivalenciasMap.get(codigo) || new Set())];
        const equivalenciasConcluidas = equivalencias.filter(cod => aprovadas.has(cod));
        const venceuDireto = aprovadas.has(codigo);
        const venceuEquiv = !venceuDireto && equivalenciasConcluidas.length > 0;
        const situacao = (venceuDireto || venceuEquiv) ? 'Vencido' : 'Não Vencido';
        const origem = venceuDireto ? 'direta' : (venceuEquiv ? 'equivalencia' : 'pendente');

        const periodo = disciplina.periodo || 'Não informado';
        if (!porPeriodo.has(periodo)) porPeriodo.set(periodo, []);

        porPeriodo.get(periodo).push({
          codigo,
          nome: disciplina.nome,
          situacao,
          origem,
          equivalenciasConcluidas,
        });
      }

      return [...porPeriodo.entries()]
        .sort((a, b) => {
          const na = Number(a[0]);
          const nb = Number(b[0]);
          if (!Number.isNaN(na) && !Number.isNaN(nb)) return na - nb;
          if (!Number.isNaN(na)) return -1;
          if (!Number.isNaN(nb)) return 1;
          return String(a[0]).localeCompare(String(b[0]));
        })
        .map(([periodo, disciplinas]) => {
          const total = disciplinas.length;
          const vencidas = disciplinas.filter((d) => d.situacao === 'Vencido').length;
          const percentual = total ? Math.round((vencidas / total) * 100) : 0;
          return {
            periodo,
            disciplinas: disciplinas.sort((x, y) => x.codigo.localeCompare(y.codigo)),
            total,
            vencidas,
            percentual,
          };
        });
    },
    loadMigracao() {
      if (!this.user || !this.user.matricula) {
        this.grade = [];
        return;
      }

      if (!historicoCsv) {
        this.message = 'Histórico escolar não disponível para consulta.';
        this.grade = [];
        return;
      }

      const matricula = String(this.user.matricula);
      const versaoAtual = this.extrairVersaoCurriculoHistorico(historicoCsv, matricula);
      const { aprovadas } = this.parseHistoricoAluno(historicoCsv, matricula);

      if (!aprovadas.size) {
        this.message = `Nenhum histórico encontrado para a matrícula ${matricula}.`;
        this.grade = [];
        return;
      }

      const curriculoDestino = this.getUltimoCurriculo();
      if (!curriculoDestino) {
        this.message = 'Nenhum currículo novo disponível.';
        this.grade = [];
        return;
      }

      const curriculoNovoList = this.parseCurriculoCsv(curriculoDestino.text);
      const equivalenciasMap = equivalenciasCsv
        ? this.parseEquivalenciasCsv(equivalenciasCsv, curriculoDestino.ver)
        : new Map();

      this.curriculoAtual = versaoAtual;
      this.curriculoNovo = curriculoDestino.ver;
      this.grade = this.buildGradeMigracao(curriculoNovoList, aprovadas, equivalenciasMap);
      this.message = null;
    },
  },
  created() {
    this.loadUser();
  },
  mounted() {
    this.loadMigracao();
    window.addEventListener('samg_user_changed', this.onSamgUserChanged);
    window.addEventListener('storage', this.onStorageChanged);
  },
  beforeUnmount() {
    window.removeEventListener('samg_user_changed', this.onSamgUserChanged);
    window.removeEventListener('storage', this.onStorageChanged);
  },
};
</script>

<style lang="css" scoped>
.historico {
  min-width: 50vw;
  margin-bottom: 24px;
}

.warning {
  color: #ef5350;
}

.periodo-card {
  border-top: 4px solid #1976d2;
}

.gap-2 {
  gap: 8px;
}

.text-left {
  text-align: left;
}

.bg-light-blue {
  background-color: #e3f2fd;
}
</style>
