<template>
  <v-container>
    <v-row justify="center">
      <v-col cols="12" md="8" lg="6">
        <v-file-input
          class="w-100"
          style="max-width: 500px;"
          label="Anexe o PDF do histórico"
          placeholder="Clique ou arraste o PDF aqui"
          accept="application/pdf"
          @change="uploadPdf"
          variant="outlined"
        ></v-file-input>
        <template v-slot:selection="{ text }">
          <span v-if="!file">Nenhum arquivo selecionado</span>
          <span v-else>{{ text }}</span>
        </template>
      </v-col>
    </v-row>


    <v-row class="mt-8" justify="center">
      <v-col
        v-for="(periodo, idx) in grade"
        :key="idx"
        cols="auto"
        class="d-flex flex-column align-center"
      >
        <h4 class="mb-2 text-center">{{ periodo.periodo }}º período</h4>

        <div
          v-for="disciplina in periodo.disciplinas[0].disciplinas"
          :key="disciplina.codigo"
          class="mb-2"
        >
          <v-btn
          :color="disciplina.situacao === 'Vencido' ? 'green' : 'grey'"
          class="w-100"
          style="min-width: 80px; max-width: 100px;"
          depressed
        >
          {{ disciplina.codigo }}
        </v-btn>

        </div>
      </v-col>
    </v-row>
  </v-container>
</template>



<script>
import axios from "axios";
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
        const response = await instance.post("uploadIntegralizacao", formData, {
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
