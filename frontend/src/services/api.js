/**
 * api.js — Singleton HTTP client for the Digi-School FastAPI backend.
 *
 * 401 INTERCEPTOR
 * ───────────────
 * handleResponse() detects HTTP 401 responses. When one arrives it:
 *   1. Calls authStore.logout()     — clears token + localStorage
 *   2. Calls classesStore.reset()   — clears cached class list
 *   3. Calls router.push('/auth')   — sends user to login page
 *   4. Throws AuthError so the calling component doesn't try to process data.
 *
 * Stores and router are imported lazily to avoid circular-dependency issues
 * at module initialisation time.
 */

const API_BASE_URL = 'http://localhost:8000';

export class AuthError extends Error {
  constructor(message = 'Session expired. Please log in again.') {
    super(message);
    this.name = 'AuthError';
  }
}

class ApiService {
  constructor() {
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  getHeaders(includeAuth = false) {
    const headers = { 'Content-Type': 'application/json' };
    if (includeAuth && this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  // ── 401 handler — lazy imports avoid circular deps ─────────────────────────

  async _handle401() {
    const { useAuthStore } = await import('@/stores/auth');
    const { useClassesStore } = await import('@/stores/classesStore');
    const { default: router } = await import('@/router');

    useAuthStore().logout();
    useClassesStore().reset();
    await router.push('/auth');
  }

  // ── Core response handler ──────────────────────────────────────────────────

  async handleResponse(response) {
    if (response.status === 401) {
      await this._handle401();
      throw new AuthError();
    }

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error?.message || 'Request failed');
    }

    return data;
  }

  // ─── Authentication ────────────────────────────────────────────────────────

  async register(name, email, password, initials = null) {
    const payload = {
      name,
      email,
      password
    };
    if (initials !== null && initials !== undefined && String(initials).trim() !== '') {
      payload.initials = initials;
    }
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(payload)
    });
    return this.handleResponse(response);
  }

  async login(email, password) {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ email, password })
    });
    return this.handleResponse(response);
  }

  async getMe() {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Classes ──────────────────────────────────────────────────────────────

  async getClasses() {
    const response = await fetch(`${API_BASE_URL}/classes`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async getTimetable() {
    const response = await fetch(`${API_BASE_URL}/timetable`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async createClass(classData) {
    const response = await fetch(`${API_BASE_URL}/classes`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(classData)
    });
    return this.handleResponse(response);
  }

  async createTimetable(entries) {
    const normalizedEntries = Array.isArray(entries)
      ? entries
      : entries
        ? [entries]
        : [];
    const response = await fetch(`${API_BASE_URL}/timetable`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ entries: normalizedEntries })
    });
    return this.handleResponse(response);
  }

  async deleteTimetable(timetableId) {
    const response = await fetch(`${API_BASE_URL}/timetable/${timetableId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async updateClass(classId, classData) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}`, {
      method: 'PUT',
      headers: this.getHeaders(true),
      body: JSON.stringify(classData)
    });
    return this.handleResponse(response);
  }

  async deleteClass(classId) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Students ─────────────────────────────────────────────────────────────

  async getStudents(classId) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/students`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async createStudent(data) {
    const { class_id, ...studentData } = data;
    const response = await fetch(`${API_BASE_URL}/classes/${class_id}/students`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(studentData)
    });
    return this.handleResponse(response);
  }

  async updateStudent(classId, studentId, data) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/students/${studentId}`, {
      method: 'PUT',
      headers: this.getHeaders(true),
      body: JSON.stringify(data)
    });
    return this.handleResponse(response);
  }

  async deleteStudent(classId, studentId) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/students/${studentId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Flags ────────────────────────────────────────────────────────────────

  async getFlags(classId, studentId) {
    const params = new URLSearchParams({ class_id: classId.toString(), student_id: studentId.toString() });
    const response = await fetch(`${API_BASE_URL}/flags?${params}`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async createFlag(classId, studentId, reason) {
    const response = await fetch(`${API_BASE_URL}/flags`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ class_id: classId, student_id: studentId, reason })
    });
    return this.handleResponse(response);
  }

  async deleteFlag(flagId) {
    const response = await fetch(`${API_BASE_URL}/flags/${flagId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Exam Types ───────────────────────────────────────────────────────────

  async getExamTypes(classId) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/exam-types`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async createExamType(classId, name) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/exam-types`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ name })
    });
    return this.handleResponse(response);
  }

  async deleteExamType(classId, examTypeId) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/exam-types/${examTypeId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Grades ───────────────────────────────────────────────────────────────

  async getGrades(classId, examTypeId = null) {
    const params = new URLSearchParams();
    if (examTypeId !== null) params.set('exam_type_id', examTypeId.toString());
    const url = `${API_BASE_URL}/classes/${classId}/grades${params.toString() ? '?' + params.toString() : ''}`;
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async saveGrade(classId, studentId, examTypeId, value) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/grades`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ student_id: studentId, exam_type_id: examTypeId, value })
    });
    return this.handleResponse(response);
  }

  async deleteGrade(classId, gradeId) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/grades/${gradeId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Notifications ────────────────────────────────────────────────────────

  async getNotifications() {
    const response = await fetch(`${API_BASE_URL}/notifications`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async markNotificationRead(notificationId) {
    const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}/read`, {
      method: 'PUT',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async deleteNotification(notificationId) {
    const response = await fetch(`${API_BASE_URL}/notifications/${notificationId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Attendance ───────────────────────────────────────────────────────────

  async createAttendance(data) {
    const response = await fetch(`${API_BASE_URL}/attendance`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(data)
    });
    return this.handleResponse(response);
  }

  async getAttendance(classId, sessionDate) {
    const params = new URLSearchParams({
      class_id: classId.toString(),
      session_date: sessionDate
    });
    const response = await fetch(`${API_BASE_URL}/attendance?${params}`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async updateAttendance(data) {
    const response = await fetch(`${API_BASE_URL}/attendance`, {
      method: 'PUT',
      headers: this.getHeaders(true),
      body: JSON.stringify(data)
    });
    return this.handleResponse(response);
  }

  // ─── Teacher Profile ──────────────────────────────────────────────────────

  async updateTeacherProfile(profileData) {
    const response = await fetch(`${API_BASE_URL}/teachers/profile`, {
      method: 'PATCH',
      headers: this.getHeaders(true),
      body: JSON.stringify(profileData)
    });
    return this.handleResponse(response);
  }

  async changePassword(currentPassword, newPassword) {
    const response = await fetch(`${API_BASE_URL}/teachers/password`, {
      method: 'PUT',
      headers: this.getHeaders(true),
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword
      })
    });
    return this.handleResponse(response);
  }

  // ─── Lessons ──────────────────────────────────────────────────────────────

  async uploadLesson(formData) {
    // FormData — do NOT set Content-Type; browser sets it with the correct boundary
    const response = await fetch(`${API_BASE_URL}/lessons/upload`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` },
      body: formData
    });
    return this.handleResponse(response);
  }

  async getLessons(classId, options = {}) {
    const { limit = 20, offset = 0, sort = 'created_at_desc', refresh = true } = options;
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
      sort,
      refresh: refresh.toString()
    });
    if (classId) {
      params.append('class_id', classId);
    }
    const response = await fetch(`${API_BASE_URL}/lessons?${params}`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async assignGlobalUpload(globalUploadId, classId) {
    const params = new URLSearchParams({
      global_upload_id: globalUploadId,
      class_id: classId.toString()
    });
    const response = await fetch(`${API_BASE_URL}/lessons/assign?${params}`, {
      method: 'POST',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  async deleteLesson(lessonId) {
    const encodedLessonId = encodeURIComponent(String(lessonId));
    const response = await fetch(`${API_BASE_URL}/lessons/${encodedLessonId}`, {
      method: 'DELETE',
      headers: this.getHeaders(true)
    });
    return this.handleResponse(response);
  }

  // ─── Pedagogical Agent ────────────────────────────────────────────────────

  async createAgentSession(classId, title) {
    const response = await fetch(`${API_BASE_URL}/agents/pedagogical/sessions`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ class_id: classId, title }),
    });
    return this.handleResponse(response);
  }

  async listAgentSessions(classId) {
    const params = new URLSearchParams({ class_id: classId.toString() });
    const response = await fetch(`${API_BASE_URL}/agents/pedagogical/sessions?${params}`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(response);
  }

  async getAgentSessionHistory(threadId) {
    const response = await fetch(
      `${API_BASE_URL}/agents/pedagogical/sessions/${encodeURIComponent(threadId)}/history`,
      { method: 'GET', headers: this.getHeaders(true) }
    );
    return this.handleResponse(response);
  }

  async renameAgentSession(threadId, newTitle) {
    const response = await fetch(
      `${API_BASE_URL}/agents/pedagogical/sessions/${encodeURIComponent(threadId)}`,
      {
        method: 'PATCH',
        headers: this.getHeaders(true),
        body: JSON.stringify({ title: newTitle }),
      }
    );
    return this.handleResponse(response);
  }

  async deleteAgentSession(threadId) {
    const response = await fetch(
      `${API_BASE_URL}/agents/pedagogical/sessions/${encodeURIComponent(threadId)}`,
      { method: 'DELETE', headers: this.getHeaders(true) }
    );
    return this.handleResponse(response);
  }

  /**
   * streamPedagogical — POST SSE for the pedagogical agent.
   * Uses fetch + ReadableStream because EventSource doesn't support POST.
   *
   * @param {{ thread_id: string, file_ids: string[], prompt: string, reasoning: boolean }} body
   * @param {function({ event: string, data: string }): void} onEvent
   * @returns {Promise<void>} resolves when the stream ends (done event)
   */
  async streamPedagogical(body, onEvent) {
    const res = await fetch(`${API_BASE_URL}/agents/pedagogical/ask`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok || !res.body) {
      let msg = `HTTP ${res.status}`;
      try { const j = await res.json(); msg = j?.error?.message || msg; } catch { /* noop */ }
      throw new Error(msg);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';

      for (const frame of frames) {
        if (!frame.trim()) continue;
        let event = 'message';
        let data = '';

        for (const line of frame.split('\n')) {
          if (line.startsWith('event:')) event = line.slice(6).trim();
          else if (line.startsWith('data:')) data += line.slice(5).trimStart();
        }

        onEvent({ event, data });

        if (event === 'done') return;
        if (event === 'error') throw new Error(data || 'Stream error');
      }
    }
  }

  // Creator Agent

  async listCreatorSessions(options = {}) {
    const { limit = 50, offset = 0 } = options;
    const params = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    });
    const response = await fetch(`${API_BASE_URL}/agents/creator/sessions?${params}`, {
      method: 'GET',
      headers: this.getHeaders(true),
    });
    return this.handleResponse(response);
  }

  async getCreatorSession(sessionId) {
    const response = await fetch(
      `${API_BASE_URL}/agents/creator/sessions/${encodeURIComponent(String(sessionId))}`,
      {
        method: 'GET',
        headers: this.getHeaders(true),
      }
    );
    return this.handleResponse(response);
  }

  async deleteCreatorSession(sessionId) {
    const response = await fetch(
      `${API_BASE_URL}/agents/creator/sessions/${encodeURIComponent(String(sessionId))}`,
      {
        method: 'DELETE',
        headers: this.getHeaders(true),
      }
    );
    return this.handleResponse(response);
  }

  async retryCreatorOverview(classId) {
    const response = await fetch(`${API_BASE_URL}/agents/creator/retry-overview`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({ class_id: classId }),
    });
    return this.handleResponse(response);
  }

  async streamCreatorGenerate(body, onEvent) {
    const res = await fetch(`${API_BASE_URL}/agents/creator/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.token}`,
      },
      body: JSON.stringify(body),
    });

    if (!res.ok || !res.body) {
      let msg = `HTTP ${res.status}`;
      try { const j = await res.json(); msg = j?.error?.message || msg; } catch { /* noop */ }
      throw new Error(msg);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split('\n\n');
      buffer = frames.pop() || '';

      for (const frame of frames) {
        if (!frame.trim()) continue;
        let event = 'message';
        let data = '';

        for (const line of frame.split('\n')) {
          if (line.startsWith('event:')) event = line.slice(6).trim();
          else if (line.startsWith('data:')) data += line.slice(5).trimStart();
        }

        onEvent({ event, data });

        if (event === 'done') return;
        if (event === 'error') throw new Error(data || 'Stream error');
      }
    }
  }

  // ─── Voice Processing ─────────────────────────────────────────────────────

  async processVoiceNote(audioBlob, classId) {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('classId', classId);
    const response = await fetch(`${API_BASE_URL}/voice/process`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${this.token}` },
      body: formData
    });
    return this.handleResponse(response);
  }

  // ─── Email Agent ──────────────────────────────────────────────────────────

  async generateEmail(payload) {
    const response = await fetch(`${API_BASE_URL}/emailagent/generate-email`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(payload)
    });
    return this.handleResponse(response);
  }

  async sendEmail(payload) {
    const response = await fetch(`${API_BASE_URL}/gmail/send-email`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify(payload)
    });
    return this.handleResponse(response);
  }
}

export default new ApiService();
