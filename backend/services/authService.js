const crypto = require('crypto');
const dbModule = require('./db');

const db = dbModule.init();

function hashPassword(password) {
  return crypto.createHash('sha256').update(password).digest('hex');
}

function generateToken() {
  return crypto.randomBytes(24).toString('hex');
}

function findByEmailOrMatricula(identifier) {
  const stmt = db.prepare('SELECT * FROM users WHERE email = ? OR matricula = ? LIMIT 1');
  return stmt.get(identifier, identifier) || null;
}

function registerUser({ name, email, matricula, password }) {
  if (!email || !password || !name || !matricula) throw new Error('Todos os campos são obrigatórios');
  const exists = db.prepare('SELECT 1 FROM users WHERE email = ? OR matricula = ?').get(email, matricula);
  if (exists) {
    // determine exact conflict
    const byEmail = db.prepare('SELECT 1 FROM users WHERE email = ?').get(email);
    if (byEmail) throw new Error('Email já cadastrado');
    throw new Error('Matrícula já cadastrada');
  }
  const pwd = hashPassword(password);
  const id = crypto.randomUUID();
  const createdAt = new Date().toISOString();
  db.prepare('INSERT INTO users (id, name, email, matricula, password, createdAt) VALUES (?, ?, ?, ?, ?, ?)').run(id, name, email, matricula, pwd, createdAt);
  return { id, name, email, matricula };
}

function loginUser({ identifier, password }) {
  if (!identifier || !password) throw new Error('Credenciais incompletas');
  const stmt = db.prepare('SELECT * FROM users WHERE email = ? OR matricula = ? LIMIT 1');
  const user = stmt.get(identifier, identifier);
  if (!user) throw new Error('Usuário não encontrado');
  const pwd = hashPassword(password);
  if (pwd !== user.password) throw new Error('Senha inválida');
  const token = generateToken();
  db.prepare('UPDATE users SET token = ? WHERE id = ?').run(token, user.id);
  return { id: user.id, name: user.name, email: user.email, matricula: user.matricula, token };
}

function findByToken(token) {
  const stmt = db.prepare('SELECT * FROM users WHERE token = ? LIMIT 1');
  return stmt.get(token) || null;
}

function changePassword({ token, oldPassword, newPassword }) {
  if (!token) throw new Error('Token ausente');
  if (!oldPassword || !newPassword) throw new Error('Campos obrigatórios');
  const user = findByToken(token);
  if (!user) throw new Error('Usuário não encontrado');
  if (hashPassword(oldPassword) !== user.password) throw new Error('Senha atual incorreta');
  const pwd = hashPassword(newPassword);
  db.prepare('UPDATE users SET password = ? WHERE id = ?').run(pwd, user.id);
  return { id: user.id, name: user.name, email: user.email, matricula: user.matricula };
}

module.exports = { registerUser, loginUser, findByEmailOrMatricula, changePassword, findByToken };
