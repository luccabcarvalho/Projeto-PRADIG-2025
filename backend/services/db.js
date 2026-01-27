const Database = require('better-sqlite3');
const path = require('path');
const fs = require('fs');

const DB_DIR = path.resolve(__dirname, '..', 'data');
const DB_FILE = path.resolve(DB_DIR, 'samg.db');
const USERS_JSON = path.resolve(__dirname, '..', 'users.json');

function ensureDir() {
  if (!fs.existsSync(DB_DIR)) fs.mkdirSync(DB_DIR, { recursive: true });
}

function init() {
  ensureDir();
  const db = new Database(DB_FILE);
  db.pragma('journal_mode = WAL');

  db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      matricula TEXT UNIQUE NOT NULL,
      password TEXT NOT NULL,
      token TEXT,
      createdAt TEXT
    );
  `);

  // Migrate users.json if present
  if (fs.existsSync(USERS_JSON)) {
    try {
      const raw = fs.readFileSync(USERS_JSON, 'utf-8');
      const users = JSON.parse(raw || '[]');
      const insert = db.prepare('INSERT OR IGNORE INTO users (id, name, email, matricula, password, token, createdAt) VALUES (?, ?, ?, ?, ?, ?, ?)');
      const now = new Date().toISOString();
      const txn = db.transaction((rows) => {
        for (const u of rows) {
          insert.run(u.id, u.name, u.email, u.matricula, u.password, u.token || null, now);
        }
      });
      txn(users);
      // Optionally rename the old file as backup
      try { fs.renameSync(USERS_JSON, USERS_JSON + '.bak'); } catch (e) { /* ignore */ }
    } catch (err) {
      console.error('Failed to migrate users.json:', err.message);
    }
  }

  return db;
}

module.exports = { init };
