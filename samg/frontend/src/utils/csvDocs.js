const csvDocs = import.meta.glob('@docs/**/*.csv', { query: '?raw', import: 'default', eager: true });

export function getCsvDocsDisponiveis() {
  const csvDisponiveis = {};

  for (const path in csvDocs) {
    const nome = path.split('/').pop().replace(/\.csv$/i, '');
    csvDisponiveis[nome] = csvDocs[path];
  }

  return csvDisponiveis;
}

function normalizeText(value) {
  return String(value || '')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim();
}
