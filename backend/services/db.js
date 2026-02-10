const sql = require('mssql');

// Build config with support for Windows Authentication or SQL Auth
const buildConfig = () => {
  const config = {
    server: process.env.DB_SERVER || 'localhost',
    database: process.env.DB_NAME || 'samg',
    options: {
      encrypt: process.env.DB_ENCRYPT === 'true' || false,
      trustServerCertificate: true,
      port: parseInt(process.env.DB_PORT || '1433')
    }
  };

  // Determine authentication type based on DB_USER
  const dbUser = (process.env.DB_USER || '').trim();
  const isWindowsAuth = !dbUser || dbUser.toLowerCase() === 'windows';

  if (isWindowsAuth && process.env.WINDOWS_USER) {
    // Windows authentication with NTLM (if WINDOWS_USER is specified)
    config.options.integratedSecurity = true;
    config.authentication = {
      type: 'ntlm',
      options: {
        domain: process.env.WINDOWS_DOMAIN || '.',
        userName: process.env.WINDOWS_USER,
        password: process.env.WINDOWS_PASSWORD || ''
      }
    };
  } else if (isWindowsAuth) {
    // Windows authentication (integratedSecurity only, no explicit credentials)
    config.options.integratedSecurity = true;
  } else {
    // SQL Server authentication (with username and password)
    config.authentication = {
      type: 'default',
      options: {
        userName: dbUser,
        password: process.env.DB_PASSWORD || ''
      }
    };
  }

  return config;
};

const config = buildConfig();

// Debug: Log config authentication info
console.log('DB Config:', {
  server: config.server,
  database: config.database,
  port: config.options.port,
  integratedSecurity: config.options.integratedSecurity,
  authentication: config.authentication ? config.authentication.type : 'Windows (integratedSecurity)'
});

let connectionPool = null;

async function init() {
  try {
    connectionPool = new sql.ConnectionPool(config);
    await connectionPool.connect();
    console.log('SQL Server connection established');

    const request = connectionPool.request();
    
    // Create Alunos table if it doesn't exist
    await request.query(`
      IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Alunos' and xtype='U')
      BEGIN
        CREATE TABLE Alunos (
          id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
          name NVARCHAR(255) NOT NULL,
          email NVARCHAR(255) UNIQUE NOT NULL,
          matricula NVARCHAR(255) UNIQUE NOT NULL,
          password NVARCHAR(255) NOT NULL,
          token NVARCHAR(255),
          createdAt DATETIME DEFAULT GETDATE()
        );
      END
    `);
    console.log('Alunos table verified/created');

    return connectionPool;
  } catch (err) {
    console.error('Database initialization error:', err);
    throw err;
  }
}

async function getConnection() {
  if (!connectionPool) {
    await init();
  }
  return connectionPool;
}

async function close() {
  if (connectionPool) {
    await connectionPool.close();
    connectionPool = null;
  }
}

module.exports = { init, getConnection, close };

