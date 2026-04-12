// =============================================
// DIGI-SCHOOL AI — Main Application Controller
// =============================================

import { API } from './api.js';
import { AuthComponent } from './components/auth.js';
import { Sidebar } from './components/sidebar.js';
import { Dashboard } from './components/dashboard.js';
import { ClassPage } from './components/class-page.js';
import { Timetable } from './components/timetable.js';
import { Notifications } from './components/notifications.js';
import { Settings } from './components/settings.js';

// ─── Global State ────────────────────────────

export const State = {
    user: null,
    token: null,
    classes: [],
    students: [],
    notifications: [],
    currentView: 'auth',
    selectedClass: null,
    
    init() {
        const savedToken = localStorage.getItem('digi_token');
        const savedUser = localStorage.getItem('digi_user');
        
        if (savedToken && savedUser) {
            this.token = savedToken;
            this.user = JSON.parse(savedUser);
            API.setToken(savedToken);
            this.currentView = 'dashboard';
        }
    },
    
    login(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('digi_token', token);
        localStorage.setItem('digi_user', JSON.stringify(user));
        API.setToken(token);
        this.currentView = 'dashboard';
    },
    
    logout() {
        this.token = null;
        this.user = null;
        this.classes = [];
        this.students = [];
        this.notifications = [];
        this.selectedClass = null;
        localStorage.removeItem('digi_token');
        localStorage.removeItem('digi_user');
        API.setToken(null);
        this.currentView = 'auth';
    },
    
    setClasses(classes) {
        this.classes = classes;
    },
    
    addClass(classData) {
        this.classes.push(classData);
    },
    
    updateClass(updatedClass) {
        const index = this.classes.findIndex(c => c.id === updatedClass.id);
        if (index !== -1) {
            this.classes[index] = updatedClass;
        }
    },
    
    removeClass(classId) {
        this.classes = this.classes.filter(c => c.id !== classId);
    },
    
    selectClass(classData) {
        this.selectedClass = classData;
        this.currentView = 'class-page';
    },
    
    setStudents(students) {
        this.students = students;
    },
    
    addStudent(student) {
        this.students.push(student);
    },
    
    setNotifications(notifications) {
        this.notifications = notifications;
    },
    
    updateUser(userData) {
        this.user = { ...this.user, ...userData };
        localStorage.setItem('digi_user', JSON.stringify(this.user));
    },
    
    goToDashboard() {
        this.selectedClass = null;
        this.currentView = 'dashboard';
    },
    
    goToTimetable() {
        this.currentView = 'timetable';
    },
    
    goToNotifications() {
        this.currentView = 'notifications';
    },
    
    goToSettings() {
        this.currentView = 'settings';
    }
};

// ─── Router ──────────────────────────────────

export const Router = {
    currentComponent: null,
    
    render() {
        const app = document.getElementById('app');
        
        // Clean up previous component
        if (this.currentComponent && this.currentComponent.destroy) {
            this.currentComponent.destroy();
        }
        
        app.innerHTML = '';
        
        switch(State.currentView) {
            case 'auth':
                this.currentComponent = new AuthComponent();
                app.appendChild(this.currentComponent.render());
                break;
                
            case 'dashboard':
                this.renderDashboard(app);
                break;
                
            case 'class-page':
                this.renderClassPage(app);
                break;
                
            case 'timetable':
                this.renderTimetable(app);
                break;
                
            case 'notifications':
                this.renderNotifications(app);
                break;
                
            case 'settings':
                this.renderSettings(app);
                break;
                
            default:
                this.currentComponent = new AuthComponent();
                app.appendChild(this.currentComponent.render());
        }
    },
    
    renderDashboard(app) {
        const container = document.createElement('div');
        container.className = 'app-container';
        
        const sidebar = new Sidebar();
        const dashboard = new Dashboard();
        
        container.appendChild(sidebar.render());
        container.appendChild(dashboard.render());
        
        app.appendChild(container);
        
        // Store references for cleanup
        this.currentComponent = { 
            destroy: () => {
                if (sidebar.destroy) sidebar.destroy();
                if (dashboard.destroy) dashboard.destroy();
            }
        };
        
        // Load classes
        dashboard.loadClasses();
    },
    
    renderClassPage(app) {
        const container = document.createElement('div');
        container.className = 'app-container';
        
        const sidebar = new Sidebar();
        const classPage = new ClassPage();
        
        container.appendChild(sidebar.render());
        container.appendChild(classPage.render());
        
        app.appendChild(container);
        
        this.currentComponent = { 
            destroy: () => {
                if (sidebar.destroy) sidebar.destroy();
                if (classPage.destroy) classPage.destroy();
            }
        };
        
        // Load students for this class
        classPage.loadStudents();
    },
    
    renderTimetable(app) {
        const container = document.createElement('div');
        container.className = 'app-container';
        
        const sidebar = new Sidebar();
        const timetable = new Timetable();
        
        container.appendChild(sidebar.render());
        container.appendChild(timetable.render());
        
        app.appendChild(container);
        
        this.currentComponent = { 
            destroy: () => {
                if (sidebar.destroy) sidebar.destroy();
                if (timetable.destroy) timetable.destroy();
            }
        };
        
        // Load timetable data
        timetable.loadTimetable();
    },
    
    renderNotifications(app) {
        const container = document.createElement('div');
        container.className = 'app-container';
        
        const sidebar = new Sidebar();
        const notifications = new Notifications();
        
        container.appendChild(sidebar.render());
        container.appendChild(notifications.render());
        
        app.appendChild(container);
        
        this.currentComponent = { 
            destroy: () => {
                if (sidebar.destroy) sidebar.destroy();
                if (notifications.destroy) notifications.destroy();
            }
        };
        
        // Load notifications
        notifications.loadNotifications();
    },
    
    renderSettings(app) {
        const container = document.createElement('div');
        container.className = 'app-container';
        
        const sidebar = new Sidebar();
        const settings = new Settings();
        
        container.appendChild(sidebar.render());
        container.appendChild(settings.render());
        
        app.appendChild(container);
        
        this.currentComponent = { 
            destroy: () => {
                if (sidebar.destroy) sidebar.destroy();
                if (settings.destroy) settings.destroy();
            }
        };
    }
};

// ─── App Initialization ──────────────────────

State.init();
Router.render();

// Listen for auth state changes
window.addEventListener('auth-changed', () => {
    Router.render();
});

// Listen for navigation
window.addEventListener('navigate', (e) => {
    const { view, classData } = e.detail;
    
    switch(view) {
        case 'dashboard':
            State.goToDashboard();
            break;
        case 'class-page':
            if (classData) State.selectClass(classData);
            break;
        case 'timetable':
            State.goToTimetable();
            break;
        case 'notifications':
            State.goToNotifications();
            break;
        case 'settings':
            State.goToSettings();
            break;
    }
    
    Router.render();
});