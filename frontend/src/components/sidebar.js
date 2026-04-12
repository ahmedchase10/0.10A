// =============================================
// DIGI-SCHOOL AI — Sidebar Component
// =============================================

import { State } from '../main.js';

export class Sidebar {
    constructor() {
        this.isExpanded = true;
    }
    
    render() {
        const sidebar = document.createElement('aside');
        sidebar.className = `sidebar ${this.isExpanded ? 'expanded' : 'collapsed'}`;
        sidebar.id = 'app-sidebar';
        
        sidebar.innerHTML = `
            <div class="sidebar-header">
                <div class="sidebar-logo">
                    <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
                        <rect width="32" height="32" rx="8" fill="url(#logo-gradient)"/>
                        <path d="M16 8L8 12V20L16 24L24 20V12L16 8Z" fill="white" opacity="0.9"/>
                        <path d="M16 16L8 20V12L16 16Z" fill="white" opacity="0.6"/>
                        <defs>
                            <linearGradient id="logo-gradient" x1="0" y1="0" x2="32" y2="32">
                                <stop offset="0%" stop-color="#667eea"/>
                                <stop offset="100%" stop-color="#764ba2"/>
                            </linearGradient>
                        </defs>
                    </svg>
                    <span class="sidebar-title">Digi-School AI</span>
                </div>
                <button class="sidebar-toggle" id="sidebar-toggle" aria-label="Toggle sidebar">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M7.5 15L12.5 10L7.5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            </div>
            
            <nav class="sidebar-nav">
                <div class="nav-section">
                    <button class="nav-item ${State.currentView === 'dashboard' ? 'active' : ''}" data-nav="dashboard">
                        <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M3 7L10 2L17 7V17C17 17.5304 16.7893 18.0391 16.4142 18.4142C16.0391 18.7893 15.5304 19 15 19H5C4.46957 19 3.96086 18.7893 3.58579 18.4142C3.21071 18.0391 3 17.5304 3 17V7Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <span class="nav-label">Dashboard</span>
                    </button>
                    
                    <button class="nav-item ${State.currentView === 'timetable' ? 'active' : ''}" data-nav="timetable">
                        <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <rect x="3" y="4" width="14" height="14" rx="2" stroke="currentColor" stroke-width="2"/>
                            <line x1="3" y1="8" x2="17" y2="8" stroke="currentColor" stroke-width="2"/>
                            <line x1="8" y1="4" x2="8" y2="18" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span class="nav-label">Timetable</span>
                    </button>
                    
                    <button class="nav-item ${State.currentView === 'notifications' ? 'active' : ''}" data-nav="notifications">
                        <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 2C7.2 2 5 4.2 5 7V10L3 12V13H17V12L15 10V7C15 4.2 12.8 2 10 2Z" stroke="currentColor" stroke-width="2"/>
                            <path d="M8.5 13C8.5 14.3807 9.11929 15 10.5 15C11.8807 15 12.5 14.3807 12.5 13" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span class="nav-label">Notifications</span>
                        ${State.notifications.filter(n => !n.read).length > 0 ? `
                            <span class="notification-badge">${State.notifications.filter(n => !n.read).length}</span>
                        ` : ''}
                    </button>
                    
                    <button class="nav-item ${State.currentView === 'settings' ? 'active' : ''}" data-nav="settings">
                        <svg class="nav-icon" width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 12.5C11.3807 12.5 12.5 11.3807 12.5 10C12.5 8.61929 11.3807 7.5 10 7.5C8.61929 7.5 7.5 8.61929 7.5 10C7.5 11.3807 8.61929 12.5 10 12.5Z" stroke="currentColor" stroke-width="2"/>
                            <path d="M16.1647 12.5C16.0583 12.8214 16.0583 13.1786 16.1647 13.5L17.5 17.5L13.5 16.1647C13.1786 16.0583 12.8214 16.0583 12.5 16.1647L10 17.5L7.5 16.1647C7.17857 16.0583 6.82143 16.0583 6.5 16.1647L2.5 17.5L3.83529 13.5C3.94171 13.1786 3.94171 12.8214 3.83529 12.5L2.5 8.5L6.5 9.83529C6.82143 9.94171 7.17857 9.94171 7.5 9.83529L10 8.5L12.5 9.83529C12.8214 9.94171 13.1786 9.94171 13.5 9.83529L17.5 8.5L16.1647 12.5Z" stroke="currentColor" stroke-width="2"/>
                        </svg>
                        <span class="nav-label">Settings</span>
                    </button>
                </div>
                
                <div class="nav-section">
                    <div class="nav-section-header">
                        <span class="nav-section-title">My Classes</span>
                        <span class="nav-section-count">${State.classes.length}</span>
                    </div>
                    <div class="nav-classes" id="nav-classes">
                        ${this.renderClassList()}
                    </div>
                </div>
            </nav>
            
            <div class="sidebar-footer">
                <div class="user-profile">
                    <div class="user-avatar">
                        ${State.user ? State.user.name.charAt(0).toUpperCase() : 'U'}
                    </div>
                    <div class="user-info">
                        <div class="user-name">${State.user ? State.user.name : 'User'}</div>
                        <div class="user-email">${State.user ? State.user.email : ''}</div>
                    </div>
                    <button class="user-logout" id="user-logout" title="Logout">
                        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
                            <path d="M6.75 15.75H3.75C3.35218 15.75 2.97064 15.592 2.68934 15.3107C2.40804 15.0294 2.25 14.6478 2.25 14.25V3.75C2.25 3.35218 2.40804 2.97064 2.68934 2.68934C2.97064 2.40804 3.35218 2.25 3.75 2.25H6.75M12 12.75L15.75 9M15.75 9L12 5.25M15.75 9H6.75" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
        
        this.attachListeners(sidebar);
        
        return sidebar;
    }
    
    renderClassList() {
        if (State.classes.length === 0) {
            return `
                <div class="nav-empty">
                    <p>No classes yet</p>
                    <small>Create your first class to get started</small>
                </div>
            `;
        }
        
        return State.classes.map(cls => `
            <button class="nav-class ${State.selectedClass?.id === cls.id ? 'active' : ''}" 
                    data-class-id="${cls.id}">
                <span class="class-color" style="background-color: ${cls.color || '#667eea'}"></span>
                <div class="class-info">
                    <div class="class-name">${cls.name}</div>
                    <div class="class-meta">${cls.subject || ''} ${cls.period ? `• ${cls.period}` : ''}</div>
                </div>
            </button>
        `).join('');
    }
    
    attachListeners(sidebar) {
        // Toggle sidebar
        const toggleBtn = sidebar.querySelector('#sidebar-toggle');
        toggleBtn.addEventListener('click', () => {
            this.isExpanded = !this.isExpanded;
            sidebar.classList.toggle('expanded', this.isExpanded);
            sidebar.classList.toggle('collapsed', !this.isExpanded);
        });
        
        // Navigation items
        const navItems = sidebar.querySelectorAll('[data-nav]');
        navItems.forEach(btn => {
            btn.addEventListener('click', () => {
                const view = btn.dataset.nav;
                window.dispatchEvent(new CustomEvent('navigate', { 
                    detail: { view } 
                }));
            });
        });
        
        // Class navigation
        const classButtons = sidebar.querySelectorAll('.nav-class');
        classButtons.forEach(btn => {
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
        
        // Logout
        const logoutBtn = sidebar.querySelector('#user-logout');
        logoutBtn.addEventListener('click', () => {
            if (confirm('Are you sure you want to logout?')) {
                State.logout();
                window.dispatchEvent(new CustomEvent('auth-changed'));
            }
        });
    }
    
    update() {
        const navClasses = document.querySelector('#nav-classes');
        const navCount = document.querySelector('.nav-section-count');
        
        if (navClasses) {
            navClasses.innerHTML = this.renderClassList();
            
            // Re-attach class navigation listeners
            const classButtons = navClasses.querySelectorAll('.nav-class');
            classButtons.forEach(btn => {
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
        }
        
        if (navCount) {
            navCount.textContent = State.classes.length;
        }
        
        // Update notification badge
        const notifItem = document.querySelector('[data-nav="notifications"]');
        if (notifItem) {
            const existingBadge = notifItem.querySelector('.notification-badge');
            const unreadCount = State.notifications.filter(n => !n.read).length;
            
            if (unreadCount > 0) {
                if (existingBadge) {
                    existingBadge.textContent = unreadCount;
                } else {
                    const badge = document.createElement('span');
                    badge.className = 'notification-badge';
                    badge.textContent = unreadCount;
                    notifItem.appendChild(badge);
                }
            } else if (existingBadge) {
                existingBadge.remove();
            }
        }
    }
    
    destroy() {
        // Cleanup if needed
    }
}