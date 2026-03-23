// =============================================
// DIGI-SCHOOL AI — Attendance Routes
// GET  /api/attendance?classId=1&date=2026-02-21
// POST /api/attendance        (mark one student)
// POST /api/attendance/bulk   (mark multiple at once)
// =============================================

import express from 'express';
import pool from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.use(requireAuth);

// ─── GET /api/attendance/today ───────────────
// Returns all absent/late/excused records across
// all of the teacher's classes for today

router.get('/today', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT a.id, a.student_id, a.date, a.status,
              s.name  AS student_name,
              c.id    AS class_id,
              c.name  AS class_name
       FROM attendance a
       JOIN students s ON s.id = a.student_id
       JOIN classes  c ON c.id = a.class_id
       WHERE c.teacher_id = $1
         AND a.date = CURRENT_DATE
         AND a.status IN ('A','L','E')
       ORDER BY c.name, s.name`,
      [req.teacher.id]
    );
    return res.json({ attendance: result.rows });
  } catch (err) {
    console.error('[Attendance] Today error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── GET /api/attendance ─────────────────────

router.get('/', async (req, res) => {
  const { classId, date } = req.query;

  if (!classId) {
    return res.status(400).json({ message: 'classId is required.' });
  }

  try {
    const query = `
      SELECT a.id, a.student_id, a.date, a.status,
             s.name AS student_name
      FROM attendance a
      JOIN students s ON s.id = a.student_id
      WHERE a.class_id = $1
        ${date ? 'AND a.date = $2' : ''}
      ORDER BY a.date DESC, s.name ASC
    `;
    const params = date ? [classId, date] : [classId];
    const result = await pool.query(query, params);
    return res.json({ attendance: result.rows });

  } catch (err) {
    console.error('[Attendance] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── POST /api/attendance ────────────────────

router.post('/', async (req, res) => {
  const { studentId, classId, date, status } = req.body;

  if (!studentId || !classId || !date || !status) {
    return res.status(400).json({ message: 'studentId, classId, date and status are required.' });
  }

  try {
    const result = await pool.query(
      `INSERT INTO attendance (student_id, class_id, date, status)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (student_id, date)
       DO UPDATE SET status = EXCLUDED.status
       RETURNING *`,
      [studentId, classId, date, status]
    );
    return res.status(201).json({ attendance: result.rows[0] });

  } catch (err) {
    console.error('[Attendance] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── POST /api/attendance/bulk ───────────────
// Body: { records: [{ studentId, classId, date, status }, ...] }

router.post('/bulk', async (req, res) => {
  const { records } = req.body;

  if (!records || !Array.isArray(records) || records.length === 0) {
    return res.status(400).json({ message: 'records array is required.' });
  }

  const client = await pool.connect();
  try {
    await client.query('BEGIN');

    for (const r of records) {
      await client.query(
        `INSERT INTO attendance (student_id, class_id, date, status)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (student_id, date)
         DO UPDATE SET status = EXCLUDED.status`,
        [r.studentId, r.classId, r.date, r.status]
      );
    }

    await client.query('COMMIT');
    return res.status(201).json({ message: `${records.length} attendance records saved.` });

  } catch (err) {
    await client.query('ROLLBACK');
    console.error('[Attendance] Bulk error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  } finally {
    client.release();
  }
});

export default router;