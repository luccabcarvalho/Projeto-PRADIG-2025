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

function storeSession(token, userId, email, name, matricula) {
  activeSessions.set(token, {
    userId,
    email,
    name,
    matricula,
    createdAt: Date.now()
  });
  // Auto-cleanup after 24 hours
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
    console.error('Database error:', err);
    throw err;
  }
}

async function registerUser({ name, email, matricula, password }) {
  if (!email || !password || !name || !matricula) throw new Error('Todos os campos são obrigatórios');
  
  try {
    const pool = await dbModule.getConnection();
    
    // Check if already exists
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
      .query(`INSERT INTO Alunos (name, email, matricula, password) OUTPUT INSERTED.id VALUES (@name, @email, @matricula, @password)`);
    
    const id = result.recordset[0].id;
    return { id, name, email, matricula };
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
    storeSession(token, user.id, user.email, user.name, user.matricula);
    
    return { id: user.id, name: user.name, email: user.email, matricula: user.matricula, token };
  } catch (err) {
    throw err;
  }
}

async function findByToken(token) {
  // Token-based authentication não é usado
  throw new Error('Token-based authentication não implementado');
}

async function changePassword({ token, oldPassword, newPassword }) {
  if (!token || !oldPassword || !newPassword) throw new Error('Dados incompletos');
  
  try {
    // Validate token
    const session = getSessionByToken(token);
    if (!session) throw new Error('Sessão expirada. Por favor, faça login novamente.');
    
    const pool = await dbModule.getConnection();
    
    // Verify old password
    const result = await pool.request()
      .input('userId', session.userId)
      .query(`SELECT password FROM Alunos WHERE id = @userId`);
    
    const user = result.recordset[0];
    if (!user) throw new Error('Usuário não encontrado');
    
    const hashedOldPassword = hashPassword(oldPassword);
    if (hashedOldPassword !== user.password) throw new Error('Senha atual inválida');
    
    // Update password
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
