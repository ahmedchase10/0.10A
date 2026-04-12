// =============================================
// DIGI-SCHOOL AI — Dashboard Component
// =============================================

import { API } from '../api.js';
import { State } from '../main.js';

export class Dashboard {
    constructor() {
        this.showCreateModal = false;
    }
    
    render() {
        const main = document.createElement('main');
        main.className = 'dashboard-main';
        
        main.innerHTML = `
            <div class="dashboard-header">
                <div class="dashboard-title-section">
                    <h1 class="dashboard-title">My Classes</h1>
                    <p class="dashboard-subtitle">Manage your teaching schedule</p>
                </div>
                <button class="btn-primary" id="create-class-btn">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M10 4V16M4 10H16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                    <span>New Class</span>
                </button>
            </div>
            
            <div class="classes-grid" id="classes-grid">
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Loading classes...</p>
                </div>
            </div>
            
            ${this.renderCreateModal()}
        `;
        
        this.attachListeners(main);
        
        return main;
    }
    
    renderCreateModal() {
        return `
            <div class="modal" id="create-class-modal" style="display: none;">
                <div class="modal-overlay" id="modal-overlay"></div>
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>Create New Class</h2>
                        <button class="modal-close" id="modal-close">
                            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                                <path d="M18 6L6 18M6 6L18 18" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                            </svg>
                        </button>
                    </div>
                    
                    <form class="modal-form" id="create-class-form">
                        <div class="form-group">
                            <label for="class-name">Class Name *</label>
                            <input 
                                type="text" 
                                id="class-name" 
                                name="name" 
                                required 
                                placeholder="e.g., 3G — Mathematics"
                            />
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="class-subject">Subject</label>
                                <input 
                                    type="text" 
                                    id="class-subject" 
                                    name="subject" 
                                    placeholder="Mathematics"
                                />
                            </div>
                            
                            <div class="form-group">
                                <label for="class-period">Period</label>
                                <input 
                                    type="text" 
                                    id="class-period" 
                                    name="period" 
                                    placeholder="Period 3"
                                />
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="class-room">Room</label>
                                <input 
                                    type="text" 
                                    id="class-room" 
                                    name="room" 
                                    placeholder="Room 204"
                                />
                            </div>
                            
                            <div class="form-group">
                                <label for="class-school">School</label>
                                <input 
                                    type="text" 
                                    id="class-school" 
                                    name="school" 
                                    placeholder="Lycée Pilote"
                                />
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="class-color">Class Color</label>
                            <div class="color-picker">
                                ${this.renderColorPicker()}
                            </div>
                        </div>
                        
                        <div class="modal-error" id="modal-error" style="display: none;"></div>
                        
                        <div class="modal-footer">
                            <button type="button" class="btn-secondary" id="cancel-create">
                                Cancel
                            </button>
                            <button type="submit" class="btn-primary" id="submit-create">
                                Create Class
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
    }
    
    renderColorPicker() {
        const colors = [
            '#667eea', '#764ba2', '#f093fb', '#4facfe',
            '#43e97b', '#fa709a', '#fee140', '#30cfd0',
            '#a8edea', '#fed6e3', '#c471f5', '#ff6b6b'
        ];
        
        return colors.map(color => `
            <label class="color-option">
                <input 
                    type="radio" 
                    name="color" 
                    value="${color}" 
                    ${color === '#667eea' ? 'checked' : ''}
                />
                <span class="color-swatch" style="background-color: ${color}"></span>
            </label>
        `).join('');
    }
    
    renderClassesGrid(classes) {
        if (classes.length === 0) {
            return `
                <div class="empty-state">
                    <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                        <rect x="20" y="30" width="80" height="60" rx="8" stroke="currentColor" stroke-width="2" fill="none" opacity="0.2"/>
                        <line x1="30" y1="45" x2="70" y2="45" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                        <line x1="30" y1="55" x2="90" y2="55" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                        <line x1="30" y1="65" x2="80" y2="65" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                    </svg>
                    <h3>No classes yet</h3>
                    <p>Create your first class to get started with Digi-School AI</p>
                    <button class="btn-primary" id="empty-create-btn">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 4V16M4 10H16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                        <span>Create Your First Class</span>
                    </button>
                </div>
            `;
        }
        
        return classes.map(cls => `
            <div class="class-card" data-class-id="${cls.id}">
                <div class="class-card-header" style="background: linear-gradient(135deg, ${cls.color || '#667eea'} 0%, ${this.adjustColor(cls.color || '#667eea', -20)} 100%)">
                    <div class="class-card-info">
                        <h3 class="class-card-name">${cls.name}</h3>
                        <p class="class-card-meta">${cls.subject || 'No subject'}</p>
                    </div>
                    <button class="class-card-menu" data-class-id="${cls.id}">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <circle cx="10" cy="4" r="1.5" fill="currentColor"/>
                            <circle cx="10" cy="10" r="1.5" fill="currentColor"/>
                            <circle cx="10" cy="16" r="1.5" fill="currentColor"/>
                        </svg>
                    </button>
                </div>
                
                <div class="class-card-body">
                    <div class="class-card-details">
                        <div class="detail-item">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <path d="M2 6L8 2L14 6V13C14 13.2652 13.8946 13.5196 13.7071 13.7071C13.5196 13.8946 13.2652 14 13 14H3C2.73478 14 2.48043 13.8946 2.29289 13.7071C2.10536 13.5196 2 13.2652 2 13V6Z" stroke="currentColor" stroke-width="1.5"/>
                            </svg>
                            <span>${cls.room || 'No room'}</span>
                        </div>
                        
                        <div class="detail-item">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/>
                                <path d="M8 4V8L11 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                            </svg>
                            <span>${cls.period || 'No period'}</span>
                        </div>
                        
                        <div class="detail-item">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <path d="M13 2H3C2.44772 2 2 2.44772 2 3V13C2 13.5523 2.44772 14 3 14H13C13.5523 14 14 13.5523 14 13V3C14 2.44772 13.5523 2 13 2Z" stroke="currentColor" stroke-width="1.5"/>
                                <line x1="2" y1="6" x2="14" y2="6" stroke="currentColor" stroke-width="1.5"/>
                            </svg>
                            <span>${cls.school || 'No school'}</span>
                        </div>
                    </div>
                    
                    <button class="class-card-action" data-class-id="${cls.id}">
                        Open Class
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M6 12L10 8L6 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        `).join('');
    }
    
    adjustColor(color, percent) {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255))
            .toString(16).slice(1);
    }
    
    attachListeners(main) {
        // Create class button
        const createBtn = main.querySelector('#create-class-btn');
        createBtn.addEventListener('click', () => this.openCreateModal(main));
        
        // Modal close buttons
        const modalClose = main.querySelector('#modal-close');
        const modalOverlay = main.querySelector('#modal-overlay');
        const cancelBtn = main.querySelector('#cancel-create');
        
        modalClose?.addEventListener('click', () => this.closeCreateModal(main));
        modalOverlay?.addEventListener('click', () => this.closeCreateModal(main));
        cancelBtn?.addEventListener('click', () => this.closeCreateModal(main));
        
        // Form submission
        const form = main.querySelector('#create-class-form');
        form?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleCreateClass(main, form);
        });
    }
    
    openCreateModal(main) {
        const modal = main.querySelector('#create-class-modal');
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }
    
    closeCreateModal(main) {
        const modal = main.querySelector('#create-class-modal');
        modal.style.display = 'none';
        document.body.style.overflow = '';
        
        // Reset form
        const form = main.querySelector('#create-class-form');
        form.reset();
        this.hideModalError(main);
    }
    
    async handleCreateClass(main, form) {
        const formData = new FormData(form);
        const submitBtn = main.querySelector('#submit-create');
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Creating...';
        
        try {
            const classData = {
                name: formData.get('name'),
                subject: formData.get('subject') || null,
                period: formData.get('period') || null,
                room: formData.get('room') || null,
                school: formData.get('school') || null,
                color: formData.get('color') || '#667eea'
            };
            
            const response = await API.createClass(classData);
            
            if (response.success) {
                State.addClass(response.class);
                
                // Update sidebar
                const sidebar = document.querySelector('#app-sidebar');
                if (sidebar) {
                    const sidebarInstance = new (await import('./sidebar.js')).Sidebar();
                    sidebarInstance.update();
                }
                
                this.closeCreateModal(main);
                this.updateClassesGrid(main);
            }
            
        } catch (error) {
            this.showModalError(main, error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Create Class';
        }
    }
    
    showModalError(main, message) {
        const errorDiv = main.querySelector('#modal-error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    hideModalError(main) {
        const errorDiv = main.querySelector('#modal-error');
        errorDiv.style.display = 'none';
    }
    
    async loadClasses() {
        const grid = document.querySelector('#classes-grid');
        
        try {
            const response = await API.getClasses();
            
            if (response.success) {
                State.setClasses(response.classes || []);
                this.updateClassesGrid(document.querySelector('.dashboard-main'));
                
                // Update sidebar
                const sidebar = document.querySelector('#app-sidebar');
                if (sidebar) {
                    const sidebarInstance = new (await import('./sidebar.js')).Sidebar();
                    sidebarInstance.update();
                }
            }
            
        } catch (error) {
            grid.innerHTML = `
                <div class="error-state">
                    <p>Failed to load classes: ${error.message}</p>
                    <button class="btn-primary" onclick="location.reload()">Retry</button>
                </div>
            `;
        }
    }
    
    updateClassesGrid(main) {
        const grid = main.querySelector('#classes-grid');
        grid.innerHTML = this.renderClassesGrid(State.classes);
        
        // Attach listeners to class cards
        const classActions = grid.querySelectorAll('.class-card-action');
        classActions.forEach(btn => {
            btn.addEventListener('click', () => {
                const classId = parseInt(btn.dataset.classId);
                const classData = State.classes.find(c => c.id === classId);
                
                if (classData) {
                    window.dispatchEvent(new CustomEvent('navigate', {
                        detail: { view: 'class-page', classData }
                    }));
                }
            });
        });
        
        // Attach listener to empty state button if present
        const emptyCreateBtn = grid.querySelector('#empty-create-btn');
        if (emptyCreateBtn) {
            emptyCreateBtn.addEventListener('click', () => this.openCreateModal(main));
        }
    }
    
    destroy() {
        document.body.style.overflow = '';
    }
}