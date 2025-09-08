<template>
    <v-container fluid class="historico">
        <v-row>
            <strong class="warning text-h5 text-center">AVISO: este simulador foi elaborado apenas com propósitos informacionais e não deve ser
                considerado como uma garantia de situação após a migração curricular. Leia os anexos do Projeto Pedagógico
                de Curso (PPC) e as comunicações oficiais da Coordenação para mais informações.</strong>
        </v-row>
        <v-row>
            <v-col cols="12">
                <v-file-input label="Usar o histórico emitido no portal do aluno em 'Relatórios >> Histórico Escolar CR - Aprovados (SIE)'" variant="solo" ref="historico"
                    @change="lerPlanilhaDisciplinas"></v-file-input>
            </v-col>
        </v-row>
        <CurriculoAtual :disciplinas-cursadas="progressoAlunoGrade" />

        <v-col class="text-center">
            <v-btn :disabled="!naoEquivalentes.length" text
                @click="verDisciplinasNaoAproveitadas = !verDisciplinasNaoAproveitadas">Disciplinas não
                aproveitadas</v-btn>
        </v-col>

        <CurriculoNovo :disciplinas-cursadas="progressoAlunoGradeNova" />

        <v-row justify="center">
            <v-dialog v-model="verDisciplinasNaoAproveitadas" width="420px">
                <v-card flat>
                    <v-list>
                        <v-list-item v-for="disciplina in naoEquivalentes" :key="disciplina.Codigo">
                            <p>Nome: {{ disciplina.Nome }}</p>
                            <p>Código: {{ disciplina.Codigo }}</p>
                        </v-list-item>
                        <p class="text-center warning font-weight-bold">Consulte seu professor tutor para saber a situação das disciplinas acima e/ou <a class="text-center warning font-weight-bold link-equivalencias" href="https://docs.google.com/spreadsheets/d/1sy8dg5g71ShyxwP7jZld7-yV3u0GTqqfIPGLc33NWTA/edit" target="_blank">consulte o arquivo "Reforma: equivalências e dispensas" disponível no classroom Reforma Curricular BSI</a></p>
                    </v-list>
                </v-card>
            </v-dialog>
        </v-row>
    </v-container>
</template>
<script>
import curriculoAntigoObrigatorias from '../assets/Disciplinas Obrigatórias - Currículo antigo.json';
import curriculoAntigoOptativas from '../assets/Disciplinas Optativas - Curriculo Antigo.json';
import curriculoNovoObrigatorias from '../assets/Disciplinas Obrigatórias - Currículo novo.json';
import curriculoNovoOptativas from '../assets/Disciplinas Optativas - Curriculo Novo.json';
import dePara from '../assets/De - Para.json';
import CaixaDisciplina from '../components/CaixaDisciplina.vue';
import DetalhesDisciplina from '../components/DetalhesDisciplina.vue';

import instance from '../api/instance';
import CurriculoNovo from '../components/CurriculoNovo.vue';
import CurriculoAtual from '../components/CurriculoAtual.vue';


export default {
    name: "disciplinasCurriculoNovo",
    data() {
        return {
            disciplinasObrigatoriasCurriculoAntigo: curriculoAntigoObrigatorias.CurriculoAntigo,
            disciplinasOptativasCurriculoAntigo: curriculoAntigoOptativas.CurriculoAntigoOptativas,
            disciplinasObrigatoriasCurriculoNovo: curriculoNovoObrigatorias.CurriculoNovo,
            disciplinasOptativasCurriculoNovo: curriculoNovoOptativas.CurriculoNovoOptativas,
            disciplinasDePara: JSON.parse(JSON.stringify(dePara['De-Para'])),

            disciplinasCursadasCurriculoAntigo: [],
            periodos: 8,
            disciplinaSelecionada: null,
            disciplinasAlunoCurriculoAntigo: [],
            disciplinasAlunoCurriculoNovo: [],
            totalDisciplinasAluno: [],

            historico: [],
            progressoAlunoGrade: [],
            grade: curriculoAntigoObrigatorias.CurriculoAntigo,
            gradeNova: curriculoNovoObrigatorias.CurriculoNovo,
            progressoAlunoGradeNova: [],
            equivalencias: JSON.parse(JSON.stringify(dePara['De-Para'])),
            naoEquivalentes: [],

            verDisciplinasNaoAproveitadas: false
        }
    },

    methods: {
        async lerPlanilhaDisciplinas() {
            const arquivo = this.$refs.historico.files[0];
            const formData = new FormData();
            formData.append('file', arquivo);
            try {
                const jsonDisciplinasAluno = await instance.post("upload", formData, { headers: { 'Content-Type': 'multipart/form-data;boundary=boundary' } })
                this.disciplinasAlunoCurriculoAntigo = JSON.parse(JSON.stringify(jsonDisciplinasAluno.data.disciplinas));
                this.lerHistorico();
            } catch (error) {
                console.error(error)
                this.disciplinasAlunoCurriculoAntigo = [];
                this.disciplinasCursadasCurriculoAntigo = []
                this.disciplinasAlunoCurriculoAntigo = []
                this.disciplinasAlunoCurriculoNovo = []
                this.totalDisciplinasAluno = []
            }

        },

        lerHistorico() {
            //Pego somente as obrigatórias
            const obrigatorias = this.disciplinasObrigatoriasCurriculoAntigo.map(disciplinaCurriculoAntigo => {
                const disciplina = this.disciplinasAlunoCurriculoAntigo.findLast(discAluno => discAluno.codigo === disciplinaCurriculoAntigo.Codigo)
                if (disciplina) return { ...disciplinaCurriculoAntigo, Situacao: disciplina.situacao || disciplina.trancamento }
            }).filter(disciplina => disciplina)

            //Pego somente as optativas que o aluno passou
            const optativas = this.preencheOptativas(this.disciplinasOptativasCurriculoAntigo.map(disciplinaOptativaCurriculoAntigo => {
                const disciplina = this.disciplinasAlunoCurriculoAntigo.findLast(discAluno => discAluno.codigo === disciplinaOptativaCurriculoAntigo.Codigo)

                if (disciplina && disciplina.situacao === "Aprovado") return { ...disciplinaOptativaCurriculoAntigo, Situacao: disciplina.situacao, Tipo: "Optativa" }
            }).filter(disciplina => disciplina));

            //Pego somente as eletivas que o aluno passou
            const eletivas = this.preencheEletivas(this.disciplinasAlunoCurriculoAntigo.map(discAluno =>
                !obrigatorias.some(disciplina => disciplina?.Codigo === discAluno.codigo)
                && !optativas.some(disciplina => disciplina?.Codigo === discAluno.codigo)
                && discAluno.situacao === "Aprovado" && {
                    Codigo: discAluno.codigo,
                    Nome: discAluno.nome,
                    CargaHoraria: 60,
                    Creditos: 4,
                    Ementa: null,
                    PreRequisitos: null,
                    Situacao: "Aprovado",
                    Tipo: "Eletiva",
                    Periodo: discAluno.periodo
                }).filter(disciplina => disciplina));


            this.historico = [...obrigatorias, ...optativas, ...eletivas]
            this.fazEquivalencias([...eletivas]);
            this.progressoAlunoGrade = this.grade.map(disciplina => {

                const eletiva = disciplina.Tipo === "Eletiva" && eletivas.length && eletivas.shift();
                const optativa = disciplina.Tipo === "Optativa" && optativas.length && optativas.shift();
                if (eletiva) return eletiva;
                if (optativa) return optativa;


                const disciplinaHistorico = this.historico.find(hist => hist.Codigo === disciplina.Codigo)
                if (disciplinaHistorico) return disciplinaHistorico;

                return disciplina;
            })


        },

        preencheOptativas(disciplinas) {

            const optativas = [];
            this.disciplinasObrigatoriasCurriculoAntigo.forEach(disciplina => {
                if (disciplina?.Tipo === "Optativa") {
                    const optativa = disciplinas.shift();

                    optativa && optativas.push({ ...disciplina, Sigla: optativa.Sigla, ...optativa })
                }
            })

            return optativas;
        },

        preencheEletivas(disciplinas) {
            const eletivas = [];
            this.disciplinasObrigatoriasCurriculoAntigo.forEach(disciplina => {
                if (disciplina?.Tipo === "Eletiva") {
                    const eletiva = disciplinas.shift();
                    eletiva && eletivas.push({ ...disciplina, ...eletiva })
                }
            })

            return eletivas;
        },

        fazEquivalencias(eletivas) {
            const naoAproveitadas = [];
            const materiasDispensadas = this.calculaDispensas();

            const equivalencias = [];
            this.historico.map(disciplina => {
                const codigo = disciplina.Codigo;
                const disciplinasEquivalentes = this.equivalencias.filter(item => item.codigoCurriculoAntigo === codigo);

                if (disciplinasEquivalentes.length) {
                    disciplinasEquivalentes.forEach(disciplinaEquivalente => {
                        console.log("equivalente: ", disciplinaEquivalente, "disciplina: ", disciplina)
                        if (disciplinaEquivalente && (disciplina?.Situacao.toLowerCase().includes("aprovado") || disciplina?.Situacao.toLowerCase().includes("dispensa")) && disciplinaEquivalente?.tipoCorrespondencia?.toLowerCase().includes("equivalencia")) {
                            equivalencias.push({ ...disciplina, Codigo: disciplinaEquivalente.codigoCurriculoNovo, Nome: disciplinaEquivalente.nomeCurriculoNovo })
                        }
                        if (disciplinaEquivalente && (disciplina?.Situacao.toLowerCase().includes("aprovado") || disciplina?.Situacao.toLowerCase().includes("dispensa")) && disciplinaEquivalente?.tipoCorrespondencia?.toLowerCase().includes("dispensa") && disciplina?.Periodo === disciplinaEquivalente?.periodo) {
                            equivalencias.push({ ...disciplina, Codigo: disciplinaEquivalente.codigoCurriculoNovo, Nome: disciplinaEquivalente.nomeCurriculoNovo, Situacao: "Solicitar dispensa" })
                        }
                    })
                } else {
                    if (disciplina.Tipo !== "Eletiva" && (disciplina?.Situacao.toLowerCase().includes("aprovado") || disciplina?.Situacao.toLowerCase().includes("dispensa")) && (!materiasDispensadas[1].some(codigo => codigo === disciplina.Codigo))) {
                        naoAproveitadas.push(disciplina);
                    }
                }
            }).filter(disciplina => disciplina) // esse filter faz retornar apenas valores diferentes de undefined ou null

            const optativasGradeNova = [];
            this.disciplinasOptativasCurriculoNovo.map(optativa => {
                const equivalentes = equivalencias.filter(equivalencia => equivalencia.Codigo === optativa.Codigo);

                if (equivalentes.length) {
                    equivalentes.forEach(equivalente => {
                        optativasGradeNova.push({ ...optativa, Situacao: equivalente.Situacao, Sigla: optativa.Sigla || equivalente.Sigla })
                    })
                }
            }).filter(disciplina => disciplina)

            if (eletivas.length) {
                this.gradeNova = this.gradeNova.map(item => {
                    if (item.Tipo === "Optativa/Eletiva" && eletivas.length) {
                        const eletiva = eletivas.shift();
                        return { ...eletiva, PeriodoRecomendado: item.PeriodoRecomendado, Situacao: eletiva.Situacao }
                    }
                    return item;
                })
            }

            this.progressoAlunoGradeNova = this.gradeNova.map(item => {
                //if (materiasDispensadas[0].some(codigo => codigo === item.Codigo)) return { ...item, Situacao: "Dispensa sem nota" }
                if (materiasDispensadas[0].some(codigo => codigo === item.Codigo)) return { ...item, Situacao: "Solicitar dispensa" }

                const disciplina = equivalencias.find(equivalencia => equivalencia.Codigo === item.Codigo)

                if (item.Tipo.includes("Optativa") && item.Codigo.includes("OPT") && optativasGradeNova.length) {
                    const optativa = optativasGradeNova.shift();
                    return { ...optativa, PeriodoRecomendado: item.PeriodoRecomendado, Tipo: item.Tipo, Sigla: optativa.Sigla || item.Sigla }
                }
                if (disciplina) return { ...item, Situacao: disciplina.Situacao }
                return { ...item, Situacao: item.Situacao || "Matrícula" }
            })

            this.naoEquivalentes = [...naoAproveitadas]
            console.log(this.naoEquivalentes);
        },

        calculaDispensas() {
            const disciplinas = this.historico.filter(item => item.Sigla.toLowerCase().includes("ace"));
            const TPD = this.historico.find(item => item.Codigo === "HTD0058");
            const dispensas = [];
            const utilizadas = [];
            if (disciplinas.length === 4) {
                dispensas.push("TIN0151", "TIN0152", "TIN9999")
                utilizadas.push(disciplinas[0].Codigo, disciplinas[1].Codigo, disciplinas[2].Codigo, disciplinas[3].Codigo)
            } else if (disciplinas.length == 3) {
                dispensas.push("TIN0151", "TIN0152")
                utilizadas.push(disciplinas[0].Codigo, disciplinas[1].Codigo, disciplinas[2].Codigo)
            } else if (disciplinas.length == 2 && disciplinas.some(disciplina => disciplina.Codigo === "TIN0156" || disciplina.Codigo === "TIN0157") && TPD) {
                dispensas.push("TIN0151", "TIN9999")
                utilizadas.push(disciplinas[0].Codigo, disciplinas[1].Codigo, TPD.Codigo)
            } else if (disciplinas.length >= 1 && TPD) {
                dispensas.push("TIN0151")
                utilizadas.push(...disciplinas.map(disciplina => disciplina.Codigo), TPD.Codigo)
            }
            return [dispensas, utilizadas]
        }
    },
    components: { CaixaDisciplina, DetalhesDisciplina, CurriculoNovo, CurriculoAtual }
}
</script>

<style lang="css" scoped>
.historico {
    min-width: 80vw;
    margin-bottom: 24px;
}

.borda-coluna {
    border-right: 1px solid #BDBDBD;
}

.borda-linha {
    border-bottom: 1px solid #BDBDBD;
}

.warning {
    color: #EF5350;
}

.link-equivalencias{
    text-decoration: underline;
}

.link-equivalencias:hover {
    text-decoration: underline;
    background: #1a1a1a;
}

</style>
