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


const pump = util.promisify(pipeline);


const fastify = Fastify({ logger: true });
fastify.register(fastifyCors, { origin: "*" });
fastify.register(fastifyMultipart);

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

  fastify.listen({ port: 80, host: "0.0.0.0" }, (err, address) => {
    if (err) {
      fastify.log.error(err);
      process.exit(1);
    }
  console.log(`Servidor rodando em ${address}`);
});