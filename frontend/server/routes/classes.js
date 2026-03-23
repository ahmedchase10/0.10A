// =============================================
// DIGI-SCHOOL AI — Classes Routes
// GET    /api/classes
// POST   /api/classes
// PUT    /api/classes/:id
// DELETE /api/classes/:id
// =============================================

import express from 'express';
import pool from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

router.use(requireAuth);

// ─── GET /api/classes ────────────────────────

router.get('/', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT c.*,
              COUNT(s.id)::int AS total_students,
              COUNT(CASE WHEN a.status = 'P' AND a.date = CURRENT_DATE THEN 1 END)::int AS present_today
       FROM classes c
       LEFT JOIN students s   ON s.class_id = c.id
       LEFT JOIN attendance a ON a.class_id = c.id AND a.date = CURRENT_DATE
       WHERE c.teacher_id = $1
       GROUP BY c.id
       ORDER BY c.name ASC`,
      [req.teacher.id]
    );
    return res.json({ classes: result.rows });

  } catch (err) {
    console.error('[Classes] GET error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── POST /api/classes ───────────────────────

router.post('/', async (req, res) => {
  const { name, period, room, color } = req.body;

  if (!name) {
    return res.status(400).json({ message: 'Class name is required.' });
  }

  try {
    const result = await pool.query(
      `INSERT INTO classes (teacher_id, name, period, room, color)
       VALUES ($1, $2, $3, $4, $5) RETURNING *`,
      [req.teacher.id, name, period || '', room || '', color || '#40916c']
    );
    return res.status(201).json({ class: result.rows[0] });

  } catch (err) {
    console.error('[Classes] POST error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── PUT /api/classes/:id ────────────────────

router.put('/:id', async (req, res) => {
  const { id } = req.params;
  const { name, period, room, color } = req.body;

  try {
    const result = await pool.query(
      `UPDATE classes SET name   = COALESCE($1, name),
                          period = COALESCE($2, period),
                          room   = COALESCE($3, room),
                          color  = COALESCE($4, color)
       WHERE id = $5 AND teacher_id = $6
       RETURNING *`,
      [name, period, room, color, id, req.teacher.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Class not found.' });
    }

    return res.json({ class: result.rows[0] });

  } catch (err) {
    console.error('[Classes] PUT error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── DELETE /api/classes/:id ─────────────────

router.delete('/:id', async (req, res) => {
  const { id } = req.params;
  try {
    await pool.query(
      'DELETE FROM classes WHERE id = $1 AND teacher_id = $2',
      [id, req.teacher.id]
    );
    return res.json({ message: 'Class deleted.' });
  } catch (err) {
    console.error('[Classes] DELETE error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export default router;