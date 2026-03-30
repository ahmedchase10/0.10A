// =============================================
// DIGI-SCHOOL AI — AI Routes
// GET  /api/ai/me/classes
// GET  /api/ai/me/students
// GET  /api/ai/me/summary
// POST /api/ai/agent   ← main bridge to Python agent
// =============================================

import express from 'express';
import pool    from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();
const AGENT_URL = process.env.AGENT_URL || 'http://localhost:8000';

router.use(requireAuth);

// ─── GET /api/ai/me/classes ──────────────────

router.get('/me/classes', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT id, name, period, room, color
       FROM classes
       WHERE teacher_id = $1
       ORDER BY created_at DESC`,
      [req.teacher.id]
    );
    return res.json({ classes: result.rows });
  } catch (err) {
    console.error('[AI] classes error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── GET /api/ai/me/students ─────────────────

router.get('/me/students', async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT s.id, s.name, s.behavior, s.notes, s.parent_email,
              s.class_id, c.name AS class_name, c.period, c.room
       FROM students s
       JOIN classes c ON c.id = s.class_id
       WHERE c.teacher_id = $1
       ORDER BY s.name ASC`,
      [req.teacher.id]
    );
    return res.json({ students: result.rows });
  } catch (err) {
    console.error('[AI] students error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── GET /api/ai/me/summary ──────────────────

router.get('/me/summary', async (req, res) => {
  try {
    // Single query — much faster than 4 separate calls
    const result = await pool.query(
      `SELECT
        (SELECT COUNT(*) FROM classes         WHERE teacher_id = $1)                                                   AS classes_count,
        (SELECT COUNT(*) FROM students s JOIN classes c ON c.id = s.class_id WHERE c.teacher_id = $1)                 AS students_count,
        (SELECT COUNT(*) FROM attendance a JOIN classes c ON c.id = a.class_id WHERE c.teacher_id = $1 AND a.date = CURRENT_DATE) AS today_attendance,
        (SELECT COUNT(*) FROM flagged_students f JOIN classes c ON c.id = f.class_id WHERE c.teacher_id = $1 AND f.resolved = FALSE) AS unresolved_flags`,
      [req.teacher.id]
    );

    const row = result.rows[0];
    return res.json({
      teacherId:            req.teacher.id,
      classesCount:         parseInt(row.classes_count),
      studentsCount:        parseInt(row.students_count),
      todayAttendanceRecords: parseInt(row.today_attendance),
      unresolvedFlags:      parseInt(row.unresolved_flags),
    });
  } catch (err) {
    console.error('[AI] summary error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

// ─── POST /api/ai/agent ──────────────────────
// Main bridge: receives teacher input from frontend,
// forwards to Python agent with teacher context,
// returns agent actions + response.
//
// Body: { input: "Ahmed and Sarra were absent today in 3G" }

router.post('/agent', async (req, res) => {
  const { input } = req.body;

  if (!input || !input.trim()) {
    return res.status(400).json({ message: 'Input text is required.' });
  }

  try {
    // Fetch teacher context to send along with the input
    const [classesRes, studentsRes] = await Promise.all([
      pool.query(
        `SELECT id, name, period, room FROM classes WHERE teacher_id = $1 ORDER BY name`,
        [req.teacher.id]
      ),
      pool.query(
        `SELECT s.id, s.name, s.class_id, c.name AS class_name
         FROM students s
         JOIN classes c ON c.id = s.class_id
         WHERE c.teacher_id = $1
         ORDER BY s.name`,
        [req.teacher.id]
      ),
    ]);

    // Forward to Python agent server
    const agentResponse = await fetch(`${AGENT_URL}/agent/run`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input,
        teacher: {
          id:    req.teacher.id,
          name:  req.teacher.name,
          email: req.teacher.email,
        },
        context: {
          classes:  classesRes.rows,
          students: studentsRes.rows,
          date:     new Date().toISOString().split('T')[0],
        },
      }),
    });

    if (!agentResponse.ok) {
      const errData = await agentResponse.json().catch(() => ({}));
      throw new Error(errData.detail || `Agent server returned ${agentResponse.status}`);
    }

    const agentData = await agentResponse.json();

    // agentData shape (returned by Python):
    // {
    //   actions:  [{ type, description, data }],
    //   summary:  "Agent marked Ahmed and Sarra as absent in 3G",
    //   raw:      { ... full agent output ... }
    // }

    return res.json(agentData);

  } catch (err) {
    // If Python server is not running yet, return a clear message
    if (err.cause?.code === 'ECONNREFUSED') {
      return res.status(503).json({
        message: 'Agent server is not running. Start it with: uvicorn main:app --reload',
      });
    }
    console.error('[AI] agent error:', err.message);
    return res.status(500).json({ message: err.message });
  }
});

export default router;