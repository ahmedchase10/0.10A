// =============================================
// DIGI-SCHOOL AI — Settings Component
// Teacher profile and account management
// =============================================

import { State } from '../main.js';
import { API } from '../api.js';

export class Settings {
    constructor() {
        this.activeTab = 'profile';
    }
    
    render() {
        const main = document.createElement('main');
        main.className = 'settings-main';
        
        main.innerHTML = `
            <div class="settings-header">
                <h1 class="settings-title">Settings</h1>
                <p class="settings-subtitle">Manage your account and preferences</p>
            </div>
            
            <div class="settings-container">
                <div class="settings-tabs">
                    <button class="settings-tab ${this.activeTab === 'profile' ? 'active' : ''}" data-tab="profile">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 10C12.0711 10 13.75 8.32107 13.75 6.25C13.75 4.17893 12.0711 2.5 10 2.5C7.92893 2.5 6.25 4.17893 6.25 6.25C6.25 8.32107 7.92893 10 10 10Z" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M3.75 17.5C3.75 14.0482 6.54822 11.25 10 11.25C13.4518 11.25 16.25 14.0482 16.25 17.5" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        Profile
                    </button>
                    <button class="settings-tab ${this.activeTab === 'security' ? 'active' : ''}" data-tab="security">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 1.875L3.125 5L10 8.125L16.875 5L10 1.875Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M3.125 13.75V5L10 8.125" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                            <path d="M16.875 5V13.75C16.875 15.8211 13.7563 17.5 10 17.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        Security
                    </button>
                    <button class="settings-tab ${this.activeTab === 'preferences' ? 'active' : ''}" data-tab="preferences">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path d="M10 12.5C11.3807 12.5 12.5 11.3807 12.5 10C12.5 8.61929 11.3807 7.5 10 7.5C8.61929 7.5 7.5 8.61929 7.5 10C7.5 11.3807 8.61929 12.5 10 12.5Z" stroke="currentColor" stroke-width="1.5"/>
                            <path d="M16.1647 12.5C16.0583 12.8214 16.0583 13.1786 16.1647 13.5L17.5 17.5L13.5 16.1647C13.1786 16.0583 12.8214 16.0583 12.5 16.1647L10 17.5L7.5 16.1647C7.17857 16.0583 6.82143 16.0583 6.5 16.1647L2.5 17.5L3.83529 13.5C3.94171 13.1786 3.94171 12.8214 3.83529 12.5L2.5 8.5L6.5 9.83529C6.82143 9.94171 7.17857 9.94171 7.5 9.83529L10 8.5L12.5 9.83529C12.8214 9.94171 13.1786 9.94171 13.5 9.83529L17.5 8.5L16.1647 12.5Z" stroke="currentColor" stroke-width="1.5"/>
                        </svg>
                        Preferences
                    </button>
                </div>
                
                <div class="settings-content" id="settings-content">
                    ${this.renderTabContent()}
                </div>
            </div>
        `;
        
        this.attachListeners(main);
        
        return main;
    }
    
    renderTabContent() {
        switch(this.activeTab) {
            case 'profile':
                return this.renderProfileTab();
            case 'security':
                return this.renderSecurityTab();
            case 'preferences':
                return this.renderPreferencesTab();
            default:
                return '';
        }
    }
    
    renderProfileTab() {
        return `
            <div class="settings-section">
                <h2>Profile Information</h2>
                <p class="section-description">Update your personal information and teaching details</p>
                
                <form class="settings-form" id="profile-form">
                    <div class="form-group">
                        <label for="profile-name">Full Name *</label>
                        <input 
                            type="text" 
                            id="profile-name" 
                            name="name" 
                            value="${State.user?.name || ''}"
                            required
                        />
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="profile-initials">Initials</label>
                            <input 
                                type="text" 
                                id="profile-initials" 
                                name="initials" 
                                value="${State.user?.initials || ''}"
                                maxlength="5"
                            />
                        </div>
                        
                        <div class="form-group">
                            <label for="profile-email">Email</label>
                            <input 
                                type="email" 
                                id="profile-email" 
                                value="${State.user?.email || ''}"
                                disabled
                            />
                            <small>Email cannot be changed</small>
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label for="profile-subject">Primary Subject</label>
                            <input 
                                type="text" 
                                id="profile-subject" 
                                name="subject" 
                                placeholder="Mathematics"
                            />
                        </div>
                        
                        <div class="form-group">
                            <label for="profile-school">School</label>
                            <input 
                                type="text" 
                                id="profile-school" 
                                name="school" 
                                placeholder="Lycée Pilote"
                            />
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="profile-grades">Grade Levels</label>
                        <input 
                            type="text" 
                            id="profile-grades" 
                            name="grades" 
                            placeholder="e.g., 9th, 10th, 11th"
                        />
                    </div>
                    
                    <div class="form-success" id="profile-success" style="display: none;"></div>
                    <div class="form-error" id="profile-error" style="display: none;"></div>
                    
                    <button type="submit" class="btn-primary" id="save-profile">
                        Save Changes
                    </button>
                </form>
            </div>
        `;
    }
    
    renderSecurityTab() {
        return `
            <div class="settings-section">
                <h2>Password & Security</h2>
                <p class="section-description">Keep your account secure</p>
                
                <form class="settings-form" id="security-form">
                    <div class="form-group">
                        <label for="current-password">Current Password *</label>
                        <input 
                            type="password" 
                            id="current-password" 
                            name="current_password" 
                            required
                            autocomplete="current-password"
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="new-password">New Password *</label>
                        <input 
                            type="password" 
                            id="new-password" 
                            name="new_password" 
                            required
                            autocomplete="new-password"
                            placeholder="Minimum 8 characters"
                        />
                    </div>
                    
                    <div class="form-group">
                        <label for="confirm-password">Confirm New Password *</label>
                        <input 
                            type="password" 
                            id="confirm-password" 
                            name="confirm_password" 
                            required
                            autocomplete="new-password"
                        />
                    </div>
                    
                    <div class="form-success" id="security-success" style="display: none;"></div>
                    <div class="form-error" id="security-error" style="display: none;"></div>
                    
                    <button type="submit" class="btn-primary" id="change-password">
                        Change Password
                    </button>
                </form>
                
                <div class="danger-zone">
                    <h3>Danger Zone</h3>
                    <p>Once you delete your account, there is no going back. Please be certain.</p>
                    <button class="btn-danger" id="delete-account">
                        Delete Account
                    </button>
                </div>
            </div>
        `;
    }
    
    renderPreferencesTab() {
        return `
            <div class="settings-section">
                <h2>Application Preferences</h2>
                <p class="section-description">Customize your Digi-School experience</p>
                
                <div class="preference-group">
                    <h3>Voice Settings</h3>
                    <div class="preference-item">
                        <div class="preference-info">
                            <strong>Enable Voice Commands</strong>
                            <p>Allow voice input for AI commands</p>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    
                    <div class="preference-item">
                        <div class="preference-info">
                            <strong>Auto-transcribe Voice Notes</strong>
                            <p>Automatically transcribe and save voice notes</p>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
                
                <div class="preference-group">
                    <h3>Notifications</h3>
                    <div class="preference-item">
                        <div class="preference-info">
                            <strong>Student Absence Alerts</strong>
                            <p>Get notified when students exceed absence threshold</p>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                    
                    <div class="preference-item">
                        <div class="preference-info">
                            <strong>Behavior Flags</strong>
                            <p>Receive alerts for repeated behavioral issues</p>
                        </div>
                        <label class="toggle-switch">
                            <input type="checkbox" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
                
                <div class="preference-group">
                    <h3>Display</h3>
                    <div class="preference-item">
                        <div class="preference-info">
                            <strong>Theme</strong>
                            <p>Choose your preferred color scheme</p>
                        </div>
                        <select class="preference-select">
                            <option value="light" selected>Light</option>
                            <option value="dark">Dark</option>
                            <option value="auto">Auto</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }
    
    attachListeners(main) {
        // Tab switching
        const tabs = main.querySelectorAll('.settings-tab');
        tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.activeTab = e.currentTarget.dataset.tab;
                this.updateTabContent(main);
            });
        });
        
        // Form submissions
        const profileForm = main.querySelector('#profile-form');
        profileForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleProfileUpdate(main, profileForm);
        });
        
        const securityForm = main.querySelector('#security-form');
        securityForm?.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handlePasswordChange(main, securityForm);
        });
    }
    
    updateTabContent(main) {
        // Update tab active state
        main.querySelectorAll('.settings-tab').forEach(tab => {
            tab.classList.toggle('active', tab.dataset.tab === this.activeTab);
        });
        
        // Update content
        const content = main.querySelector('#settings-content');
        content.innerHTML = this.renderTabContent();
        
        // Re-attach form listeners
        this.attachListeners(main);
    }
    
    async handleProfileUpdate(main, form) {
        const formData = new FormData(form);
        const submitBtn = main.querySelector('#save-profile');
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
        
        try {
            const profileData = {
                name: formData.get('name'),
                initials: formData.get('initials'),
                subject: formData.get('subject'),
                school: formData.get('school'),
                grades: formData.get('grades')
            };
            
            const response = await API.updateTeacherProfile(profileData);
            
            if (response.success) {
                State.updateUser(response.teacher);
                this.showSuccess(main, 'profile-success', 'Profile updated successfully!');
            }
            
        } catch (error) {
            this.showError(main, 'profile-error', error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Save Changes';
        }
    }
    
    async handlePasswordChange(main, form) {
        const formData = new FormData(form);
        const submitBtn = main.querySelector('#change-password');
        
        const newPassword = formData.get('new_password');
        const confirmPassword = formData.get('confirm_password');
        
        if (newPassword !== confirmPassword) {
            this.showError(main, 'security-error', 'Passwords do not match');
            return;
        }
        
        if (newPassword.length < 8) {
            this.showError(main, 'security-error', 'Password must be at least 8 characters');
            return;
        }
        
        submitBtn.disabled = true;
        submitBtn.textContent = 'Changing...';
        
        try {
            const response = await API.changePassword(
                formData.get('current_password'),
                newPassword
            );
            
            if (response.success) {
                form.reset();
                this.showSuccess(main, 'security-success', 'Password changed successfully!');
            }
            
        } catch (error) {
            this.showError(main, 'security-error', error.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Change Password';
        }
    }
    
    showSuccess(main, elementId, message) {
        const successDiv = main.querySelector(`#${elementId}`);
        successDiv.textContent = message;
        successDiv.style.display = 'block';
        
        setTimeout(() => {
            successDiv.style.display = 'none';
        }, 5000);
    }
    
    showError(main, elementId, message) {
        const errorDiv = main.querySelector(`#${elementId}`);
        errorDiv.textContent = message;
        errorDiv.style.display = 'block';
    }
    
    destroy() {
        // Cleanup if needed
    }
}