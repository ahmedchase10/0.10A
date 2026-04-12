// =============================================
// DIGI-SCHOOL AI — Authentication Component
// =============================================

import { API } from '../api.js';
import { State } from '../main.js';

export class AuthComponent {
    constructor() {
        this.mode = 'login'; // 'login' or 'signup'
    }
    
    render() {
        const container = document.createElement('div');
        container.className = 'auth-container';
        
        container.innerHTML = `
            <div class="auth-card">
                <div class="auth-header">
                    <h1>Digi-School AI</h1>
                    <p class="auth-subtitle">Voice-First Teaching Assistant</p>
                </div>
                
                <div class="auth-tabs">
                    <button class="auth-tab ${this.mode === 'login' ? 'active' : ''}" data-tab="login">
                        Login
                    </button>
                    <button class="auth-tab ${this.mode === 'signup' ? 'active' : ''}" data-tab="signup">
                        Sign Up
                    </button>
                </div>
                
                <form class="auth-form" id="auth-form">
                    <div class="form-content">
                        ${this.mode === 'login' ? this.renderLoginForm() : this.renderSignupForm()}
                    </div>
                    
                    <div class="auth-error" id="auth-error" style="display: none;"></div>
                    
                    <button type="submit" class="auth-submit" id="auth-submit">
                        ${this.mode === 'login' ? 'Login' : 'Create Account'}
                    </button>
                </form>
                
                <div class="auth-footer">
                    <p class="auth-info">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M8 1C4.13438 1 1 4.13438 1 8C1 11.8656 4.13438 15 8 15C11.8656 15 15 11.8656 15 8C15 4.13438 11.8656 1 8 1ZM8 11.5C7.58594 11.5 7.25 11.1641 7.25 10.75C7.25 10.3359 7.58594 10 8 10C8.41406 10 8.75 10.3359 8.75 10.75C8.75 11.1641 8.41406 11.5 8 11.5ZM8.75 8.5C8.75 8.91406 8.41406 9.25 8 9.25C7.58594 9.25 7.25 8.91406 7.25 8.5V5C7.25 4.58594 7.58594 4.25 8 4.25C8.41406 4.25 8.75 4.58594 8.75 5V8.5Z" fill="currentColor"/>
                        </svg>
                        Your data is stored securely and never shared
                    </p>
                </div>
            </div>
        `;
        
        // Attach event listeners
        this.attachListeners(container);
        
        return container;
    }
    
    renderLoginForm() {
        return `
            <div class="form-group">
                <label for="login-email">Email</label>
                <input 
                    type="email" 
                    id="login-email" 
                    name="email" 
                    required 
                    autocomplete="email"
                    placeholder="teacher@school.edu"
                />
            </div>
            
            <div class="form-group">
                <label for="login-password">Password</label>
                <input 
                    type="password" 
                    id="login-password" 
                    name="password" 
                    required 
                    autocomplete="current-password"
                    placeholder="Enter your password"
                />
            </div>
        `;
    }
    
    renderSignupForm() {
        return `
            <div class="form-group">
                <label for="signup-name">Full Name</label>
                <input 
                    type="text" 
                    id="signup-name" 
                    name="name" 
                    required 
                    autocomplete="name"
                    placeholder="John Smith"
                />
            </div>
            
            <div class="form-group">
                <label for="signup-email">Email</label>
                <input 
                    type="email" 
                    id="signup-email" 
                    name="email" 
                    required 
                    autocomplete="email"
                    placeholder="teacher@school.edu"
                />
            </div>
            
            <div class="form-row">
                <div class="form-group">
                    <label for="signup-subject">Subject</label>
                    <input 
                        type="text" 
                        id="signup-subject" 
                        name="subject" 
                        placeholder="Mathematics"
                    />
                </div>
                
                <div class="form-group">
                    <label for="signup-initials">Initials</label>
                    <input 
                        type="text" 
                        id="signup-initials" 
                        name="initials" 
                        maxlength="5"
                        placeholder="JS"
                    />
                </div>
            </div>
            
            <div class="form-group">
                <label for="signup-password">Password</label>
                <input 
                    type="password" 
                    id="signup-password" 
                    name="password" 
                    required 
                    autocomplete="new-password"
                    placeholder="Minimum 8 characters"
                />
            </div>
        `;
    }
    
    attachListeners(container) {
        // Tab switching
        const tabs = container.querySelectorAll('.auth-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.mode = e.target.dataset.tab;
                this.updateForm(container);
            });
        });
        
        // Form submission
        const form = container.querySelector('#auth-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit(container);
        });
    }
    
    updateForm(container) {
        // Update tabs
        container.querySelectorAll('.auth-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === this.mode);
        });
        
        // Update form content
        const formContent = container.querySelector('.form-content');
        formContent.innerHTML = this.mode === 'login' 
            ? this.renderLoginForm() 
            : this.renderSignupForm();
        
        // Update button text
        const submitBtn = container.querySelector('#auth-submit');
        submitBtn.textContent = this.mode === 'login' ? 'Login' : 'Create Account';
        
        // Hide error
        this.hideError(container);
    }
    
    async handleSubmit(container) {
        const form = container.querySelector('#auth-form');
        const formData = new FormData(form);
        const submitBtn = container.querySelector('#auth-submit');
        
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.textContent = this.mode === 'login' ? 'Logging in...' : 'Creating account...';
        
        try {
            let response;
            
            if (this.mode === 'login') {
                response = await API.login(
                    formData.get('email'),
                    formData.get('password')
                );
            } else {
                response = await API.register(
                    formData.get('name'),
                    formData.get('email'),
                    formData.get('password'),
                    formData.get('initials')
                );
            }
            
            // Backend returns: { success: true, token, teacher: {id, name, email} }
            if (response.success) {
                State.login(response.token, response.teacher);
                window.dispatchEvent(new CustomEvent('auth-changed'));
            }
            
        } catch (error) {
            this.showError(container, error.message);
            submitBtn.disabled = false;
            submitBtn.textContent = this.mode === 'login' ? 'Login' : 'Create Account';
        }
    }
    
    showError(container, message) {
        const errorDiv = container.querySelector('#auth-error');
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    hideError(container) {
        const errorDiv = container.querySelector('#auth-error');
        errorDiv.style.display = 'none';
    }
    
    destroy() {
        // Cleanup if needed
    }
}