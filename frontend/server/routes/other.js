// =============================================
// DIGI-SCHOOL AI — Flagged Students Routes
// GET  /api/flagged
// POST /api/flagged
// PUT  /api/flagged/:id/resolve
// =============================================

import express from 'express';
import pool from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();
router.use(requireAuth);

router.get('/', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT f.id, f.type, f.reason, f.resolved, f.created_at,
              s.id AS student_id, s.name AS student_name, s.parent_email,
              c.id AS class_id, c.name AS class_name, c.color
       FROM flagged_students f
       JOIN students s ON s.id = f.student_id
       JOIN classes  c ON c.id = f.class_id
       WHERE c.teacher_id = $1 AND f.resolved = FALSE
       ORDER BY f.created_at DESC`,
      [req.teacher.id]
    );
    return res.json({ flagged: result.rows });
  } catch (err) {
    console.error('[Flagged] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

router.post('/', async (req, res) => {
  const { studentId, classId, type, reason } = req.body;
  if (!studentId || !classId || !type || !reason) {
    return res.status(400).json({ message: 'studentId, classId, type and reason are required.' });
  }
  try {
    const result = await pool.query(
      `INSERT INTO flagged_students (student_id, class_id, type, reason)
       VALUES ($1, $2, $3, $4) RETURNING *`,
      [studentId, classId, type, reason]
    );
    return res.status(201).json({ flagged: result.rows[0] });
  } catch (err) {
    console.error('[Flagged] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

router.put('/:id/resolve', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query(
      `UPDATE flagged_students SET resolved = TRUE WHERE id = $1`, [id]
    );
    return res.json({ message: 'Flag resolved.' });
  } catch (err) {
    console.error('[Flagged] Resolve error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export { router as flaggedRouter };

// =============================================
// Notifications Routes
// GET  /api/notifications
// POST /api/notifications
// =============================================

const notifRouter = express.Router();
notifRouter.use(requireAuth);

notifRouter.get('/', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT n.id, n.type, n.message, n.status, n.sent_at,
              s.name AS student_name,
              c.name AS class_name
       FROM notifications n
       JOIN students s ON s.id = n.student_id
       JOIN classes  c ON c.id = n.class_id
       WHERE n.teacher_id = $1
       ORDER BY n.sent_at DESC`,
      [req.teacher.id]
    );
    return res.json({ notifications: result.rows });
  } catch (err) {
    console.error('[Notifications] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

notifRouter.post('/', async (req, res) => {
  const { studentId, classId, type, message } = req.body;
  if (!studentId || !classId || !type || !message) {
    return res.status(400).json({ message: 'studentId, classId, type and message are required.' });
  }
  try {
    const result = await pool.query(
      `INSERT INTO notifications (student_id, class_id, teacher_id, type, message)
       VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      [studentId, classId, req.teacher.id, type, message]
    );
    return res.status(201).json({ notification: result.rows[0] });
  } catch (err) {
    console.error('[Notifications] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export { notifRouter };

// =============================================
// Voice History Routes
// GET  /api/voice
// POST /api/voice
// =============================================

const voiceRouter = express.Router();
voiceRouter.use(requireAuth);

voiceRouter.get('/', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT v.id, v.transcript, v.duration_sec, v.actions_count,
              v.actions_json, v.recorded_at,
              c.name AS class_name, c.color, c.id AS class_id
       FROM voice_history v
       JOIN classes c ON c.id = v.class_id
       WHERE v.teacher_id = $1
       ORDER BY v.recorded_at DESC`,
      [req.teacher.id]
    );
    return res.json({ history: result.rows });
  } catch (err) {
    console.error('[Voice] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

voiceRouter.post('/', async (req, res) => {
  const { classId, transcript, durationSec, actionsCount, actionsJson } = req.body;
  if (!classId || !transcript) {
    return res.status(400).json({ message: 'classId and transcript are required.' });
  }
  try {
    const result = await pool.query(
      `INSERT INTO voice_history
         (teacher_id, class_id, transcript, duration_sec, actions_count, actions_json)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [
        req.teacher.id, classId, transcript,
        durationSec   || 0,
        actionsCount  || 0,
        JSON.stringify(actionsJson || []),
      ]
    );
    return res.status(201).json({ entry: result.rows[0] });
  } catch (err) {
    console.error('[Voice] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export { voiceRouter };

// =============================================
// Lesson Log Routes
// GET  /api/lessons?classId=1
// POST /api/lessons
// =============================================

const lessonsRouter = express.Router();
lessonsRouter.use(requireAuth);

lessonsRouter.get('/', async (req, res) => {
  const { classId } = req.query;
  try {
    let query = `
      SELECT l.*, c.name AS class_name
      FROM lesson_log l
      JOIN classes c ON c.id = l.class_id
      WHERE c.teacher_id = $1
    `;
    const params = [req.teacher.id];
    if (classId) { query += ` AND l.class_id = $2`; params.push(classId); }
    query += ` ORDER BY l.date DESC`;

    const result = await pool.query(query, params);
    return res.json({ lessons: result.rows });
  } catch (err) {
    console.error('[Lessons] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

lessonsRouter.post('/', async (req, res) => {
  const { classId, date, chapter, topic, weakPoint, insight } = req.body;
  if (!classId || !date) {
    return res.status(400).json({ message: 'classId and date are required.' });
  }
  try {
    const result = await pool.query(
      `INSERT INTO lesson_log (class_id, date, chapter, topic, weak_point, insight)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [classId, date, chapter || '', topic || '', weakPoint || '', insight || '']
    );
    return res.status(201).json({ lesson: result.rows[0] });
  } catch (err) {
    console.error('[Lessons] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export { lessonsRouter };

// =============================================
// Homework Routes
// GET  /api/homework?classId=1
// POST /api/homework
// PUT  /api/homework/:id/complete
// =============================================

const homeworkRouter = express.Router();
homeworkRouter.use(requireAuth);

homeworkRouter.get('/', async (req, res) => {
  const { classId } = req.query;
  try {
    let query = `
      SELECT h.*, c.name AS class_name
      FROM homework h
      JOIN classes c ON c.id = h.class_id
      WHERE c.teacher_id = $1
    `;
    const params = [req.teacher.id];
    if (classId) { query += ` AND h.class_id = $2`; params.push(classId); }
    query += ` ORDER BY h.assigned_date DESC`;

    const result = await pool.query(query, params);
    return res.json({ homework: result.rows });
  } catch (err) {
    console.error('[Homework] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

homeworkRouter.post('/', async (req, res) => {
  const { classId, title, subject, chapter, assignedDate, dueDate } = req.body;
  if (!classId || !title || !assignedDate || !dueDate) {
    return res.status(400).json({ message: 'classId, title, assignedDate and dueDate are required.' });
  }
  try {
    const result = await pool.query(
      `INSERT INTO homework (class_id, title, subject, chapter, assigned_date, due_date)
       VALUES ($1, $2, $3, $4, $5, $6) RETURNING *`,
      [classId, title, subject || '', chapter || '', assignedDate, dueDate]
    );
    return res.status(201).json({ homework: result.rows[0] });
  } catch (err) {
    console.error('[Homework] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

homeworkRouter.put('/:id/complete', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query(
      `UPDATE homework SET status = 'completed' WHERE id = $1`, [id]
    );
    return res.json({ message: 'Homework marked as completed.' });
  } catch (err) {
    console.error('[Homework] Complete error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export { homeworkRouter };