// =============================================
// DIGI-SCHOOL AI — Database Schema
// Run once: node server/schema.js
// =============================================

import pool from './db.js';

const schema = `

  -- ── Teachers ──────────────────────────────
  CREATE TABLE IF NOT EXISTS teachers (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    initials   VARCHAR(5)   NOT NULL,
    email      VARCHAR(150) NOT NULL UNIQUE,
    password   TEXT         NOT NULL,
    subject    VARCHAR(100),
    school     VARCHAR(150),
    grades     VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW()
  );

  -- ── Classes ───────────────────────────────
  CREATE TABLE IF NOT EXISTS classes (
    id         SERIAL PRIMARY KEY,
    teacher_id INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
    name       VARCHAR(100) NOT NULL,
    period     VARCHAR(50),
    room       VARCHAR(50),
    color      VARCHAR(10) DEFAULT '#40916c',
    created_at TIMESTAMP DEFAULT NOW()
  );

  -- ── Students ──────────────────────────────
  CREATE TABLE IF NOT EXISTS students (
    id         SERIAL PRIMARY KEY,
    class_id   INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    name       VARCHAR(100) NOT NULL,
    behavior   VARCHAR(50)  DEFAULT 'Good',
    notes      TEXT         DEFAULT '',
    created_at TIMESTAMP DEFAULT NOW(),
    parent_email VARCHAR(150) 
  );

  -- ── Attendance ────────────────────────────
  CREATE TABLE IF NOT EXISTS attendance (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER REFERENCES students(id) ON DELETE CASCADE,
    class_id    INTEGER REFERENCES classes(id)  ON DELETE CASCADE,
    date        DATE    NOT NULL,
    status      CHAR(1) NOT NULL CHECK (status IN ('P','A','L','E')),
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, date)
  );

  -- ── Grades ────────────────────────────────
  CREATE TABLE IF NOT EXISTS grades (
    id         SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    subject    VARCHAR(100) NOT NULL,
    score      NUMERIC(4,1) NOT NULL CHECK (score >= 0 AND score <= 20),
    term       VARCHAR(50)  DEFAULT 'Semester 2',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (student_id, subject, term)
  );

  -- ── Lesson Log ────────────────────────────
  CREATE TABLE IF NOT EXISTS lesson_log (
    id          SERIAL PRIMARY KEY,
    class_id    INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    date        DATE        NOT NULL,
    chapter     VARCHAR(200),
    topic       VARCHAR(200),
    weak_point  TEXT        DEFAULT '',
    insight     TEXT        DEFAULT '',
    created_at  TIMESTAMP DEFAULT NOW()
  );

  -- ── Homework ──────────────────────────────
  CREATE TABLE IF NOT EXISTS homework (
    id            SERIAL PRIMARY KEY,
    class_id      INTEGER REFERENCES classes(id) ON DELETE CASCADE,
    title         VARCHAR(200) NOT NULL,
    subject       VARCHAR(100),
    chapter       VARCHAR(200),
    assigned_date DATE         NOT NULL,
    due_date      DATE         NOT NULL,
    status        VARCHAR(20)  DEFAULT 'active' CHECK (status IN ('active','completed')),
    created_at    TIMESTAMP DEFAULT NOW()
  );

  -- ── Flagged Students ──────────────────────
  CREATE TABLE IF NOT EXISTS flagged_students (
    id         SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    class_id   INTEGER REFERENCES classes(id)  ON DELETE CASCADE,
    type       VARCHAR(20) NOT NULL CHECK (type IN ('behavior','absence','grade')),
    reason     TEXT        NOT NULL,
    resolved   BOOLEAN     DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
  );

  -- ── Notifications ─────────────────────────
  CREATE TABLE IF NOT EXISTS notifications (
    id          SERIAL PRIMARY KEY,
    student_id  INTEGER REFERENCES students(id) ON DELETE CASCADE,
    class_id    INTEGER REFERENCES classes(id)  ON DELETE CASCADE,
    teacher_id  INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
    type        VARCHAR(20) NOT NULL CHECK (type IN ('behavior','absence','grade')),
    message     TEXT        NOT NULL,
    status      VARCHAR(20) DEFAULT 'sent',
    sent_at     TIMESTAMP DEFAULT NOW()
  );

  -- ── Voice History ─────────────────────────
  CREATE TABLE IF NOT EXISTS voice_history (
    id            SERIAL PRIMARY KEY,
    teacher_id    INTEGER REFERENCES teachers(id) ON DELETE CASCADE,
    class_id      INTEGER REFERENCES classes(id)  ON DELETE CASCADE,
    transcript    TEXT        NOT NULL,
    duration_sec  INTEGER,
    actions_count INTEGER     DEFAULT 0,
    actions_json  JSONB       DEFAULT '[]',
    recorded_at   TIMESTAMP DEFAULT NOW()
  );

`;

async function runSchema() {
  const client = await pool.connect();
  try {
    console.log('[Schema] Creating tables...');
    await client.query(schema);
    console.log('[Schema] All tables created successfully ✓');
  } catch (err) {
    console.error('[Schema] Error:', err.message);
  } finally {
    client.release();
    pool.end();
  }
}

runSchema();