<template>
  <v-container fluid class="progresso">
    <v-row>
      <strong class="warning text-h5 text-center">
        AVISO: Este simulador é informativo. Leia os anexos oficiais para mais detalhes.
      </strong>
    </v-row>
  
    <v-row justify="center">
      <v-col cols="12" md="10">
        <v-alert v-if="!user" type="info" border="left" class="mb-4">Faça login para ver seu histórico e progresso automaticamente a partir da matrícula.</v-alert>
        <v-alert v-if="message" type="info" border="left" class="mb-4">{{ message }}</v-alert>
        
        <!-- Grade Curricular por Período -->
        <div v-if="curriculoGrade.length && user" class="text-center my-6">
          <h2 class="mb-2">Grade Curricular</h2>
          <p v-if="user.matricula && curriculoVersion" class="text-caption mb-6">
            Matrícula: {{ user.matricula }} | Currículo: v{{ curriculoVersion }}
          </p>
          
          <v-row class="mt-6" justify="center">
            <v-col v-for="(periodo, idx) in curriculoGrade" :key="'periodo-'+idx" cols="12" md="6" lg="4" class="pa-4">
              <v-card class="elevation-4 periodo-card" style="min-height: 100%;">
                <v-card-title class="text-center bg-light-blue" style="background-color: #e3f2fd;">
                  <span class="text-h6">{{ periodo.periodo }}</span>
                </v-card-title>
                
                <v-card-text class="pa-4">
                  <div v-for="disc in periodo.disciplinas" :key="disc.codigo" class="mb-3 d-flex align-center gap-2">
                    <v-btn
                      :color="disc.status === 'Vencido' ? 'success' : 'grey-lighten-2'"
                      :text-color="disc.status === 'Vencido' ? 'white' : 'black'"
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

          <!-- Legenda de cores -->
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
              </div>
            </v-col>
          </v-row>
        </div>

        <!-- Fallback quando não carregou -->
        <div v-else-if="user && !curriculoGrade.length" class="mt-6 text-center">
          <v-alert type="warning" border="left">
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
import historicoCsv from '@/docs/HistoricoEscolarSimplificado.csv?raw';

// Importa todos os currículos disponíveis
import curriculo20002 from '@/docs/curriculo-20002.csv?raw';
import curriculo20052 from '@/docs/curriculo-20052.csv?raw';
import curriculo20081 from '@/docs/curriculo-20081.csv?raw';
import curriculo20232 from '@/docs/curriculo-20232.csv?raw';

export default {
  data() {
    return {
      grade: [],
      user: null,
      message: null,
      periodList: [],
      curriculoVersion: null,
      curriculoGrade: [],
    };
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

    /**
     * Extrai o ano e semestre do currículo da matrícula (primeiros 5 dígitos)
     * Ex: "20002210547" -> "20002" (para curriculo-20002.csv)
     */
    _extractCurriculoYearFromMatricula(matricula) {
      if (!matricula || matricula.length < 5) return null;
      return matricula.substring(0, 5);
    },

    async loadHistoricoForUser() {
      if (!this.user || !this.user.matricula) return;
      try {
        // 1. Extrair o ano do currículo da matrícula
        const curriculoYear = this._extractCurriculoYearFromMatricula(this.user.matricula);

        // 2. Carregar o histórico do aluno filtrado pela matrícula
        const text = historicoCsv;
        const disciplinas = this._parseHistoricoCsv(text, String(this.user.matricula));
        
        if (!disciplinas.length) {
          this.message = 'Nenhum histórico encontrado para a matrícula ' + this.user.matricula;
          this.grade = [];
          this.curriculoGrade = [];
          return;
        }
        
        this.grade = this.organizarPorPeriodo(disciplinas);
        this.periodList = this.grade.map(p => p.periodo);
        
        // 3. Carregar o currículo específico do aluno (baseado no ano da matrícula)
        // Se não encontrar, _getCurriculoByYear já busca alternativas automaticamente
        if (curriculoYear) {
          const curriculoRaw = this._getCurriculoByYear(curriculoYear);
          if (curriculoRaw) {
            const currList = this._parseCurriculoCsv(curriculoRaw.text);
            this.curriculoVersion = curriculoRaw.ver;
            // 4. Construir grade com status baseado no histórico
            this.curriculoGrade = this._buildCurriculoProgress(currList, disciplinas);
          } else {
            this.curriculoGrade = [];
          }
        }

        this.message = null; 
      } catch (err) {
        console.error('Erro ao carregar histórico:', err);
        this.message = 'Erro ao carregar histórico: ' + err.message;
        this.curriculoGrade = [];
      }
    },

    onSamgUserChanged(e) {
      // reload when other parts of the app (or other tabs) update the logged user
      this.loadUser();
      this.loadHistoricoForUser();
    },
    sigla(nome) {
      if (!nome || typeof nome !== 'string') return '';
      // Remove diacríticos e normaliza espaços
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
        // Inclui algarismos romanos inteiros como token (I, II, III, IV, ...)
        if (romanRe.test(t)) {
          numerals.push(t.toUpperCase());
        } else if (/^\d+$/.test(t)) {
          initials.push(t[0]);
        } else {
          initials.push(t[0].toUpperCase());
        }
      }

      // Base: até 3 letras das iniciais (mantém compactação padrão)
      let base = initials.join('');
      if (!base && numerals.length) {
        // Se só há algarismo romano, retorna-o
        return numerals.join(' ');
      }
      if (!base) {
        // Fallback: primeiras letras do nome bruto
        base = s.replace(/\s+/g, '').slice(0, 3).toUpperCase();
      }
      base = base.slice(0, 3);
      // Alg. romano aparece separado: "GA II"
      if (numerals.length) return `${base} ${numerals.join(' ')}`;
      return base;
    },
    async uploadPdf(event) {
      const file = event.target.files[0];
      if (!file) return;
      // Se for CSV, parse no frontend
      const name = (file.name || '').toLowerCase();
      if (name.endsWith('.csv') || file.type === 'text/csv') {
        try {
          const text = await this._readFileAsText(file);
          const disciplinas = this._parseHistoricoCsv(text);
          this.grade = this.organizarPorPeriodo(disciplinas);
        } catch (e) {
          console.error(e);
          alert('Erro ao processar CSV');
          this.grade = [];
        }
        return;
      }

      // Caso contrário, assume PDF e envia ao backend
      const formData = new FormData();
      formData.append("pdf", file);

      try {
        const response = await instance.post("uploadIntegralizacao", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        this.grade = this.organizarPorPeriodo(response.data.disciplinas);
      } catch (err) {
        alert("Erro ao processar PDF");
        this.grade = [];
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

    _splitCsvLine(line) {
      // Split on commas not inside quotes
      const cols = line.split(/,(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)/);
      return cols.map(c => {
        let v = c.trim();
        if (v.startsWith('"') && v.endsWith('"')) v = v.slice(1, -1).replace(/""/g, '"');
        return v;
      });
    },

    _parseHistoricoCsv(text, matricula = null) {
      const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return [];
      const header = this._splitCsvLine(lines[0]).map(h => h.toLowerCase());

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
        const cols = this._splitCsvLine(lines[i]);

        // If filtering by matricula, skip rows that don't match
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

        // Normalize PERIODO: extrai número e formata como "N°" (trata "1" e "1°"). Caso não haja número, mantém o texto bruto.
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

      // Deduplicação por (codigo + periodo): mantém múltiplos registros do mesmo curso em períodos diferentes.
      const byCodePeriod = new Map();
      for (const r of rows) {
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

      // Mapeia situação textual para os rótulos usados no frontend
      const mapSituacao = (raw) => {
        if (!raw) return 'Não Vencido';
        if (/apv|aprovad/i.test(raw)) return 'Vencido';
        if (/matr|matr[ií]cula|matricula/i.test(raw)) return 'Matricula/Cursando';
        return 'Não Vencido';
      };

      // Converte para array plano esperado pela organizarPorPeriodo
      const out = [];
      for (const [key, r] of byCodePeriod.entries()) {
        out.push({ codigo: r.codigo.trim(), nome: r.nome || r.codigo.trim(), situacao: mapSituacao(r.situacaoRaw), periodo: r.periodo });
      }
      
      return out;
    },

    /**
     * Carrega o currículo específico pelo ano+semestre
     * Ex: year = "20072" procura por curriculo-20072.csv
     * Se não encontrar, procura pelo currículo mais recente anterior
     */
    _getCurriculoByYear(year) {
      // Mapa de currículos importados
      const curriculosDisponiveis = {
        '20002': { text: curriculo20002, ver: '20002' },
        '20052': { text: curriculo20052, ver: '20052' },
        '20081': { text: curriculo20081, ver: '20081' },
        '20232': { text: curriculo20232, ver: '20232' },
      };
      
      // Tentar encontrar exatamente
      if (curriculosDisponiveis[year]) {
        return curriculosDisponiveis[year];
      }
      
      // Se não encontrou, procurar pelo mais recente anterior
      const yearNum = parseInt(year, 10);
      const disponiveisOrdenados = Object.keys(curriculosDisponiveis)
        .map(k => ({ year: k, num: parseInt(k, 10) }))
        .filter(k => k.num <= yearNum)
        .sort((a, b) => b.num - a.num);
      
      if (disponiveisOrdenados.length > 0) {
        const melhorOpcao = disponiveisOrdenados[0].year;
        return curriculosDisponiveis[melhorOpcao];
      }
      
      // Última tentativa: usar o mais recente disponível
      const todosOrdenados = Object.keys(curriculosDisponiveis)
        .map(k => ({ year: k, num: parseInt(k, 10) }))
        .sort((a, b) => b.num - a.num);
      
      if (todosOrdenados.length > 0) {
        const ultimoRecurso = todosOrdenados[0].year;
        return curriculosDisponiveis[ultimoRecurso];
      }
      
      console.error('❌ Nenhum currículo disponível');
      return null;
    },

    // Carrega o arquivo de currículo mais recente embutido pelo Vite (build-time)
    _getLatestCurriculoRaw() {
      const modules = import.meta.globEager('../docs/curriculo*.csv?raw');
      const candidates = Object.keys(modules).filter(p => /curriculo-?(\d+)\.csv$/i.test(p));
      if (!candidates.length) return null;

      let best = null;
      let bestNum = -Infinity;
      for (const p of candidates) {
        const m = p.match(/curriculo-?(\d+)\.csv$/i);
        if (!m) continue;
        const num = parseInt(m[1], 10);
        if (num > bestNum) { bestNum = num; best = p; }
      }
      if (!best) return null;
      const raw = modules[best];
      const text = (typeof raw === 'string') ? raw : (raw.default || raw);
      const ver = best.match(/curriculo-?(\d+)\.csv$/i)?.[1] || best;
      return { text, ver };
    },

    _parseCurriculoCsv(text) {
      const lines = text.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
      if (!lines.length) return [];
      const header = this._splitCsvLine(lines[0]).map(h => h.toLowerCase());

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

      // Usar Map para evitar duplicatas por código
      const dedup = new Map();
      
      for (let i = 1; i < lines.length; i++) {
        const cols = this._splitCsvLine(lines[i]);
        const codigo = idxCod >= 0 ? (cols[idxCod] || '').trim() : null;
        if (!codigo) continue;
        
        const codUpper = codigo.toUpperCase();
        
        // Se já tem essa disciplina, pula (deduplicação)
        if (dedup.has(codUpper)) continue;
        
        const nome = idxNome >= 0 ? (cols[idxNome] || '').trim() : '';
        const rawPeriodo = idxPeriodo >= 0 ? (cols[idxPeriodo] || '').trim() : '';
        let periodo = 'Não informado';
        const matchNum = rawPeriodo.match(/(\d+)/);
        if (matchNum) periodo = `${parseInt(matchNum[1],10)}°`;
        else if (rawPeriodo) periodo = rawPeriodo;
        const creditos = idxCred >= 0 ? parseFloat((cols[idxCred] || '').replace(',', '.')) || null : null;
        const tipo = idxTipo >= 0 ? (cols[idxTipo] || '').trim() : null;

        dedup.set(codUpper, { codigo: codUpper, nome, periodo, creditos, tipo });
      }

      const out = Array.from(dedup.values());
      
      return out;
    },

    _buildCurriculoProgress(curriculoList, userDisciplinas) {
      const statusByCode = {};
      
      // Mapear status do histórico por código de disciplina
      const aprovados = [];
      for (const d of userDisciplinas) {
        const cod = (d.codigo || '').toUpperCase();
        statusByCode[cod] = d.situacao || 'Não Vencido';
        if (d.situacao === 'Vencido') {
          aprovados.push({ cod, nome: d.nome });
        }
      }

      const periodMap = {};
      const encontrados = new Set();
      
      for (const c of curriculoList) {
        const periodo = c.periodo || 'Não informado';
        if (!periodMap[periodo]) periodMap[periodo] = [];
        
        const codUpper = (c.codigo || '').toUpperCase();
        const status = statusByCode[codUpper] || 'Não Vencido';
        
        if (status === 'Vencido') {
          encontrados.add(codUpper);
        }
        
        periodMap[periodo].push({ 
          codigo: c.codigo, 
          nome: c.nome, 
          creditos: c.creditos, 
          tipo: c.tipo, 
          status 
        });
      }

      // Adicionar disciplinas aprovadas que não estão no currículo
      const adicionais = [];
      for (const ap of aprovados) {
        if (!encontrados.has(ap.cod)) {
          adicionais.push({ 
            codigo: ap.cod, 
            nome: ap.nome, 
            creditos: null, 
            tipo: 'Optativa/Complementar', 
            status: 'Vencido' 
          });
        }
      }
      
      // Se houver disciplinas adicionais, adicionar um período especial
      if (adicionais.length > 0) {
        periodMap['Optativas/Complementares'] = adicionais;
      }

      return Object.keys(periodMap)
        .sort((a,b) => {
          // Ordenar períodos numericamente, com "Optativas/Complementares" por último
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

    organizarPorPeriodo(disciplinas) {
  const periodos = {};

  disciplinas.forEach((disc) => {
    const periodo = disc.periodo !== undefined && disc.periodo !== null
      ? disc.periodo
      : "Não informado";

    if (!periodos[periodo]) periodos[periodo] = [];
    periodos[periodo].push(disc);
  });

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

.periodo-card {
  border-top: 4px solid #1976d2;
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

.bg-light-blue {
  background-color: #e3f2fd;
}
</style>