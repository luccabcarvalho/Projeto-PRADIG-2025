const fs = require("fs");
const path = require("path");
const pdfParse = require("pdf-parse");

const CODE_RE = /^[A-Z]{3}\d{4}$/; // código puro (sem dois pontos) para delimitar blocos

function clean(s) {
	return (s || "").replace(/\s+/g, " ").trim();
}

function deburr(s) {
	return (s || "")
		.normalize("NFD")
		.replace(/\p{Diacritic}/gu, "");
}

function isDigit1to8(line) {
	return /^([1-8])$/.test(line.trim());
}

function isDegreeSymbol(line) {
	return /^º$/.test(line.trim());
}

function readPeriodo(lines, i) {
	// procura por padrão: numero (1..8) possivelmente seguido de uma linha 'º'
	let periodo = null;
	let idx = i;
	while (idx < lines.length) {
		const t = lines[idx].trim();
		if (isDigit1to8(t)) {
			periodo = parseInt(t, 10);
			// pular símbolo º se existir
			if (idx + 1 < lines.length && isDegreeSymbol(lines[idx + 1].trim())) idx += 1;
			return { periodo, next: idx + 1 };
		}
		idx++;
	}
	return { periodo: null, next: i };
}

function readChCr(lines, i) {
	// Ex.: "60h /" em uma linha e "4T" na próxima -> normaliza para "60h/4T"
	let chCr = null;
	let idx = i;
	const buf = [];
		while (idx < lines.length && buf.length < 4) {
		const t = lines[idx].trim();
		buf.push(t);
		const joined = buf.join(" ");
			if (/\d+\s*h\s*\/\s*[0-9]+\s*[A-Za-z0-9+]+/i.test(joined)) {
			chCr = joined.replace(/\s+/g, "").replace(/\/(?!\d)/, "/");
			return { chCr, next: idx + 1 };
		}
		// também cobre caso em uma linha só (raro neste PDF)
			if (/\d+\s*h\s*\/\s*[0-9]+\s*[A-Za-z0-9+]+/i.test(t)) {
			chCr = t.replace(/\s+/g, "");
			return { chCr, next: idx + 1 };
		}
		idx++;
	}
	return { chCr, next: i };
}

function readChExt(lines, i) {
	// Ex.: "0h" ou "32h"
	if (i >= lines.length) return { chExt: null, next: i };
	const t = lines[i].trim();
	const m = t.match(/(\d+)\s*h/i);
	if (m) return { chExt: parseInt(m[1], 10), next: i + 1 };
	return { chExt: null, next: i };
}

function isCodeLine(line) {
	return CODE_RE.test(line.trim());
}

function splitDeptAndDisciplina(tokens) {
	// tokens: linhas entre Código(Proposta) e Período. Heurísticas:
	const iParen = tokens.findIndex((t) => /\([A-Z]{2,5}\)/.test(t));
	if (iParen >= 0) {
		return {
			departamento: clean(tokens.slice(0, iParen + 1).join(" ")) || null,
			disciplina: clean(tokens.slice(iParen + 1).join(" ")) || null,
		};
	}
	if (tokens.length >= 2) {
		return {
			departamento: clean(tokens[0]) || null,
			disciplina: clean(tokens.slice(1).join(" ")) || null,
		};
	}
	return { departamento: null, disciplina: clean(tokens.join(" ")) || null };
}

function takeUntil(nextIdx, predicate) {
	let idx = nextIdx.start;
	const out = [];
	while (idx < nextIdx.end) {
		const t = nextIdx.lines[idx].trim();
		if (predicate(t, idx)) break;
		out.push(nextIdx.lines[idx]);
		idx++;
	}
	return { values: out.map((s) => s.trim()).filter(Boolean), next: idx };
}

function findNextCode(lines, i) {
	for (let k = i; k < lines.length; k++) {
		if (isCodeLine(lines[k])) return k;
	}
	return lines.length;
}

function splitPrereqTipoAndTail(arr) {
	// arr: sequência após CH Ext. Regra: primeiro token curto (<=5) vira 'tipo',
	// tudo antes vira pré-requisitos, o restante vira 'tail' (p/ tipoAlteracao).
	if (!arr || arr.length === 0) return { pre: null, tipo: null, tail: [] };
	let tipo = null;
	let splitIdx = -1;
	for (let i = 0; i < arr.length; i++) {
		const t = arr[i].trim();
		if (t.length <= 5) {
			tipo = t;
			splitIdx = i;
			break;
		}
	}
	if (splitIdx === -1) return { pre: clean(arr.join(" ")) || null, tipo: null, tail: [] };
	const pre = clean(arr.slice(0, splitIdx).join(" ")) || null;
	const tail = arr.slice(splitIdx + 1);
	return { pre, tipo, tail };
}

const readPdfMigracao = async (uri) => {
	const buffer = fs.readFileSync(path.resolve(uri));
	const data = await pdfParse(buffer);
	const rawLines = data.text.split("\n").map((l) => l.trim());

	// localizar início da seção "Mapa de equivalência"
	const norm = rawLines.map((l) => deburr(l).toLowerCase());
	let startIdx = 0;
		for (let i = 0; i < norm.length; i++) {
			if (
				(norm[i].includes("situacao atual") || norm[i].includes("situação atual")) &&
				((norm[i + 1] || "").includes("situacao proposta") || (norm[i + 1] || "").includes("situação proposta"))
			) {
				// Avança até a primeira linha que seja um código; isso pula todo o cabeçalho de colunas,
				// independentemente de quebras em "Tipo de" / "alteração".
				let j = i + 1;
				while (j < norm.length && !CODE_RE.test(rawLines[j].trim())) j++;
				startIdx = j;
				break;
			}
		}

	const lines = rawLines.slice(startIdx).filter(Boolean);
	const registros = [];

	let i = 0;
	while (i < lines.length) {
		// buscar código da situação atual
		while (i < lines.length && !isCodeLine(lines[i].replace(/:$/, ""))) i++;
		if (i >= lines.length) break;
		let atualCodigo = lines[i].replace(/:$/, "");
		i++;

		// Nome atual: até encontrar período
		const nomeTokens = [];
		let tmpIdx = i;
		// captura nome até achar período (número 1-8, possivelmente seguido de º)
		while (tmpIdx < lines.length && !isDigit1to8(lines[tmpIdx])) {
			// Para evitar capturar o próximo registro por acidente, se aparecer um código antes do período,
			// interrompemos (linha malformatada). Isso é raro no layout do PDF.
			if (isCodeLine(lines[tmpIdx])) break;
			nomeTokens.push(lines[tmpIdx]);
			tmpIdx++;
		}
		let periodoAtual = null;
		if (tmpIdx < lines.length && isDigit1to8(lines[tmpIdx])) {
			periodoAtual = parseInt(lines[tmpIdx], 10);
			tmpIdx++;
			if (tmpIdx < lines.length && isDegreeSymbol(lines[tmpIdx])) tmpIdx++;
		}

		// CH/CR atual
		const { chCr: chCrAtual, next: afterChCrAtual } = readChCr(lines, tmpIdx);
		tmpIdx = afterChCrAtual;

			// CH Ext atual
			const { chExt: chExtAtual, next: afterChExtAtual } = readChExt(lines, tmpIdx);
			tmpIdx = afterChExtAtual;

				// Varre até encontrar o 'tipo' (token curto). Só depois procura o próximo código para começar a proposta.
				let preTokens = [];
				let tipoAtual = null;
				let nextCodeIdxForCurrent = -1;
				let scanIdx = tmpIdx;
				while (scanIdx < lines.length) {
					const t = lines[scanIdx].trim();
					if (tipoAtual === null && (/^\d{1,2}$/.test(t) || /^[A-Z]{1,3}$/.test(t)) && t !== "—") {
						tipoAtual = t;
						scanIdx++;
						// após encontrar tipo, o próximo código marca o início da proposta
						nextCodeIdxForCurrent = findNextCode(lines, scanIdx);
						break;
					}
					preTokens.push(lines[scanIdx]);
					scanIdx++;
				}
					if (nextCodeIdxForCurrent === -1) {
					// não achou tipo -> tenta fallback: pegar próximo código (se houver)
						nextCodeIdxForCurrent = findNextCode(lines, scanIdx);
				}
					if (nextCodeIdxForCurrent >= lines.length || !isCodeLine(lines[nextCodeIdxForCurrent].replace(/:$/, ""))) {
					break; // não há código de proposta; encerrar
				}
				const preAtual = clean(preTokens.join(" ")) || null;

				// Agora parse da situação proposta a partir do próximo código real (não código dentro de pré-requisito)
				i = nextCodeIdxForCurrent;
		let propostaCodigo = lines[i].replace(/:$/, "");
		i++;

		// tokens até período
		const beforePeriodoTokens = [];
			while (i < lines.length && !isDigit1to8(lines[i])) {
				if (isCodeLine(lines[i].replace(/:$/, ""))) break; // quebra de linha inesperada
			beforePeriodoTokens.push(lines[i]);
			i++;
		}
		let periodoProposta = null;
		if (i < lines.length && isDigit1to8(lines[i])) {
			periodoProposta = parseInt(lines[i], 10);
			i++;
			if (i < lines.length && isDegreeSymbol(lines[i])) i++;
		}

		const { departamento, disciplina } = splitDeptAndDisciplina(beforePeriodoTokens);

		const { chCr: chCrProposta, next: afterChCrProposta } = readChCr(lines, i);
		i = afterChCrProposta;

			const { chExt: chExtProposta, next: afterChExtProposta } = readChExt(lines, i);
			i = afterChExtProposta;

			// Coletar até o próximo código (início do próximo registro)
			const nextCodeIdx = findNextCode(lines, i);
			const tailTokens = lines.slice(i, nextCodeIdx).map((s) => s.trim()).filter(Boolean);

			// Split pré, tipo e tail para a "situação proposta"
			const splitPreTipoTail = (arr) => {
				const idx = arr.findIndex((t) => (/^\d{1,2}$/.test(t) || /^[A-Z]{1,3}$/.test(t)) && t !== "—");
				if (idx === -1) return { pre: clean(arr.join(" ")) || null, tipo: null, tail: [] };
				return { pre: clean(arr.slice(0, idx).join(" ")) || null, tipo: arr[idx], tail: arr.slice(idx + 1) };
			};
			const { pre: preProposta, tipo: tipoProposta, tail } = splitPreTipoTail(tailTokens);
			const tipoAlteracao = clean(tail.join(" ")) || null;

		registros.push({
			atual: {
				codigo: atualCodigo,
				nome: clean(nomeTokens.join(" ")) || null,
				periodo: periodoAtual,
				chCr: chCrAtual,
				chExt: chExtAtual,
				preRequisitos: preAtual,
				tipo: tipoAtual,
			},
			proposta: {
				codigo: propostaCodigo,
				departamento: departamento,
				nome: disciplina,
				periodo: periodoProposta,
				chCr: chCrProposta,
				chExt: chExtProposta,
				preRequisitos: preProposta,
				tipo: tipoProposta,
			},
			tipoAlteracao,
		});

		i = nextCodeIdx; // avançar para o próximo registro
	}

	return registros;
};

module.exports = readPdfMigracao;

