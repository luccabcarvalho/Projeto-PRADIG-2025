const crypto = require('crypto');

const activeSessions = new Map();

function generateToken() {
  return crypto.randomBytes(24).toString('hex');
}

function storeSession(token, user) {
  activeSessions.set(token, {
    userId: user.id,
    email: user.email,
    name: user.name,
    matricula: user.matricula,
    tipoUsuario: user.tipoUsuario || 'aluno',
    fotoPerfil: user.fotoPerfil || null,
    createdAt: Date.now()
  });
  // Expira em 24h
  setTimeout(() => activeSessions.delete(token), 24 * 60 * 60 * 1000);
}

function getSessionByToken(token) {
  return activeSessions.get(token) || null;
}

async function signInWithGoogle({ sub, email, name, picture }) {
  // Cria usuário em memória com id do Google (`sub`)
  const user = {
    id: sub,
    name: name || '',
    email: email || '',
    matricula: null,
    fotoPerfil: picture || null,
    picture: picture || null,
    tipoUsuario: 'aluno'
  };

  // Marca que precisa fornecer matrícula manualmente
  user.needsMatricula = true;

  const token = generateToken();
  storeSession(token, user);
  return { user, token };
}


async function setMatricula(token, matricula) {
  if (!token) throw new Error('Token ausente');
  if (!matricula) throw new Error('Matrícula ausente');

  const session = getSessionByToken(token);
  if (!session) throw new Error('Sessão inválida ou expirada');

  // Evita duplicação entre sessões ativas
  for (const [t, s] of activeSessions.entries()) {
    if (t === token) continue;
    if (s.matricula && s.matricula === matricula) {
      throw new Error('Matrícula já em uso por outra sessão ativa');
    }
  }

  session.matricula = matricula;
  session.needsMatricula = false;
  return {
    id: session.userId,
    name: session.name,
    email: session.email,
    matricula: session.matricula,
    fotoPerfil: session.fotoPerfil,
    picture: session.fotoPerfil,
    tipoUsuario: session.tipoUsuario,
    needsMatricula: session.needsMatricula,
  };
}

module.exports = { signInWithGoogle, getSessionByToken, registerUser, loginUser, changePassword, setMatricula };
