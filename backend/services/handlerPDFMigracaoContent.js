const fs = require('fs');
const path = require('path');

const regexCodigoDisciplina = /[A-Z]{3}[0-9]{4}/g;

const readMapaEquivalencia = (uri) => {
  const text = fs.readFileSync(path.resolve(uri), 'utf8');

  // Extrair bloco do mapa de equivalência pelo título e fim da seção
  const inicio = text.search(/III\s+Mapa de equivalênciaos/i);
  if (inicio === -1) {
    console.warn("Mapa de equivalência não encontrado");
    return null;
  }
  const fim = text.slice(inicio).search(/IV\s+Termo de compromisso/i);
  const bloco = fim !== -1 ? text.slice(inicio, inicio + fim) : text.slice(inicio);

  // Dividir em linhas e filtrar linhas que tenham pelo menos 2 códigos de disciplinas
  const linhas = bloco.split('\n').map(l => l.trim()).filter(l => {
    const encontrados = l.match(regexCodigoDisciplina);
    return encontrados && encontrados.length >= 2;
  });

  // Função para agrupar disciplinas por período (fixo 1 pois não há info clara)
  const periodos = [];

  function garantirPeriodo(periodo) {
    let pObj = periodos.find(p => p.periodo === periodo);
    if (!pObj) {
      pObj = { periodo, disciplinas: [] };
      periodos.push(pObj);
    }
    return pObj;
  }

  linhas.forEach(line => {
    const codigos = line.match(regexCodigoDisciplina);
    const idxAntigo = line.indexOf(codigos[0]);
    const idxNovo = line.indexOf(codigos[1]);

    const nomeAntigo = line.substring(idxAntigo + codigos[0].length, idxNovo).trim().replace(/\s\s+/g, ' ');
    const nomeNovo = line.substring(idxNovo + codigos[1].length).trim().replace(/\s\s+/g, ' ');

    const tipoAlteracaoMatch = line.match(/exclusão|criação|mudança|inclu[sã]o/i);

    const periodo = 1;

    const periodoObj = garantirPeriodo(periodo);
    periodoObj.disciplinas.push({
      codigoAntigo: codigos[0],
      nomeAntigo,
      codigoNovo: codigos[1],
      nomeNovo,
      tipoAlteracao: tipoAlteracaoMatch ? tipoAlteracaoMatch[0] : 'sem info'
    });
  });

  // Ordenar períodos (apesar de fixo 1)
  periodos.sort((a, b) => a.periodo - b.periodo);

  return { disciplinas: periodos };
};

module.exports = readMapaEquivalencia;
