<template>
    <v-card class="pa-2 largura-caixa" :color="cor">
        <v-icon :icon="status.ver === 'check' ? '$check' : '$unCheck'" :color="status.cor" class="icone"></v-icon>
        <v-tooltip :text="textoDispensa" content-class="caixa-tooltip">
            <template v-slot:activator="{ props }">
                <v-icon v-bind="props" v-show="dispensa" :icon="'$alert'" color="#E65100" class="icone-alerta"></v-icon>
            </template>
        </v-tooltip>
        <v-card-title>{{ disciplina.Sigla }}</v-card-title>
        <v-card-subtitle>{{ disciplina.codigo }}</v-card-subtitle>
    </v-card>
</template>
<script>
export default {
    name: 'CaixaDisciplina',
    props: {
        disciplina: {
            type: Object,
            required: true,
            default: () => { }
        },
        status: { type: Object, default: () => ({ ver: false, cor: "", solicitarDispensa: false }) },
        cor: { type: String, default: () => '' },
        eixo: { type: String, default: () => '' }
    },
    computed: {
        dispensa() {
            return this.status.solicitarDispensa === true;
        },
        textoDispensa(){
            return "É necessário o pedido de dispensa na secretaria do curso."
        }
    }
}
</script>
<style scoped>
.largura-caixa {
    width: 120px;
}

.icone {
    position: absolute !important;
    right: 4px;
}

.icone-alerta {
    position: absolute !important;
    left: 4px;
    z-index: 1;
}
.caixa-tooltip {
    background: black;
}

.v-card:hover {
    filter: brightness(70%) !important;
}
</style>
