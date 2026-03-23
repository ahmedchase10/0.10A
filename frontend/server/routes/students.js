// =============================================
// DIGI-SCHOOL AI — Students Routes
// GET    /api/students?classId=1
// POST   /api/students
// PUT    /api/students/:id
// DELETE /api/students/:id
// =============================================

import express from 'express';
import pool from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

// All routes require auth
router.use(requireAuth);

// ─── GET /api/students ───────────────────────

router.get('/', async (req, res) => {
  const { classId } = req.query;

  try {
    let query = `
      SELECT s.id, s.name, s.behavior, s.notes, s.parent_email, s.class_id,
             c.name AS class_name, c.color
      FROM students s
      JOIN classes c ON s.class_id = c.id
      WHERE c.teacher_id = $1
    `;
    const params = [req.teacher.id];

    if (classId) {
      query += ` AND s.class_id = $2`;
      params.push(classId);
    }

    query += ` ORDER BY s.name ASC`;

    const result = await pool.query(query, params);
    return res.json({ students: result.rows });

  } catch (err) {
    console.error('[Students] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── POST /api/students ──────────────────────

router.post('/', async (req, res) => {
  const { name, classId, behavior, notes, parentEmail } = req.body;

  if (!name || !classId) {
    return res.status(400).json({ message: 'Name and classId are required.' });
  }

  try {
    const result = await pool.query(
      `INSERT INTO students (name, class_id, behavior, notes, parent_email)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [name, classId, behavior || 'Good', notes || '', parentEmail || '']
    );
    return res.status(201).json({ student: result.rows[0] });

  } catch (err) {
    console.error('[Students] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── PUT /api/students/:id ───────────────────

router.put('/:id', async (req, res) => {
  const { id } = req.params;
  const { name, behavior, notes, parentEmail } = req.body;

  try {
    const result = await pool.query(
      `UPDATE students SET name         = COALESCE($1, name),
                           behavior     = COALESCE($2, behavior),
                           notes        = COALESCE($3, notes),
                           parent_email = COALESCE($4, parent_email)
       WHERE id = $5 RETURNING *`,
      [name, behavior, notes, parentEmail, id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Student not found.' });
    }

    return res.json({ student: result.rows[0] });

  } catch (err) {
    console.error('[Students] PUT error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── DELETE /api/students/:id ────────────────

router.delete('/:id', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query('DELETE FROM students WHERE id = $1', [id]);
    return res.json({ message: 'Student deleted.' });
  } catch (err) {
    console.error('[Students] DELETE error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export default router;