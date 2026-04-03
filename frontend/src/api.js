// =============================================
// DIGI-SCHOOL AI — API Client
// All backend calls go through this module.
// =============================================

const BASE_URL = 'http://localhost:3001/api';

// ─── Core fetch wrapper ──────────────────────

async function request(method, path, body = null) {
  const token = sessionStorage.getItem('digischool_token');

  const headers = { 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const config = { method, headers };
  if (body) config.body = JSON.stringify(body);

  const res  = await fetch(`${BASE_URL}${path}`, config);
  const data = await res.json();

  if (!res.ok) {
    throw new Error(data.message || `Request failed with status ${res.status}`);
  }

  return data;
}

const get    = (path)        => request('GET',    path);
const post   = (path, body)  => request('POST',   path, body);
const put    = (path, body)  => request('PUT',    path, body);
const del    = (path)        => request('DELETE', path);

// ─── Auth ────────────────────────────────────

export const api = {

  auth: {
    login:    (email, password)                   => post('/auth/login',    { email, password }),
    register: (name, email, password, subject)    => post('/auth/register', { name, email, password, subject }),
    me:       ()                                  => get('/auth/me'),
  },

  // ─── Classes ──────────────────────────────

  classes: {
    getAll:   ()              => get('/classes'),
    create:   (data)          => post('/classes', data),
    update:   (id, data)      => put(`/classes/${id}`, data),
    delete:   (id)            => del(`/classes/${id}`),
  },

  // ─── Students ─────────────────────────────

  students: {
    getAll:       (classId)   => get(`/students${classId ? `?classId=${classId}` : ''}`),
    create:       (data)      => post('/students', data),
    update:       (id, data)  => put(`/students/${id}`, data),
    delete:       (id)        => del(`/students/${id}`),
  },

  // ─── Attendance ───────────────────────────

  attendance: {
    get:    (classId, date)   => get(`/attendance?classId=${classId}${date ? `&date=${date}` : ''}`),
    today:  ()                => get('/attendance/today'),
    mark:   (data)            => post('/attendance', data),
    bulk:   (records)         => post('/attendance/bulk', { records }),
  },

  // ─── Grades ───────────────────────────────

  grades: {
    get:    (classId)         => get(`/grades${classId ? `?classId=${classId}` : ''}`),
    save:   (data)            => post('/grades', data),
    bulk:   (records)         => post('/grades/bulk', { records }),
    update: (id, score)       => put(`/grades/${id}`, { score }),
  },

  // ─── Flagged ──────────────────────────────

  flagged: {
    getAll:   ()              => get('/flagged'),
    create:   (data)          => post('/flagged', data),
    resolve:  (id)            => put(`/flagged/${id}/resolve`),
  },

  // ─── Notifications ────────────────────────

  notifications: {
    getAll:   ()              => get('/notifications'),
    send:     (data)          => post('/notifications', data),
  },

  // ─── Voice History ────────────────────────

  voice: {
    getAll:   ()              => get('/voice'),
    save:     (data)          => post('/voice', data),
  },

  // ─── Lesson Log ───────────────────────────

  lessons: {
    get:    (classId)         => get(`/lessons${classId ? `?classId=${classId}` : ''}`),
    create: (data)            => post('/lessons', data),
  },

  // ─── Homework ─────────────────────────────

  homework: {
    get:      (classId)       => get(`/homework${classId ? `?classId=${classId}` : ''}`),
    create:   (data)          => post('/homework', data),
    complete: (id)            => put(`/homework/${id}/complete`),
  },
  // ─── Agent ───────────────────────────
  agent: {
    run: (message) => post('/agent/run', { message }),
  },
};