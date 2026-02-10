// Load environment variables
require('dotenv').config();

const Fastify = require("fastify");
const fs = require("fs");
const path = require("path");
const fastifyCors = require("@fastify/cors");
const fastifyMultipart = require("@fastify/multipart");
const util = require("util");
const { pipeline } = require("stream");
const readPdf = require("./services/handlerPDFContent");
const readPdfIntegralizacao = require("./services/handlerPDFIntegralizacaoContent");
const readPdfMigracao = require("./services/handlerPDFMigracaoContent");
const authService = require('./services/authService');
const dbModule = require('./services/db');

const pump = util.promisify(pipeline);

const fastify = Fastify({ logger: true });
fastify.register(fastifyCors, { origin: "*" });
fastify.register(fastifyMultipart);

// Initialize database
fastify.register(async function(fastify) {
  try {
    await dbModule.init();
    console.log('Database initialized successfully');
  } catch (err) {
    fastify.log.error('Failed to initialize DB: ' + err.message);
    throw err;
  }
});

fastify.get('/', function (req, reply) {
    reply.send({ hello: 'opa' })
})

fastify.post('/upload', async (req, reply) => {
    const data = await req.file()
    await pump(data.file, fs.createWriteStream(data.filename))
    const disciplinas = await readPdf(data.filename);
    try {
        fs.unlinkSync(path.resolve(__dirname, data.filename));
      } catch (err) {
        throw new Error(err);
      }
    reply.send({ disciplinas })
})

fastify.post('/auth/register', async (req, reply) => {
  try {
    const body = await req.body;
    const user = await authService.registerUser(body);
    reply.send({ user });
  } catch (err) {
    reply.status(400).send({ error: err.message });
  }
});

fastify.post('/auth/login', async (req, reply) => {
  try {
    const body = await req.body;
    // support identifier email or matricula
    const identifier = body.email || body.matricula || body.identifier;
    const password = body.password || body.senha;
    const user = await authService.loginUser({ identifier, password });
    reply.send({ user });
  } catch (err) {
    reply.status(401).send({ error: err.message });
  }
});

// Change password using Bearer token
fastify.post('/auth/change-password', async (req, reply) => {
  try {
    const authHeader = req.headers['authorization'] || '';
    const token = authHeader.startsWith('Bearer ') ? authHeader.slice(7) : authHeader;
    const body = await req.body;
    const { oldPassword, newPassword } = body;
    const user = await authService.changePassword({ token, oldPassword, newPassword });
    reply.send({ user });
  } catch (err) {
    reply.status(400).send({ error: err.message });
  }
});

fastify.post("/uploadIntegralizacao", async (req, reply) => {
  const data = await req.file();
  await pump(data.file, fs.createWriteStream(data.filename));
  const disciplinas = await readPdfIntegralizacao(data.filename);

  try {
    await fs.unlinkSync(path.resolve(__dirname, data.filename));
    reply.send({ disciplinas });
  } catch (err) {
    throw new Error(err);
  }
  reply.send({ disciplinas })
})


fastify.post("/uploadReforma", async (req, reply) => {
  const data = await req.file();
  await pump(data.file, fs.createWriteStream(data.filename));
  const disciplinas = await readPdfMigracao(data.filename);

  try {
    await fs.unlinkSync(path.resolve(__dirname, data.filename));
    reply.send({ disciplinas });
  } catch (err) {
    try { fs.unlinkSync(path.resolve(__dirname, data.filename)); } catch {}
    fastify.log.error(err);
    reply.status(500).send({ error: "Erro ao processar o arquivo." });
  }
})

  const port = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;
  const host = process.env.HOST || '0.0.0.0';
  fastify.listen({ port, host }, (err, address) => {
    if (err) {
      fastify.log.error(err);
      process.exit(1);
    }
  console.log(`Servidor rodando em ${address}`);
});