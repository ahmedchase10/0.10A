// =============================================
// DIGI-SCHOOL AI — AI Routes
// GET /api/ai/me/classes
// GET /api/ai/me/students
// GET /api/ai/me/summary
// =============================================

import express from 'express';
import pool from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

// All AI routes require auth (same as students route)
router.use(requireAuth);

// ─── GET /api/ai/me/classes ───────────────────────

router.get('/me/classes', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT id, name, period, room, color
      FROM classes
      WHERE teacher_id = $1
      ORDER BY created_at DESC
    `, [req.teacher.id]);

    return res.json({ classes: result.rows });

  } catch (err) {
    console.error('[AI] classes error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── GET /api/ai/me/students ───────────────────────

router.get('/me/students', async (req, res) => {
  try {
    const result = await pool.query(`
      SELECT 
        s.id,
        s.name,
        s.behavior,
        s.notes,
        s.parent_email,
        s.class_id,
        c.name AS class_name,
        c.period,
        c.room
      FROM students s
      JOIN classes c ON c.id = s.class_id
      WHERE c.teacher_id = $1
      ORDER BY s.name ASC
    `, [req.teacher.id]);

    return res.json({ students: result.rows });

  } catch (err) {
    console.error('[AI] students error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── GET /api/ai/me/summary ───────────────────────

router.get('/me/summary', async (req, res) => {
  try {
    const classes = await pool.query(`
      SELECT COUNT(*) 
      FROM classes 
      WHERE teacher_id = $1
    `, [req.teacher.id]);

    const students = await pool.query(`
      SELECT COUNT(*)
      FROM students s
      JOIN classes c ON c.id = s.class_id
      WHERE c.teacher_id = $1
    `, [req.teacher.id]);

    const attendance = await pool.query(`
      SELECT COUNT(*)
      FROM attendance a
      JOIN classes c ON c.id = a.class_id
      WHERE c.teacher_id = $1
      AND a.date = CURRENT_DATE
    `, [req.teacher.id]);

    const flagged = await pool.query(`
      SELECT COUNT(*)
      FROM flagged_students f
      JOIN classes c ON c.id = f.class_id
      WHERE c.teacher_id = $1
      AND f.resolved = FALSE
    `, [req.teacher.id]);

    return res.json({
      teacherId: req.teacher.id,
      classesCount: parseInt(classes.rows[0].count),
      studentsCount: parseInt(students.rows[0].count),
      todayAttendanceRecords: parseInt(attendance.rows[0].count),
      unresolvedFlags: parseInt(flagged.rows[0].count)
    });

  } catch (err) {
    console.error('[AI] summary error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export default router;