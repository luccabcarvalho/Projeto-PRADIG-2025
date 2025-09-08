const fs = require('fs');
const path = require('path');
const pdfParse = require('pdf-parse');

const regexDisciplina = new RegExp(/^[a-zA-Z]{3}[0-9]{4}/mi);
const regexSituacao = new RegExp(/(aprovado.*|reprovado.*|matrícula.*|trancamento.*|dispensa.*)$/gmi);
const regexTrancamento = new RegExp(/(trancamento.*)$/gmi);
//Melhorar, casos de nomes de disciplina muito grandes e que acabam quebrando em duas linhas não estão sendo contemplados.
const regexNomeDisciplina = new RegExp(/[a-zA-Z]{3}[0-9]{4}([A-Za-záãÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇç\s]*)/gmi);
const regexPegaPeriodo = new RegExp(/(\d+)\s*$/);
const regexPegaCursoFerias = new RegExp(/(Curso de Férias de [0-9]{4})/gmi);
const regexPegaSemestre = new RegExp(/^[0-9]{1}/gmi);
const regexPegaAno = new RegExp(/[0-9]{4}/gmi);

const criaVetorDisciplinas = (disciplinas) => {
  const vetorDisciplinas = disciplinas.map(disciplina => ({
    codigo: disciplina.disciplina.match(regexDisciplina)?.toString(),
    situacao: disciplina.disciplina.match(regexSituacao)?.toString(),
    trancamento: disciplina.disciplina.match(regexTrancamento)?.toString(),
    nome: disciplina.disciplina.match(regexNomeDisciplina)?.toString().split(regexDisciplina)[1]?.trim(),
    periodo: disciplina.disciplina.match(regexPegaPeriodo)?.toString()
  }));
  return vetorDisciplinas;
};


const readPdf = async (uri) => {

    const buffer = fs.readFileSync(path.resolve(__dirname, "../" + uri));

    try {
        const data = await pdfParse(buffer);

        const splitted = data.text.split('\n')
        let periodo = "";

        let disciplinas = [];
        for (let i = 0; i < splitted.length; i++) {
            if (regexTrancamento.test(splitted[i])) {
                continue;
            }

            if (regexPegaPeriodo.test(splitted[i])){
                periodo = splitted[i].match(regexPegaAno).toString() + "." + splitted[i].match(regexPegaSemestre)
            }

        
            if (regexDisciplina.test(splitted[i]) && regexSituacao.test(splitted[i])) {
                disciplinas.push({ disciplina: splitted[i], periodo });
                continue;
            }

            if (regexDisciplina.test(splitted[i])) {
                let disciplina = '';
                let j = i;
                do {
                    disciplina += splitted[j];
                    j++;
                } while (!regexSituacao.test(splitted[j - 1]));
                disciplinas.push({ disciplina, periodo });
            }
        }
        return criaVetorDisciplinas(disciplinas);
    } catch (err) {
        throw new Error(err);
    }
}
module.exports = readPdf;