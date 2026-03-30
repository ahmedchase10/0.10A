// =============================================
// DIGI-SCHOOL AI — Express Server
// =============================================

import express    from 'express';
import cors       from 'cors';
import dotenv     from 'dotenv';

import authRouter    from './routes/auth.js';
import studentsRouter from './routes/students.js';
import classesRouter  from './routes/classes.js';
import attendanceRouter from './routes/attendance.js';
import gradesRouter   from './routes/grades.js';
import aiRouter       from './routes/ai.js';
import {
  flaggedRouter,
  notifRouter,
  voiceRouter,
  lessonsRouter,
  homeworkRouter,
} from './routes/other.js';

dotenv.config();

const app  = express();
const PORT = process.env.PORT || 3001;

// ─── Middleware ──────────────────────────────

app.use(cors({
  origin: 'http://localhost:5173', // Vite dev server
  credentials: true,
}));

app.use(express.json());

// ─── Routes ─────────────────────────────────

app.use('/api/auth',          authRouter);
app.use('/api/students',      studentsRouter);
app.use('/api/classes',       classesRouter);
app.use('/api/attendance',    attendanceRouter);
app.use('/api/grades',        gradesRouter);
app.use('/api/ai',            aiRouter);
app.use('/api/flagged',       flaggedRouter);
app.use('/api/notifications', notifRouter);
app.use('/api/voice',         voiceRouter);
app.use('/api/lessons',       lessonsRouter);
app.use('/api/homework',      homeworkRouter);

// ─── Health check ────────────────────────────

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// ─── 404 handler ─────────────────────────────

app.use((req, res) => {
  res.status(404).json({ message: `Route ${req.method} ${req.path} not found.` });
});

// ─── Global error handler ────────────────────

app.use((err, req, res, next) => {
  console.error('[Server] Unhandled error:', err.message);
  res.status(500).json({ message: 'Internal server error.' });
});

// ─── Start ───────────────────────────────────

app.listen(PORT, () => {
  console.log(`[Server] Digi-School API running at http://localhost:${PORT}`);
});