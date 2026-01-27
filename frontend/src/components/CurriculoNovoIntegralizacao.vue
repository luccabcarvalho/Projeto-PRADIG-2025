<template>
    <v-row>
        <v-col cols="12" class="d-flex align-center">
            <v-card-title>Currículo novo</v-card-title>
            <v-spacer></v-spacer>
        </v-col>
        <v-col v-show="ver" v-for="i in periodos" :key="i" class="pa-6" :class="{ 'borda-coluna': i < 8 }">
            <div class="mb-8 borda-linha">{{ `${i}° período` }}</div>

            <v-row v-if="disciplinasCursadas.length" v-for="disciplina in disciplinasCursadas" :key="disciplina.Codigo">
                <CaixaDisciplina v-if="disciplina.PeriodoRecomendado === i" @click="disciplinaSelecionada = disciplina"
                    :disciplina="disciplina" class="mb-4" :status="status(disciplina)" :cor="pegaCorEixo(disciplina?.Eixo)" />
            </v-row>
            <v-row v-else v-for="disciplina in disciplinasObrigatorias" :key="disciplina.Codigo + 'index'">
                <CaixaDisciplina v-if="disciplina.PeriodoRecomendado === i" @click="disciplinaSelecionada = disciplina"
                    :disciplina="disciplina" class="mb-4" :cor="pegaCorEixo(disciplina?.Eixo)" />
            </v-row>
        </v-col>
        <v-col v-show="ver" cols="12">
            <v-list class="d-flex flex-row flex-wrap">
                <v-list-item v-for="legenda in legendas" :key="legenda.eixo">
                    <v-icon icon="$square" :color="legenda.cor" class="mr-2" small></v-icon>
                    <span>{{ legenda.eixo }}</span>
                </v-list-item>
            </v-list>
        </v-col>

        <v-col cols="12">
            <v-list class="d-flex flex-row flex-wrap">
                <v-list-item v-for="legenda in legendasStatus" :key="legenda.eixo">
                    <v-icon :icon="legenda.icon" :color="legenda.cor" class="mr-2" small></v-icon>
                    <span>{{ legenda.status === "Matricula"? "Disciplina por fazer": legenda.status  }}</span>
                </v-list-item>
            </v-list>
        </v-col>

        <v-dialog v-if="disciplinaSelecionada !== null" v-model="disciplinaSelecionada">
            <DetalhesDisciplina :disciplina="disciplinaSelecionada" />
        </v-dialog>
    </v-row>
</template>
<script>
import { mdiPackageVariantClosedRemove } from '@mdi/js';
import curriculoNovoObrigatorias from '../assets/Disciplinas Obrigatórias - Currículo novo.json';
import CaixaDisciplina from './CaixaDisciplina.vue';
import DetalhesDisciplina from './DetalhesDisciplina.vue';

const EIXO_COR = [
    { eixo: "Atividades complementares", cor: "#78909C" },
    { eixo: "Atividades de extensão", cor: "#6D4C41" },
    { eixo: "Trabalho de conclusão de curso", cor: "#00ACC1" },
    { eixo: "Infraestrutura em SI", cor: "#F06292" },
    { eixo: "Engenharia de Dados e Informação", cor: "#81C784" },
    { eixo: "Desenvolvimento de Software para SI (Engenharia de Software)", cor: "#5C6BC0" },
    { eixo: "Desenvolvimento de Software para SI (Programação e Algoritmos)", cor: "#64B5F6" },
    { eixo: "Gestão de SI e TI, Empreendedorismo e Inovação", cor: "#7E57C2" },
    { eixo: "Visão Sistêmica (Fundamentos de Matemática)", cor: "#FFCC80" },
    { eixo: "Visão Sistêmica (Sistemas de Informação)", cor: "#FFFF00" },
]

const EIXO_COR_STATUS = [
    { status: "Vencido", cor: "green", icon: "$check" },
    { status: "Matricula/Cursand", cor: "orange", icon: "$unCheck" },
    { status: "Não vencido", cor: "Black", icon: "$unCheck" },
]


export default {
    name: "curriculo-novo-integralizacao",
    props: {
        disciplinasCursadas: {
            required: true,
            type: Array,
            default: () => []
        }
    },
    data: () => ({
        disciplinasObrigatorias: curriculoNovoObrigatorias.CurriculoNovo,
        disciplinaSelecionada: null,
        periodos: 8,
        ver: true,
        eixoCor: EIXO_COR,
        legendas: EIXO_COR,
        legendasStatus: EIXO_COR_STATUS
    }),
    methods: {
        corPorStatus(situacao) {
            if (!situacao) return "Black";
            switch (situacao.toLowerCase()) {
                case "vencido": return "green";
                case "matricula/cursand": return "orange";
                case "nao vencido": return "Black";
                default: return "Black";
            }
        },
        status(disciplina) {
            if (!disciplina || !disciplina.Situacao) return { ver: "uncheck", cor: ""};
            switch (disciplina.Situacao.toLowerCase()) {
                case "vencido": return { ver: "check", cor: "green"};
                case "não vencido": return { ver: "uncheck", cor: "Black"};
                case "matricula/cursand": return { ver: "", cor: "orange"};
                default: return { ver: "uncheck", cor: ""};
            }
        },
        pegaCorEixo(eixo){
            return this.eixoCor.find(arrayEixo => arrayEixo.eixo === eixo)? this.eixoCor.find(arrayEixo => arrayEixo.eixo === eixo).cor : '#BDBDBD'  
        }
    },
    components: { DetalhesDisciplina, CaixaDisciplina }
}
</script>