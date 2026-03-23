// =============================================
// DIGI-SCHOOL AI — Grades Routes
// GET  /api/grades?classId=1
// POST /api/grades
// POST /api/grades/bulk
// PUT  /api/grades/:id
// =============================================

import express from 'express';
import pool from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.use(requireAuth);

// ─── GET /api/grades ─────────────────────────

router.get('/', async (req, res) => {
  const { classId, studentId } = req.query;

  try {
    let query = `
      SELECT g.id, g.student_id, g.subject, g.score, g.term,
             s.name AS student_name, s.class_id
      FROM grades g
      JOIN students s ON s.id = g.student_id
      JOIN classes  c ON c.id = s.class_id
      WHERE c.teacher_id = $1
    `;
    const params = [req.teacher.id];

    if (classId) {
      query += ` AND s.class_id = $${params.length + 1}`;
      params.push(classId);
    }
    if (studentId) {
      query += ` AND g.student_id = $${params.length + 1}`;
      params.push(studentId);
    }

    query += ` ORDER BY s.name, g.subject`;

    const result = await pool.query(query, params);
    return res.json({ grades: result.rows });

  } catch (err) {
    console.error('[Grades] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── POST /api/grades ────────────────────────

router.post('/', async (req, res) => {
  const { studentId, subject, score, term } = req.body;

  if (!studentId || !subject || score == null) {
    return res.status(400).json({ message: 'studentId, subject and score are required.' });
  }

  try {
    const result = await pool.query(
      `INSERT INTO grades (student_id, subject, score, term)
       VALUES ($1, $2, $3, $4)
       ON CONFLICT (student_id, subject, term)
       DO UPDATE SET score = EXCLUDED.score
       RETURNING *`,
      [studentId, subject, score, term || 'Semester 2']
    );
    return res.status(201).json({ grade: result.rows[0] });

  } catch (err) {
    console.error('[Grades] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── POST /api/grades/bulk ───────────────────

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
        `INSERT INTO grades (student_id, subject, score, term)
         VALUES ($1, $2, $3, $4)
         ON CONFLICT (student_id, subject, term)
         DO UPDATE SET score = EXCLUDED.score`,
        [r.studentId, r.subject, r.score, r.term || 'Semester 2']
      );
    }

    await client.query('COMMIT');
    return res.status(201).json({ message: `${records.length} grades saved.` });

  } catch (err) {
    await client.query('ROLLBACK');
    console.error('[Grades] Bulk error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  } finally {
    client.release();
  }
});

// ─── PUT /api/grades/:id ─────────────────────

router.put('/:id', async (req, res) => {
  const { id } = req.params;
  const { score } = req.body;

  try {
    const result = await pool.query(
      `UPDATE grades SET score = $1 WHERE id = $2 RETURNING *`,
      [score, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Grade not found.' });
    }

    return res.json({ grade: result.rows[0] });

  } catch (err) {
    console.error('[Grades] PUT error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export default router;