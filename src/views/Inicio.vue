<template>
    <v-container fluid>
        <v-row justify="center">
            <v-card class="d-flex flex-column pa-8">
                <v-card-title>SAMG BSI</v-card-title>
                <router-link to="/integralizacao">
                    <v-btn class="mb-4">Histórico</v-btn>
                </router-link>
                <router-link to="/progresso">
                    <v-btn>Progresso</v-btn>
                </router-link>
            </v-card>
        </v-row>
    </v-container>
</template>
<script>

export default {
    name: "inicio",
    data() {
        return {}
    },

    methods: {
    }
}
</script>

<style lang="css" scoped></style>
