// =============================================
// DIGI-SCHOOL AI — Class Page Component
// Individual class dashboard with students & AI command zone
// =============================================

import { State } from '../main.js';
import { API } from '../api.js';

export class ClassPage {
    constructor() {
        this.students = [];
        this.showAddStudentModal = false;
    }
    
    render() {
        const main = document.createElement('main');
        main.className = 'class-page-main';
        
        const classData = State.selectedClass;
        
        if (!classData) {
            main.innerHTML = '<div class="error-state"><p>No class selected</p></div>';
            return main;
        }
        
        main.innerHTML = `
            <!-- Class Header -->
            <div class="class-page-header">
                <div class="class-page-breadcrumb">
                    <button class="breadcrumb-link" id="back-to-dashboard">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M10 12L6 8L10 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                        Dashboard
                    </button>
                    <span class="breadcrumb-separator">/</span>
                    <span class="breadcrumb-current">${classData.name}</span>
                </div>
                
                <div class="class-page-title">
                    <div class="class-color-indicator" style="background-color: ${classData.color || '#667eea'}"></div>
                    <div class="class-info-header">
                        <h1 class="class-page-name">${classData.name}</h1>
                        <div class="class-meta-pills">
                            ${classData.subject ? `<span class="meta-pill">${classData.subject}</span>` : ''}
                            ${classData.period ? `<span class="meta-pill">${classData.period}</span>` : ''}
                            ${classData.room ? `<span class="meta-pill">${classData.room}</span>` : ''}
                            ${classData.school ? `<span class="meta-pill">${classData.school}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- AI Command Zone -->
            <div class="ai-command-zone">
                <div class="ai-zone-header">
                    <div class="ai-zone-title">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <div>
                            <h2>AI Command Console</h2>
                            <p>Speak or type naturally to execute commands</p>
                        </div>
                    </div>
                    <div class="ai-status">
                        <span class="status-dot active"></span>
                        <span class="status-text">Ready</span>
                    </div>
                </div>
                
                <div class="ai-interaction-area">
                    <div class="ai-input-group">
                        <textarea 
                            id="ai-command-input" 
                            class="ai-command-input" 
                            placeholder="Try: 'Ahmed and Sara were absent today' or 'Homework is exercises 10-15'"
                            rows="2"
                        ></textarea>
                        <div class="ai-input-actions">
                            <button class="ai-voice-btn" id="ai-voice-btn" title="Voice input">
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                    <path d="M10 13C11.6569 13 13 11.6569 13 10V4C13 2.34315 11.6569 1 10 1C8.34315 1 7 2.34315 7 4V10C7 11.6569 8.34315 13 10 13Z" stroke="currentColor" stroke-width="2"/>
                                    <path d="M5 9V10C5 12.7614 7.23858 15 10 15C12.7614 15 15 12.7614 15 10V9" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                                </svg>
                            </button>
                            <button class="ai-send-btn" id="ai-send-btn">
                                <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                                    <path d="M18 2L9 11M18 2L12 18L9 11M18 2L2 8L9 11" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                                Execute
                            </button>
                        </div>
                    </div>
                    
                    <div class="ai-quick-actions">
                        <span class="quick-action-label">Quick Actions:</span>
                        <button class="quick-action-chip" data-action="Mark attendance for today">Mark Attendance</button>
                        <button class="quick-action-chip" data-action="Show class statistics">Class Stats</button>
                        <button class="quick-action-chip" data-action="Generate report cards">Generate Reports</button>
                    </div>
                </div>
            </div>
            
            <!-- Students Section -->
            <div class="students-section">
                <div class="section-header">
                    <div>
                        <h2>Students</h2>
                        <p class="section-subtitle">Manage students in this class</p>
                    </div>
                    <button class="btn-primary" id="add-student-btn">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 4V16M4 10H16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                        Add Student
                    </button>
                </div>
                
                <div class="students-table-container" id="students-table-container">
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <p>Loading students...</p>
                    </div>
                </div>
            </div>
            
            ${this.renderAddStudentModal()}
        `;
        
        this.attachListeners(main);
        
        return main;
    }
    
    renderAddStudentModal() {
        return `
            <div class="modal" id="add-student-modal" style="display: none;">
                <div class="modal-overlay" id="student-modal-overlay"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Add Student</h2>
                        <button class="modal-close" id="student-modal-close">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </button>
                    </div>
                    
                    <form class="modal-form" id="add-student-form">
                        <div class="form-group">
                            <label for="student-name">Student Name *</label>
                            <input 
                                type="text" 
                                id="student-name" 
                                name="name" 
                                required 
                                placeholder="e.g., Ahmed Ben Ali"
                            />
                        </div>
                        
                        <div class="form-group">
                            <label for="parent-email">Parent Email</label>
                            <input 
                                type="email" 
                                id="parent-email" 
                                name="parent_email" 
                                placeholder="parent@email.com"
                            />
                        </div>
                        
                        <div class="form-group">
                            <label for="student-behavior">Behavior</label>
                            <select id="student-behavior" name="behavior">
                                <option value="Excellent">Excellent</option>
                                <option value="Good" selected>Good</option>
                                <option value="Fair">Fair</option>
                                <option value="Needs Improvement">Needs Improvement</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="student-notes">Notes</label>
                            <textarea 
                                id="student-notes" 
                                name="notes" 
                                rows="3"
                                placeholder="Additional notes about the student..."
                            ></textarea>
                        </div>
                        
                        <div class="modal-error" id="student-modal-error" style="display: none;"></div>
                        
                        <div class="modal-footer">
                            <button type="button" class="btn-secondary" id="cancel-student">
                                Cancel
                            </button>
                            <button type="submit" class="btn-primary" id="submit-student">
                                Add Student
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
    }
    
    renderStudentsTable(students) {
        if (students.length === 0) {
            return `
                <div class="empty-state">
                    <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                        <circle cx="60" cy="45" r="15" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                        <path d="M40 85C40 76.7157 46.7157 70 55 70H65C73.2843 70 80 76.7157 80 85V90H40V85Z" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                    </svg>
                    <h3>No students yet</h3>
                    <p>Add students to this class to get started</p>
                </div>
            `;
        }
        
        return `
            <table class="students-table">
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Behavior</th>
                        <th>Parent Email</th>
                        <th>Notes</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${students.map(student => `
                        <tr>
                            <td class="student-name-cell">
                                <div class="student-avatar">${student.name.charAt(0).toUpperCase()}</div>
                                <span>${student.name}</span>
                            </td>
                            <td>
                                <span class="behavior-badge behavior-${student.behavior?.toLowerCase().replace(/\s+/g, '-') || 'good'}">
                                    ${student.behavior || 'Good'}
                                </span>
                            </td>
                            <td>${student.parent_email || '—'}</td>
                            <td class="notes-cell">${student.notes || '—'}</td>
                            <td>
                                <div class="table-actions">
                                    <button class="action-btn" data-student-id="${student.id}" data-action="edit" title="Edit">
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                            <path d="M11.333 2.00004C11.5081 1.82494 11.716 1.68605 11.9447 1.59129C12.1735 1.49653 12.4187 1.44775 12.6663 1.44775C12.914 1.44775 13.1592 1.49653 13.3879 1.59129C13.6167 1.68605 13.8246 1.82494 13.9997 2.00004C14.1748 2.17513 14.3137 2.383 14.4084 2.61178C14.5032 2.84055 14.552 3.08575 14.552 3.33337C14.552 3.58099 14.5032 3.82619 14.4084 4.05497C14.3137 4.28374 14.1748 4.49161 13.9997 4.66671L5.33301 13.3334L1.33301 14.6667L2.66634 10.6667L11.333 2.00004Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                    </button>
                                    <button class="action-btn danger" data-student-id="${student.id}" data-action="delete" title="Delete">
                                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                            <path d="M2 4H14M12.6667 4V13.3333C12.6667 14 12 14.6667 11.3333 14.6667H4.66667C4 14.6667 3.33333 14 3.33333 13.3333V4M5.33333 4V2.66667C5.33333 2 6 1.33333 6.66667 1.33333H9.33333C10 1.33333 10.6667 2 10.6667 2.66667V4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                        </svg>
                                    </button>
                                </div>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    attachListeners(main) {
        // Back to dashboard
        const backBtn = main.querySelector('#back-to-dashboard');
        backBtn.addEventListener('click', () => {
            window.dispatchEvent(new CustomEvent('navigate', {
                detail: { view: 'dashboard' }
            }));
        });
        
        // Add student button
        const addStudentBtn = main.querySelector('#add-student-btn');
        addStudentBtn.addEventListener('click', () => this.openAddStudentModal(main));
        
        // Modal close
        const modalClose = main.querySelector('#student-modal-close');
        const modalOverlay = main.querySelector('#student-modal-overlay');
        const cancelBtn = main.querySelector('#cancel-student');
        
        modalClose?.addEventListener('click', () => this.closeAddStudentModal(main));
        modalOverlay?.addEventListener('click', () => this.closeAddStudentModal(main));
        cancelBtn?.addEventListener('click', () => this.closeAddStudentModal(main));
        
        // Form submission
        const form = main.querySelector('#add-student-form');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleAddStudent(main, form);
        });
        
        // AI Command listeners
        const sendBtn = main.querySelector('#ai-send-btn');
        const commandInput = main.querySelector('#ai-command-input');
        const voiceBtn = main.querySelector('#ai-voice-btn');
        
        sendBtn?.addEventListener('click', () => this.executeAICommand(main, commandInput.value));
        commandInput?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.executeAICommand(main, commandInput.value);
            }
        });
        voiceBtn?.addEventListener('click', () => this.toggleVoiceInput(main));
        
        // Quick actions
        const quickActions = main.querySelectorAll('.quick-action-chip');
        quickActions.forEach(chip => {
            chip.addEventListener('click', () => {
                const action = chip.dataset.action;
                commandInput.value = action;
                this.executeAICommand(main, action);
            });
        });
    }
    
    openAddStudentModal(main) {
        const modal = main.querySelector('#add-student-modal');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    closeAddStudentModal(main) {
        const modal = main.querySelector('#add-student-modal');
        modal.style.display = 'none';
        document.body.style.overflow = '';
        
        const form = main.querySelector('#add-student-form');
        form.reset();
        this.hideModalError(main);
    }
    
    async handleAddStudent(main, form) {
        const formData = new FormData(form);
        const submitBtn = main.querySelector('#submit-student');
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Adding...';
        
        try {
            const studentData = {
                class_id: State.selectedClass.id,
                name: formData.get('name'),
                parent_email: formData.get('parent_email') || null,
                behavior: formData.get('behavior'),
                notes: formData.get('notes') || ''
            };
            
            const response = await API.createStudent(studentData);
            
            if (response.success) {
                State.addStudent(response.student);
                this.students.push(response.student);
                this.closeAddStudentModal(main);
                this.updateStudentsTable(main);
            }
            
        } catch (error) {
            this.showModalError(main, error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Add Student';
        }
    }
    
    showModalError(main, message) {
        const errorDiv = main.querySelector('#student-modal-error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    hideModalError(main) {
        const errorDiv = main.querySelector('#student-modal-error');
        errorDiv.style.display = 'none';
    }
    
    async loadStudents() {
        const container = document.querySelector('#students-table-container');
        
        try {
            const response = await API.getStudents(State.selectedClass.id);
            
            if (response.success) {
                this.students = response.students || [];
                State.setStudents(this.students);
                this.updateStudentsTable(document.querySelector('.class-page-main'));
            }
            
        } catch (error) {
            container.innerHTML = `
                <div class="error-state">
                    <p>Failed to load students: ${error.message}</p>
                </div>
            `;
        }
    }
    
    updateStudentsTable(main) {
        const container = main.querySelector('#students-table-container');
        container.innerHTML = this.renderStudentsTable(this.students);
        
        // Attach action listeners
        const actionBtns = container.querySelectorAll('.action-btn');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const studentId = parseInt(btn.dataset.studentId);
                const action = btn.dataset.action;
                
                if (action === 'delete') {
                    this.handleDeleteStudent(studentId);
                }
            });
        });
    }
    
    async handleDeleteStudent(studentId) {
        if (!confirm('Are you sure you want to remove this student?')) return;
        
        try {
            const response = await API.deleteStudent(studentId);
            
            if (response.success) {
                this.students = this.students.filter(s => s.id !== studentId);
                State.setStudents(this.students);
                this.updateStudentsTable(document.querySelector('.class-page-main'));
            }
        } catch (error) {
            alert('Failed to delete student: ' + error.message);
        }
    }
    
    executeAICommand(main, command) {
        if (!command.trim()) return;
        
        console.log('AI Command:', command);
        // TODO: Send to backend AI orchestrator
        alert(`AI Command Received:\n"${command}"\n\nThis will be processed by the multi-agent system.`);
        
        const input = main.querySelector('#ai-command-input');
        input.value = '';
    }
    
    toggleVoiceInput(main) {
        console.log('Voice input activated');
        // TODO: Implement voice recording
        alert('Voice input will be implemented with the AI orchestrator.');
    }
    
    destroy() {
        document.body.style.overflow = '';
    }
}