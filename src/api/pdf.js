const express = require("express");
const multer = require("multer");
const PDFParser = require("pdf2json");
const fs = require("fs");

const upload = multer({ dest: "uploads/" });
const app = express();

// Função utilitária para extrair linhas de texto do pdf2json
function extrairLinhas(pdfData) {
  const pages = pdfData.formImage.Pages;
  const linhas = [];

  pages.forEach((page) => {
    const linhasPagina = {};
    page.Texts.forEach((textObj) => {
      const y = textObj.y.toFixed(2);
      const texto = decodeURIComponent(textObj.R[0].T);
      if (!linhasPagina[y]) linhasPagina[y] = [];
      linhasPagina[y].push({ x: textObj.x, texto });
    });
    Object.values(linhasPagina).forEach((linha) => {
      linha.sort((a, b) => a.x - b.x);
      const linhaTexto = linha.map(t => t.texto).join(' ');
      linhas.push(linhaTexto);
    });
  });

  return linhas;
}
// Exemplo básico para encontrar bloco do mapa e extrair códigos das linhas
function encontrarMapaEquivalencia(linhas) {
  const inicio = linhas.findIndex(l => l.includes('III') && l.toLowerCase().includes('equivalência'));
  // Pode ajustar o fim dependendo do layout
  const fim = linhas.findIndex((l, i) => i>inicio && (l.startsWith('IV') || l.toLowerCase().includes('referências')));
  // Recorte do bloco
  const blocoMapa = linhas.slice(inicio, fim>-1?fim:linhas.length);
  // Filtra linhas que parecem tabela (ajuste regex conforme layout real)
  const tabelaMapa = blocoMapa.filter(linha => linha.match(/([A-Z]{3,}\\d{3,})/));
  // Parse para objeto
  return tabelaMapa.map(linha => {
    // Exemplo regex, ajuste conforme o padrão da tabela no PDF real
    const match = linha.match(/([A-Z]{3,}\\d{3,})\\s+([^\\d]+)\\s+(\\d[ºo])?.*([A-Z]{3,}\\d{3,})\\s+([^\\d]+)\\s+(\\d[ºo])?/);
    if(match)
      return {
        cod_atual: match[1], nome_atual: match[2].trim(), periodo_atual: match[3],
        cod_proposto: match[4], nome_proposto: match[5].trim(), periodo_proposto: match[6]
      }
    return null;
  }).filter(x=>x);
}


app.post("/upload", upload.single("pdf"), (req, res) => {

const pdfParser = new PDFParser();


  if (!req.file) {
    return res.status(400).json({ error: "Nenhum arquivo enviado." });
  }

  
  pdfParser.on("pdfParser_dataError", errData => {
    fs.unlink(req.file.path, () => {}); // Remove arquivo temporário
    res.status(500).json({ error: errData.parserError });
  });

  pdfParser.on("pdfParser_dataReady", pdfData => {
    fs.unlink(req.file.path, () => {}); // Remove arquivo temporário

    // Extrai linhas de texto do PDF
    const linhas = extrairLinhas(pdfData);

    // Retorna as linhas como JSON
    res.json({ linhas });
  });

  pdfParser.loadPDF(req.file.path);
});

app.listen(3000, () => console.log("Servidor rodando na porta 3000"));
