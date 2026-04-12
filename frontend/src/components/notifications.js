// =============================================
// DIGI-SCHOOL AI — Notifications Component
// System alerts, flags, and important notices
// =============================================

import { State } from '../main.js';
import { API } from '../api.js';

export class Notifications {
    constructor() {
        this.notifications = [];
    }
    
    render() {
        const main = document.createElement('main');
        main.className = 'notifications-main';
        
        main.innerHTML = `
            <div class="notifications-header">
                <div>
                    <h1 class="notifications-title">Notifications</h1>
                    <p class="notifications-subtitle">System alerts and important updates</p>
                </div>
                <button class="btn-secondary" id="mark-all-read">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M16.6667 5L7.5 14.1667L3.33334 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    Mark All Read
                </button>
            </div>
            
            <div class="notifications-container" id="notifications-container">
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Loading notifications...</p>
                </div>
            </div>
        `;
        
        this.attachListeners(main);
        
        return main;
    }
    
    renderNotificationsList(notifications) {
        if (notifications.length === 0) {
            return `
                <div class="empty-state">
                    <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                        <path d="M60 30C47.8 30 38 39.8 38 52V62L30 70V74H90V70L82 62V52C82 39.8 72.2 30 60 30Z" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                        <path d="M54 80C54 83.3137 56.6863 86 60 86C63.3137 86 66 83.3137 66 80" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                    </svg>
                    <h3>No notifications</h3>
                    <p>You're all caught up!</p>
                </div>
            `;
        }
        
        return `
            <div class="notifications-list">
                ${notifications.map(notif => this.renderNotificationCard(notif)).join('')}
            </div>
        `;
    }
    
    renderNotificationCard(notif) {
        const iconMap = {
            'behavior': `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>`,
            'absence': `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M8 7C8 5.89543 8.89543 5 10 5H14C15.1046 5 16 5.89543 16 7V19H8V7Z" stroke="currentColor" stroke-width="2"/>
                <path d="M20 21H4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M10 9H14M10 13H14" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>`,
            'grade': `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M9 11L12 14L22 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                <path d="M21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>`,
            'system': `<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
                <path d="M12 16V12M12 8H12.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>`
        };
        
        const typeColors = {
            'behavior': '#ff6b6b',
            'absence': '#ffd43b',
            'grade': '#51cf66',
            'system': '#339af0'
        };
        
        const icon = iconMap[notif.type] || iconMap['system'];
        const color = typeColors[notif.type] || typeColors['system'];
        
        return `
            <div class="notification-card ${notif.read ? 'read' : 'unread'}" data-notif-id="${notif.id}">
                <div class="notif-icon" style="background-color: ${color}20; color: ${color}">
                    ${icon}
                </div>
                <div class="notif-content">
                    <div class="notif-header">
                        <span class="notif-type">${notif.type.charAt(0).toUpperCase() + notif.type.slice(1)}</span>
                        <span class="notif-time">${this.formatTime(notif.sent_at)}</span>
                    </div>
                    <p class="notif-message">${notif.message}</p>
                    ${notif.student_name ? `<span class="notif-student">Student: ${notif.student_name}</span>` : ''}
                </div>
                <div class="notif-actions">
                    ${!notif.read ? `
                        <button class="notif-action-btn" data-action="mark-read" data-notif-id="${notif.id}" title="Mark as read">
                            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                <path d="M13.3333 4L6 11.3333L2.66667 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </button>
                    ` : ''}
                    <button class="notif-action-btn danger" data-action="delete" data-notif-id="${notif.id}" title="Delete">
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path d="M2 4H14M12.6667 4V13.3333C12.6667 14 12 14.6667 11.3333 14.6667H4.66667C4 14.6667 3.33333 14 3.33333 13.3333V4M5.33333 4V2.66667C5.33333 2 6 1.33333 6.66667 1.33333H9.33333C10 1.33333 10.6667 2 10.6667 2.66667V4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }
    
    formatTime(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);
        
        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins} min ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        
        return date.toLocaleDateString();
    }
    
    attachListeners(main) {
        const markAllBtn = main.querySelector('#mark-all-read');
        markAllBtn?.addEventListener('click', () => this.markAllAsRead());
    }
    
    async loadNotifications() {
        const container = document.querySelector('#notifications-container');
        
        try {
            const response = await API.getNotifications();
            
            if (response.success) {
                this.notifications = response.notifications || [];
                State.setNotifications(this.notifications);
                this.updateNotificationsList();
            }
            
        } catch (error) {
            // Mock data for demo purposes
            this.notifications = [
                {
                    id: 1,
                    type: 'absence',
                    message: 'Ahmed Ben Ali has been absent for 3 consecutive days',
                    student_name: 'Ahmed Ben Ali',
                    read: false,
                    sent_at: new Date(Date.now() - 3600000).toISOString()
                },
                {
                    id: 2,
                    type: 'behavior',
                    message: 'Mohamed disrupted class for the 3rd time this week',
                    student_name: 'Mohamed',
                    read: false,
                    sent_at: new Date(Date.now() - 7200000).toISOString()
                },
                {
                    id: 3,
                    type: 'system',
                    message: 'Your weekly report card generation is ready',
                    read: true,
                    sent_at: new Date(Date.now() - 86400000).toISOString()
                }
            ];
            
            this.updateNotificationsList();
        }
    }
    
    updateNotificationsList() {
        const container = document.querySelector('#notifications-container');
        container.innerHTML = this.renderNotificationsList(this.notifications);
        
        // Attach action listeners
        const actionBtns = container.querySelectorAll('.notif-action-btn');
        actionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const notifId = parseInt(btn.dataset.notifId);
                const action = btn.dataset.action;
                
                if (action === 'mark-read') {
                    this.markAsRead(notifId);
                } else if (action === 'delete') {
                    this.deleteNotification(notifId);
                }
            });
        });
    }
    
    async markAsRead(notifId) {
        try {
            await API.markNotificationRead(notifId);
            
            const notif = this.notifications.find(n => n.id === notifId);
            if (notif) {
                notif.read = true;
                this.updateNotificationsList();
            }
        } catch (error) {
            console.error('Failed to mark notification as read:', error);
            
            // Fallback for demo
            const notif = this.notifications.find(n => n.id === notifId);
            if (notif) {
                notif.read = true;
                this.updateNotificationsList();
            }
        }
    }
    
    async deleteNotification(notifId) {
        try {
            await API.deleteNotification(notifId);
            
            this.notifications = this.notifications.filter(n => n.id !== notifId);
            this.updateNotificationsList();
        } catch (error) {
            console.error('Failed to delete notification:', error);
            
            // Fallback for demo
            this.notifications = this.notifications.filter(n => n.id !== notifId);
            this.updateNotificationsList();
        }
    }
    
    async markAllAsRead() {
        const unreadNotifs = this.notifications.filter(n => !n.read);
        
        for (const notif of unreadNotifs) {
            await this.markAsRead(notif.id);
        }
    }
    
    destroy() {
        // Cleanup if needed
    }
}