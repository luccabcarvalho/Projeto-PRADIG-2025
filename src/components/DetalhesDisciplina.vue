<template>
    <v-card class="pa-2" :color="corFundoCartao">
        <v-card-title>{{ disciplina.Nome }}</v-card-title>
        <v-card-subtitle>{{ disciplina.codigo }}</v-card-subtitle>
        <div class="d-flex flex-column">
            <v-card-text>Carga horária: {{ disciplina.CargaHoraria }}</v-card-text>
            <v-card-text>Créditos: {{ disciplina.Creditos }}</v-card-text>
            <v-card-text>Ementa: {{ disciplina.Ementa }}</v-card-text>
            <v-card-text>Pré Requisitos: {{ disciplina.PreRequisitos || "Esta disciplina não tem pré-requisitos"}}</v-card-text>
            <v-card-text>Período: {{ disciplina.PeriodoRecomendado }}</v-card-text>
        </div>
    </v-card>
</template>
<script>
export default {
    name: 'DetalhesDisciplina',
    props: {
        disciplina: {
            type: Object,
            required: true,
            default: () => { }
        },
        status: { type: String, default: () => '' }
    },
    computed: {
        corFundoCartao() {
            if (this.status === 'REP') return 'red';
            else if (this.status === 'APV') return 'green';
            else return '#F5F5F5';
        }
    }
}
</script>
<style>
    .largura-caixa{
        width: 120px;
    }
</style>