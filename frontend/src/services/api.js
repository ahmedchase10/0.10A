const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  constructor() {
    this.token = null;
  }

  setToken(token) {
    this.token = token;
  }

  getHeaders(includeAuth = false) {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (includeAuth && this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  async handleResponse(response) {
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.error?.message || 'Request failed');
    }
    
    return data;
  }

  // ─── Authentication ──────────────────────────
  
  async register(name, email, password, initials = null) {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        name,
        email,
        password,
        initials: initials || name.substring(0, 2).toUpperCase()
      })
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
  
  // ─── Classes ─────────────────────────────────
  
  async getClasses() {
    const response = await fetch(`${API_BASE_URL}/classes`, {
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
  
  // ─── Students ────────────────────────────────
  
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
  
  async updateStudent(classId, studentId, studentData) {
    const response = await fetch(`${API_BASE_URL}/classes/${classId}/students/${studentId}`, {
      method: 'PUT',
      headers: this.getHeaders(true),
      body: JSON.stringify(studentData)
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

  // ─── Notifications ───────────────────────────
  
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
  
  // ─── Attendance ──────────────────────────────
  
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
  
  // ─── Teacher Profile ─────────────────────────
  
  async updateTeacherProfile(profileData) {
    const response = await fetch(`${API_BASE_URL}/teachers/profile`, {
      method: 'PUT',
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
  
  // ─── Attendance ──────────────────────────────
  
  async markAttendance(studentId, classId, date, status) {
    const response = await fetch(`${API_BASE_URL}/attendance`, {
      method: 'POST',
      headers: this.getHeaders(true),
      body: JSON.stringify({
        studentId,
        classId,
        date,
        status
      })
    });
    
    return this.handleResponse(response);
  }
  
  async getAttendance(classId, date = null) {
    const url = date
      ? `${API_BASE_URL}/attendance?classId=${classId}&date=${date}`
      : `${API_BASE_URL}/attendance?classId=${classId}`;
      
    const response = await fetch(url, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    
    return this.handleResponse(response);
  }
  
  // ─── Lessons ─────────────────────────────────
  
  async uploadLesson(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/lessons/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
    
    return this.handleResponse(response);
  }
  
  // ─── Lessons ─────────────────────────────────
  
  async uploadLesson(formData) {
    const response = await fetch(`${API_BASE_URL}/lessons/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
    
    return this.handleResponse(response);
  }
  
  async getLessons(classId, options = {}) {
    const { limit = 20, offset = 0, sort = 'created_at_desc', refresh = true } = options;
    const params = new URLSearchParams({
      class_id: classId,
      limit: limit.toString(),
      offset: offset.toString(),
      sort,
      refresh: refresh.toString()
    });
      
    const response = await fetch(`${API_BASE_URL}/lessons?${params}`, {
      method: 'GET',
      headers: this.getHeaders(true)
    });
    
    return this.handleResponse(response);
  }
  
  // Note: Backend doesn't have delete endpoint yet
  async deleteLesson(lessonId) {
    throw new Error('Delete lesson endpoint not implemented in backend yet');
  }
  
  // ─── Voice Processing ────────────────────────
  
  async processVoiceNote(audioBlob, classId) {
    const formData = new FormData();
    formData.append('audio', audioBlob);
    formData.append('classId', classId);
    
    const response = await fetch(`${API_BASE_URL}/voice/process`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`
      },
      body: formData
    });
    
    return this.handleResponse(response);
  }
}

export default new ApiService();