// carrega variaveis de ambiente
require('dotenv').config();


const Fastify = require("fastify");
const fs = require("fs");
const path = require("path");
const fastifyCors = require("@fastify/cors");
const fastifyMultipart = require("@fastify/multipart");
const util = require("util");
const { pipeline } = require("stream");
//const readPdf = require("./services/handlerPDFContent");
//const readPdfIntegralizacao = require("./services/handlerPDFIntegralizacaoContent");
//const readPdfMigracao = require("./services/handlerPDFMigracaoContent");
const authService = require('./services/authService');
const auth2Client = require('google-auth-library').OAuth2Client;
const client = new auth2Client(process.env.GOOGLE_CLIENT_ID);


const pump = util.promisify(pipeline);

const fastify = Fastify({ logger: true });
fastify.register(fastifyCors, { origin: "*" });
fastify.register(fastifyMultipart);

// No database mode: authentication via Google only (in-memory sessions)

fastify.get('/', function (req, reply) {
    reply.send({ hello: 'opa' })
})

//fastify.post('/upload', async (req, reply) => {
//    const data = await req.file()
//    await pump(data.file, fs.createWriteStream(data.filename))
//    const disciplinas = await readPdf(data.filename);
//    try {
//        fs.unlinkSync(path.resolve(__dirname, data.filename));
//      } catch (err) {
//        throw new Error(err);
//      }
//    reply.send({ disciplinas })
//})

// Note: email/password registration/login not supported in DB-free mode

//fastify.post("/uploadIntegralizacao", async (req, reply) => {
//  const data = await req.file();
//  await pump(data.file, fs.createWriteStream(data.filename));
//  const disciplinas = await readPdfIntegralizacao(data.filename);

//  try {
//    await fs.unlinkSync(path.resolve(__dirname, data.filename));
//    reply.send({ disciplinas });
//  } catch (err) {
//    throw new Error(err);
//  }
//  reply.send({ disciplinas })
//})


//fastify.post("/uploadReforma", async (req, reply) => {
//  const data = await req.file();
//  await pump(data.file, fs.createWriteStream(data.filename));
//  const disciplinas = await readPdfMigracao(data.filename);
//
//  try {
//    await fs.unlinkSync(path.resolve(__dirname, data.filename));
//    reply.send({ disciplinas });
//  } catch (err) {
//    try { fs.unlinkSync(path.resolve(__dirname, data.filename)); } catch {}
//    fastify.log.error(err);
//    reply.status(500).send({ error: "Erro ao processar o arquivo." });
//  }
//})

// Função auxiliar para obter sessão do token
function getSessionFromToken(token) {
  return authService.getSessionByToken ? authService.getSessionByToken(token) : null;
}

// Admin upload endpoints removed in DB-free mode. Use file-storage-only approach if needed.

// Rota: POST /auth/google
fastify.post('/auth/google', async (request, reply) => {
  try {
    const { credential } = request.body;
    if (!credential) {
      fastify.log.warn('Requisição /auth/google sem credential no corpo');
      return reply.status(400).send({ error: 'Missing credential in request body' });
    }

    // Valida o token JWT do Google
    const ticket = await client.verifyIdToken({
      idToken: credential,
      audience: process.env.GOOGLE_CLIENT_ID,
    });

    const payload = ticket.getPayload();
    const { sub, email, name, picture } = payload;

    // Cria sessão em memória e retorna token
    const { user, token } = await authService.signInWithGoogle({ sub, email, name, picture });

    return reply.send({ user, token });
  } catch (err) {
    // Log completo para depuração
    fastify.log.error({ err }, 'Erro em /auth/google');
    const message = err && err.message ? err.message : 'Falha ao autenticar com Google';
    return reply.status(401).send({ error: message });
  }
});

// Debug endpoint para checar configuração e sessões
fastify.get('/auth/debug', async (request, reply) => {
  try {
    const info = {
      GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID || null,
      NODE_ENV: process.env.NODE_ENV || null
    };
    return reply.send({ ok: true, info });
  } catch (err) {
    fastify.log.error(err);
    return reply.status(500).send({ error: 'Erro no debug' });
  }
});

const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
const host = process.env.HOST || '0.0.0.0';
fastify.listen({ port, host }, (err, address) => {
  if (err) {
    fastify.log.error(err);
    process.exit(1);
  }
  fastify.log.info(`Servidor rodando em ${address}`);
});

// Permite ao usuário inserir sua matrícula após login Google
fastify.post('/auth/set-matricula', async (request, reply) => {
  try {
    const authHeader = request.headers['authorization'] || '';
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;
    const body = await request.body;
    const { matricula } = body || {};

    if (!token) return reply.status(401).send({ error: 'Token ausente' });
    if (!matricula) return reply.status(400).send({ error: 'Matrícula ausente' });

    const result = await authService.setMatricula(token, matricula);
    return reply.send({ ok: true, user: result });
  } catch (err) {
    fastify.log.error({ err }, 'Erro em /auth/set-matricula');
    const message = err && err.message ? err.message : 'Erro ao setar matrícula';
    return reply.status(400).send({ error: message });
  }
});