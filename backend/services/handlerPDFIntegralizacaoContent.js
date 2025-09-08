const fs = require("fs");
const path = require("path");
const pdfParse = require("pdf-parse");

const regexCodigoDisciplina = /[A-Z]{3}[0-9]{4}/;
const regexSituacao = /(Vencido|Não Vencido|Matricula\/Cursando)/i;
const regexNumeros = /\d+/g;

const readPdfIntegralizacao = async (uri) => {
  const buffer = fs.readFileSync(path.resolve(uri));

  try {
    const data = await pdfParse(buffer);
    const lines = data.text
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);

    let periodos = [];

    const garantirPeriodo = (periodo) => {
      if (!periodos.find(p => p.periodo === periodo)) {
    periodos.push({ periodo, disciplinas: [] });
    };
  }
    for (const linha of lines) {
      const codigoMatch = linha.match(regexCodigoDisciplina);
      const situacaoMatch = linha.match(regexSituacao);

      if (codigoMatch && situacaoMatch) {
        const codigo = codigoMatch[0];
        const situacao = situacaoMatch[0];

        const nome = linha.slice(0, linha.indexOf(codigo)).trim();

        // Tenta extrair o último número da linha como período (entre 1 e 12)
        const numeros = linha.match(/\d+/g) || [];
        let periodo = "Não informado";

        if (numeros.length >= 1) {
          const ultimoNumero = numeros[numeros.length - 1]; // Ex: "14"
          const primeiroDigito = parseInt(ultimoNumero[0], 10); // Ex: 1

          if (primeiroDigito >= 1 && primeiroDigito <= 8) {
            periodo = primeiroDigito;
          }
        }


        garantirPeriodo(periodo);
        const periodoObj = periodos.find(p => p.periodo === periodo);
        periodoObj.disciplinas.push({
          codigo,
          nome,
          situacao,
          periodo,
        });
      } else {
        //console.warn("⚠️ Linha ignorada (sem código ou situação):", linha);
      }
    }

    // Ordena os períodos
    periodos.sort((a, b) => {
      if (typeof a.periodo === "number" && typeof b.periodo === "number") {
        return a.periodo - b.periodo;
      }
      if (typeof a.periodo === "number") return -1;
      if (typeof b.periodo === "number") return 1;
      return 0;
    });

    return periodos;
  } catch (err) {
    throw new Error(err);
  }
};

module.exports = readPdfIntegralizacao;
