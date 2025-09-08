const fs = require("fs");
const path = require("path");
const pdfParse = require("pdf-parse");

const regexCodigoDisciplina = /[A-Z]{3}[0-9]{4}/;
const regexPeriodo = /(\d+º)/; // ex: "2º", "6º"

const readMapaEquivalencia = async (uri) => {
  const buffer = fs.readFileSync(path.resolve(uri));

  try {
    const data = await pdfParse(buffer);
    const lines = data.text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    let dentroMapa = false;
    const bloco = [];

    // 1. Captura só o trecho do Mapa de Equivalência
    for (const linha of lines) {
      if (/III\s+Mapa\s+de\s+equival[eê]ncia/i.test(linha)) {
        dentroMapa = true;
        continue;
      }
      if (/IV\s+Termo\s+de\s+compromisso/i.test(linha)) {
        dentroMapa = false;
      }
      if (dentroMapa) {
        bloco.push(linha);
      }
    }

    // 2. Captura entradas (cada disciplina antiga e nova)
    const entradas = [];
    for (let i = 0; i < bloco.length; i++) {
      const linha = bloco[i];
      const match = linha.match(regexCodigoDisciplina);

      if (match) {
        const codigo = match[0];
        let nome = linha.replace(codigo, "").trim();

        // junta linhas seguintes até aparecer outro código ou "Tipo de alteração"
        let j = i + 1;
        while (
          j < bloco.length &&
          !regexCodigoDisciplina.test(bloco[j]) &&
          !/Tipo\s+de\s+alteração/i.test(bloco[j])
        ) {
          nome += " " + bloco[j];
          j++;
        }

        // remove "Departamento (...)"
        nome = nome.replace(/Informática Aplicada.*?\)/i, "").trim();

        // captura período se existir
        const periodoMatch = nome.match(regexPeriodo);
        const periodo = periodoMatch ? periodoMatch[1] : "Não informado";

        entradas.push({ codigo, nome: nome.trim(), periodo });
      }
    }

    // 3. Monta os pares (cada linha da tabela = 1 antigo + 1 novo)
    const disciplinas = [];
    for (let i = 0; i < entradas.length; i += 2) {
      const antigo = entradas[i];
      const novo = entradas[i + 1];
      if (!novo) continue;

      // pega algumas linhas próximas para identificar o tipo de alteração
      const afterLines = bloco.slice(i, i + 10).join(" ");
      const tipoAlteracaoMatch = afterLines.match(
        /(criação|exclusão|mudança|inclu[sã]o)([^.]*)/i
      );

      disciplinas.push({
        codigoAntigo: antigo.codigo,
        nomeAntigo: antigo.nome,
        periodoAntigo: antigo.periodo,
        codigoNovo: novo.codigo,
        nomeNovo: novo.nome,
        periodoNovo: novo.periodo,
        tipoAlteracao: tipoAlteracaoMatch
          ? tipoAlteracaoMatch[0].trim()
          : "sem info",
      });
    }

    return { disciplinas: { disciplinas } };
  } catch (err) {
    throw new Error(err);
  }
};

module.exports = readMapaEquivalencia;
