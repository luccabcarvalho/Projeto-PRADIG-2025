const crypto = require('crypto');
const dbModule = require('./db');

// In-memory token store (for production, use a database or Redis)
const activeSessions = new Map();

function hashPassword(password) {
  // Store password as plain text (no hashing)
  return password;
}

function generateToken() {
  return crypto.randomBytes(24).toString('hex');
}

function storeSession(token, userId, email, name, matricula, tipoUsuario = 'aluno') {
  activeSessions.set(token, {
    userId,
    email,
    name,
    matricula,
    tipoUsuario,
    createdAt: Date.now()
  });
  // Limpeza de sessão 24h
  setTimeout(() => {
    activeSessions.delete(token);
  }, 24 * 60 * 60 * 1000);
}

function getSessionByToken(token) {
  return activeSessions.get(token) || null;
}

async function findByEmailOrMatricula(identifier) {
  try {
    const pool = await dbModule.getConnection();
    const result = await pool.request()
      .input('identifier', identifier)
      .query(`SELECT * FROM Alunos WHERE email = @identifier OR matricula = @identifier`);
    return result.recordset[0] || null;
  } catch (err) {
    console.error('Erro no database:', err);
    throw err;
  }
}

async function registerUser({ name, email, matricula, password, tipoUsuario = 'aluno' }) {
  if (!email || !password || !name || !matricula) throw new Error('Todos os campos são obrigatórios');
  //if (!['aluno', 'adm'].includes(tipoUsuario)) throw new Error('Tipo de usuário inválido');
  
  try {
    const pool = await dbModule.getConnection();
    
    
    const checkResult = await pool.request()
      .input('email', email)
      .input('matricula', matricula)
      .query(`SELECT 1 FROM Alunos WHERE email = @email OR matricula = @matricula`);
    
    if (checkResult.recordset.length > 0) {
      const byEmail = await pool.request()
        .input('email', email)
        .query(`SELECT 1 FROM Alunos WHERE email = @email`);
      if (byEmail.recordset.length > 0) throw new Error('Email já cadastrado');
      throw new Error('Matrícula já cadastrada');
    }
    
    const pwd = hashPassword(password);
    
    const result = await pool.request()
      .input('name', name)
      .input('email', email)
      .input('matricula', matricula)
      .input('password', pwd)
      .input('tipoUsuario', tipoUsuario)
      .query(`INSERT INTO Alunos (name, email, matricula, password, tipo_usuario) OUTPUT INSERTED.id VALUES (@name, @email, @matricula, @password, @tipoUsuario)`);
    
    const id = result.recordset[0].id;
    return { id, name, email, matricula, tipoUsuario };
  } catch (err) {
    throw err;
  }
}
async function loginUser({ identifier, password }) {
  if (!identifier || !password) throw new Error('Credenciais incompletas');
  
  try {
    const pool = await dbModule.getConnection();
    const result = await pool.request()
      .input('identifier', identifier)
      .query(`SELECT * FROM Alunos WHERE email = @identifier OR matricula = @identifier`);
    
    const user = result.recordset[0];
    if (!user) throw new Error('Usuário não encontrado');
    
    const pwd = hashPassword(password);
    if (pwd !== user.password) throw new Error('Senha inválida');
    
    const token = generateToken();
    const tipoUsuario = user.tipo_usuario || 'aluno';
    storeSession(token, user.id, user.email, user.name, user.matricula, tipoUsuario);
    
    return { id: user.id, name: user.name, email: user.email, matricula: user.matricula, tipoUsuario, token };
  } catch (err) {
    throw err;
  }
}


async function findByToken(token) {
  throw new Error('Token-based authentication não implementado');
}

async function changePassword({ token, oldPassword, newPassword }) {
  if (!token || !oldPassword || !newPassword) throw new Error('Dados incompletos');
  
  try {   
    const session = getSessionByToken(token);
    if (!session) throw new Error('Sessão expirada. Por favor, faça login novamente.');
    
    const pool = await dbModule.getConnection();
    
    
    const result = await pool.request()
      .input('userId', session.userId)
      .query(`SELECT password FROM Alunos WHERE id = @userId`);
    
    const user = result.recordset[0];
    if (!user) throw new Error('Usuário não encontrado');
    
    const hashedOldPassword = hashPassword(oldPassword);
    if (hashedOldPassword !== user.password) throw new Error('Senha atual inválida');
    
    const hashedNewPassword = hashPassword(newPassword);
    await pool.request()
      .input('userId', session.userId)
      .input('newPassword', hashedNewPassword)
      .query(`UPDATE Alunos SET password = @newPassword WHERE id = @userId`);
    
    return { id: session.userId, name: session.name, email: session.email, matricula: session.matricula };
  } catch (err) {
    throw err;
  }
}

module.exports = { registerUser, loginUser, findByEmailOrMatricula, changePassword, findByToken };
