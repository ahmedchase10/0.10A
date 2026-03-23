// =============================================
// DIGI-SCHOOL AI — Auth Routes
// POST /api/auth/register
// POST /api/auth/login
// GET  /api/auth/me
// =============================================

import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import pool from '../db.js';
import { requireAuth } from '../middleware/auth.js';

const router = express.Router();

// ─── Helper: generate JWT ────────────────────

function generateToken(teacher) {
  return jwt.sign(
    { id: teacher.id, name: teacher.name, email: teacher.email },
    process.env.JWT_SECRET,
    { expiresIn: '7d' }
  );
}

// ─── POST /api/auth/register ─────────────────

router.post('/register', async (req, res) => {
  const { name, email, password, subject, school, grades } = req.body;

  // Basic validation
  if (!name || !email || !password) {
    return res.status(400).json({ message: 'Name, email and password are required.' });
  }

  if (password.length < 8) {
    return res.status(400).json({ message: 'Password must be at least 8 characters.' });
  }

  try {
    // Check if email already exists
    const existing = await pool.query(
      'SELECT id FROM teachers WHERE email = $1',
      [email.toLowerCase()]
    );

    if (existing.rows.length > 0) {
      return res.status(409).json({ message: 'An account with this email already exists.' });
    }

    // Hash password
    const hashed = await bcrypt.hash(password, 12);

    // Generate initials
    const initials = name
      .split(' ')
      .map(w => w[0])
      .join('')
      .slice(0, 2)
      .toUpperCase();

    // Insert teacher
    const result = await pool.query(
      `INSERT INTO teachers (name, initials, email, password, subject, school, grades)
       VALUES ($1, $2, $3, $4, $5, $6, $7)
       RETURNING id, name, initials, email, subject, school, grades`,
      [name, initials, email.toLowerCase(), hashed, subject || '', school || '', grades || '']
    );

    const teacher = result.rows[0];
    const token   = generateToken(teacher);

    return res.status(201).json({
      message: 'Account created successfully.',
      token,
      teacher,
    });

  } catch (err) {
    console.error('[Auth] Register error:', err.message);
    return res.status(500).json({ message: 'Server error. Please try again.' });
  }
});

// ─── POST /api/auth/login ────────────────────

router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.status(400).json({ message: 'Email and password are required.' });
  }

  try {
    // Find teacher by email
    const result = await pool.query(
      `SELECT id, name, initials, email, password, subject, school, grades
       FROM teachers WHERE email = $1`,
      [email.toLowerCase()]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ message: 'Invalid email or password.' });
    }

    const teacher = result.rows[0];

    // Compare password
    const valid = await bcrypt.compare(password, teacher.password);
    if (!valid) {
      return res.status(401).json({ message: 'Invalid email or password.' });
    }

    // Generate token — exclude password from response
    const { password: _, ...teacherData } = teacher;
    const token = generateToken(teacherData);

    return res.status(200).json({
      message: 'Login successful.',
      token,
      teacher: teacherData,
    });

  } catch (err) {
    console.error('[Auth] Login error:', err.message);
    return res.status(500).json({ message: 'Server error. Please try again.' });
  }
});

// ─── GET /api/auth/me ────────────────────────

router.get('/me', requireAuth, async (req, res) => {
  try {
    const result = await pool.query(
      `SELECT id, name, initials, email, subject, school, grades
       FROM teachers WHERE id = $1`,
      [req.teacher.id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Teacher not found.' });
    }

    return res.status(200).json({ teacher: result.rows[0] });

  } catch (err) {
    console.error('[Auth] Me error:', err.message);
    return res.status(500).json({ message: 'Server error.' });
  }
});

export default router;