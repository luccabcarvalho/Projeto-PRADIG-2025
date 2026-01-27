<template>
  <v-row>
    <v-col cols="12" class="d-flex align-center">
      <v-card-title>Currículo atual</v-card-title>
      <v-spacer></v-spacer>
      <v-icon :icon="manipulaOlho" @click="ver = !ver" />
    </v-col>
    <v-col
      v-show="ver"
      v-for="i in periodos"
      :key="i"
      class="pa-6"
      :class="{ 'borda-coluna': i < 8 }"
    >
      <div class="mb-8 borda-linha">{{ `${i}° período` }}</div>

      <v-row
        v-if="disciplinasCursadas.length"
        v-for="disciplina in disciplinasCursadas"
        :key="disciplina.Codigo"
      >
        <CaixaDisciplina
          v-if="disciplina.PeriodoRecomendado === i"
          @click="disciplinaSelecionada = disciplina"
          :disciplina="disciplina"
          class="mb-4"
          :status="status(disciplina)"
          cor="#BDBDBD"
        />
      </v-row>
      <v-row
        v-else
        v-for="disciplina in disciplinasObrigatorias"
        :key="disciplina.Codigo + 'index'"
      >
        <CaixaDisciplina
          v-if="disciplina.PeriodoRecomendado === i"
          @click="disciplinaSelecionada = disciplina"
          :disciplina="disciplina"
          class="mb-4"
          cor="#BDBDBD"
        />
      </v-row>
    </v-col>
    <v-col cols="12" v-show="ver">
      <v-list class="d-flex flex-row flex-wrap">
        <v-list-item v-for="legenda in legendasStatus" :key="legenda.eixo">
          <v-icon
            :icon="legenda.icon"
            :color="legenda.cor"
            class="mr-2"
            small
          ></v-icon>
          <span>{{
            legenda.status === "Matricula"
              ? "Disciplina por fazer"
              : legenda.status
          }}</span>
        </v-list-item>
      </v-list>
    </v-col>
    <v-dialog
      v-if="disciplinaSelecionada !== null"
      v-model="disciplinaSelecionada"
    >
      <DetalhesDisciplina :disciplina="disciplinaSelecionada" />
    </v-dialog>
  </v-row>
</template>
<script>
import curriculoAntigoObrigatorias from "../assets/Disciplinas Obrigatórias - Currículo antigo.json";
import CaixaDisciplina from "./CaixaDisciplina.vue";
import DetalhesDisciplina from "./DetalhesDisciplina.vue";

const EIXO_COR_STATUS = [
  { status: "Aprovado / Aprovado sem nota", cor: "green", icon: "$check" },
  {
    status: "Dispensa com nota / Dispensa sem nota",
    cor: "yellow",
    icon: "$check",
  },
  { status: "Reprovado sem nota", cor: "orange", icon: "$x" },
  {
    status: "Reprovado por nota / Reprovado por falta",
    cor: "red",
    icon: "$x",
  },
  { status: "Matricula", cor: "black", icon: "$unCheck" },
];

export default {
  name: "curriculo-atual",
  props: {
    disciplinasCursadas: {
      required: true,
      type: Array,
      default: () => [],
    },
  },
  data: () => ({
    disciplinasObrigatorias: curriculoAntigoObrigatorias.CurriculoAntigo,
    disciplinaSelecionada: null,
    periodos: 8,
    ver: true,
    legendasStatus: EIXO_COR_STATUS,
  }),
  computed: {
    manipulaOlho() {
      return this.ver ? "$eye" : "$offEye";
    },
  },
  methods: {
    corPorStatus(situacao) {
      if (!situacao) return "#BDBDBD";
      switch (situacao.toLowerCase()) {
        case "aprovado":
          return "green";
        case "dispensa com nota":
          return "yellow";
        case "dispensa sem nota":
          return "yellow";
        case "reprovado sem nota":
          return "orange";
        case "reprovado por nota":
          return "red";
        case "reprovado por falta":
          return "red";
        case "aprovado sem nota":
          return "green";
        case "matrícula":
          return "black";
        default:
          return "#BDBDBD";
      }
    },
    status(disciplina) {
      if (!disciplina || !disciplina.Situacao)
        return { ver: "uncheck", cor: "" };
      switch (disciplina.Situacao.toLowerCase()) {
        case "aprovado":
          return { ver: "check", cor: "green" };
        case "reprovado sem nota":
          return { ver: "x", cor: "" };
        case "reprovado por falta":
          return { ver: "x", cor: "" };
        case "aprovado sem nota":
          return { ver: "check", cor: "green" };
        case "dispensa sem nota":
          return { ver: "check", cor: "yellow" };
        case "dispensa com nota":
          return { ver: "check", cor: "yellow" };
        case "matrícula":
          return { ver: "uncheck", cor: "black" };
        default:
          return { ver: "uncheck", cor: "" };
      }
    },
  },
  components: { DetalhesDisciplina, CaixaDisciplina },
};
</script>
