<template>
  <v-container fluid class="historico">
    <v-row>
      <strong class="warning text-h5 text-center">
        AVISO: Este simulador é informativo. Leia os anexos oficiais para mais detalhes.
      </strong>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-file-input
          label="Anexar PDF da Reforma Curricular (contendo o Mapa de Equivalência)"
          variant="solo"
          ref="reforma"
          accept="application/pdf"
          @change="onChangeReforma"
        />
      </v-col>
      <v-col cols="12" md="6">
        <v-file-input
          label="Anexar PDF de Integralização (situação do aluno)"
          variant="solo"
          ref="integralizacao"
          accept="application/pdf"
          @change="onChangeIntegralizacao"
        />
      </v-col>
    </v-row>

    <v-row class="mt-8" justify="center" v-if="grade.length">
      <v-col
        v-for="(periodo, idx) in grade"
        :key="idx"
        cols="auto"
        class="d-flex flex-column align-center"
      >
        <h4 class="mb-2 text-center">{{ periodo.periodo }}º período</h4>

        <div
          v-for="disciplina in periodo.disciplinas"
          :key="disciplina.codigo"
          class="mb-2"
        >
          <v-btn
            :color="disciplina.situacao === 'Vencido' ? 'green' : disciplina.situacao?.toLowerCase().includes('cursando') ? 'blue' : 'grey'"
            class="w-100"
            style="min-width: 80px; max-width: 160px;"
            depressed
            :title="disciplina.nome"
          >
            {{ sigla(disciplina.nome) }}
          </v-btn>
        </div>
      </v-col>
    </v-row>
    <v-row v-else class="mt-8" justify="center">
      <em>Envie os dois PDFs para ver o status das disciplinas propostas na nova grade.</em>
    </v-row>
  </v-container>
</template>

<script>
import instance from "@/api/instance";

export default {
  data() {
    return {
      reforma: [], // registros do mapa (readPdfMigracao)
      integralizacao: [], // retorno do /uploadIntegralizacao
      grade: [], // [{ periodo, disciplinas: [{ codigo, nome, periodo, situacao }] }]
    };
  },
  methods: {
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
        // Mantém algarismos romanos como sufixo separado (I, II, III, IV, ...)
        if (romanRe.test(t)) {
          numerals.push(t.toUpperCase());
        } else if (/^\d+$/.test(t)) {
          initials.push(t[0]);
        } else {
          initials.push(t[0].toUpperCase());
        }
      }

      // Base: até 3 letras das iniciais (compacto e consistente)
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
    async onChangeReforma(event) {
      const file = event.target.files?.[0];
      if (!file) return;
      const formData = new FormData();
      formData.append("pdf", file);
      try {
        const { data } = await instance.post("uploadReforma", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        // data.disciplinas = [ { atual: {...}, proposta: {...}, tipoAlteracao } ]
        this.reforma = Array.isArray(data.disciplinas) ? data.disciplinas : [];
        this._recomputeGrade();
      } catch (e) {
        alert("Erro ao processar PDF da Reforma");
      }
    },
    async onChangeIntegralizacao(event) {
      const file = event.target.files?.[0];
      if (!file) return;
      const formData = new FormData();
      formData.append("pdf", file);
      try {
        const { data } = await instance.post("uploadIntegralizacao", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        // Esperado: data.disciplinas = [ { periodo, disciplinas: [ { codigo, nome, situacao, periodo } ] } ... ]
        this.integralizacao = Array.isArray(data.disciplinas) ? data.disciplinas : [];
        this._recomputeGrade();
      } catch (e) {
        alert("Erro ao processar PDF de Integralização");
      }
    },
    _recomputeGrade() {
      // Precisa da Reforma para montar as propostas; a Integralização marca o status
      if (!this.reforma.length) {
        this.grade = [];
        return;
      }

      // Mapa código -> situacao a partir do PDF de integralização
      const situacaoPorCodigo = new Map();
      for (const bloco of this.integralizacao) {
        const lista = bloco?.disciplinas || [];
        for (const d of lista) {
          if (d?.codigo) situacaoPorCodigo.set(d.codigo.trim(), d.situacao || null);
        }
      }

      // Deduplicar propostas por código e montar lista com status
      const porPeriodo = new Map();
      const vistos = new Set();
      for (const reg of this.reforma) {
        const p = reg?.proposta || {};
        if (!p?.codigo) continue;
        const codigo = String(p.codigo).trim();
        if (vistos.has(codigo)) continue;
        vistos.add(codigo);

        const periodo = p.periodo ?? "Não informado";
        const situacao = situacaoPorCodigo.get(codigo) || "Não Vencido";
        const item = {
          codigo,
          nome: p.nome || codigo,
          periodo,
          situacao,
        };
        if (!porPeriodo.has(periodo)) porPeriodo.set(periodo, []);
        porPeriodo.get(periodo).push(item);
      }

      // Ordena períodos numericamente quando possível
      const chaves = Array.from(porPeriodo.keys());
      chaves.sort((a, b) => {
        const na = parseInt(a);
        const nb = parseInt(b);
        if (!isNaN(na) && !isNaN(nb)) return na - nb;
        if (!isNaN(na)) return -1;
        if (!isNaN(nb)) return 1;
        return String(a).localeCompare(String(b));
      });

      this.grade = chaves.map((periodo) => ({
        periodo,
        disciplinas: porPeriodo.get(periodo).sort((x, y) => x.codigo.localeCompare(y.codigo)),
      }));
    },

  },
};
</script>

<style lang="css" scoped>
.historico {
  min-width: 80vw;
  margin-bottom: 24px;
}
.warning {
  color: #ef5350;
}
.link-equivalencias {
  text-decoration: underline;
}
.link-equivalencias:hover {
  text-decoration: underline;
  background: #1a1a1a;
}
</style>
