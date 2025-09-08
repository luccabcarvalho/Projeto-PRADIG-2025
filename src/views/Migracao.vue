<template>
  <v-container fluid class="historico">
    <v-row>
      <strong class="warning text-h5 text-center">
        AVISO: este simulador é informativo. Leia os anexos oficiais para mais detalhes.
      </strong>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-file-input
          label="Anexar PDF da Reforma Curricular (contendo o Mapa de Equivalência)"
          variant="solo"
          ref="reforma"
          @change="uploadPdf"
          accept=".pdf"
        ></v-file-input>
      </v-col>
      <v-col cols="12">
        <v-file-input
          label="Anexar Histórico Escolar do Aluno (PDF emitido pelo SIE)"
          variant="solo"
          ref="historico"
          @change="uploadPdf"
          accept=".pdf"
        ></v-file-input>
      </v-col>
    </v-row>


    <v-row justify="center">
      <v-dialog v-model="verDisciplinasNaoAproveitadas" width="420px">
        <v-card flat>
          <v-list>
            <v-list-item
              v-for="disciplina in naoEquivalentes"
              :key="disciplina.codigo"
            >
              <p>Nome: {{ disciplina.nome }}</p>
              <p>Código: {{ disciplina.codigo }}</p>
            </v-list-item>
            <p class="text-center warning font-weight-bold">
              Consulte seu professor tutor para validar a situação das disciplinas acima.
            </p>
          </v-list>
        </v-card>
      </v-dialog>
    </v-row>
  </v-container>
</template>

<script>
import instance from "@/api/instance";

export default {
  data() {
    return {
      grade: [],
    };
  },
  methods: {
    async uploadPdf(event) {
      const file = event.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("pdf", file);

      try {
        const response = await instance.post("uploadReforma", formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        this.grade = this.organizarPorPeriodo(response.data.disciplinas);
      } catch (err) {
        alert("Erro ao processar PDF");
        this.grade = [];
      }
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
      const numA = parseInt(a);
      const numB = parseInt(b);
      if (!isNaN(numA) && !isNaN(numB)) return numA - numB;
      if (!isNaN(numA)) return -1;
      if (!isNaN(numB)) return 1;
      return a.localeCompare(b);
    })
    .map((periodo) => ({
      periodo,
      disciplinas: periodos[periodo],
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
