// =============================================
// DIGI-SCHOOL AI — Timetable Component
// Weekly class schedule based on period data
// ============================================

import { State } from '../main.js';

export class Timetable {
    constructor() {
        this.timetableData = null;
    }
    
    render() {
        const main = document.createElement('main');
        main.className = 'timetable-main';
        
        main.innerHTML = `
            <div class="timetable-header">
                <div>
                    <h1 class="timetable-title">Weekly Timetable</h1>
                    <p class="timetable-subtitle">Your teaching schedule at a glance</p>
                </div>
                <button class="btn-secondary" id="print-timetable">
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path d="M5 7V2H15V7" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <path d="M5 14H3C2.46957 14 1.96086 13.7893 1.58579 13.4142C1.21071 13.0391 1 12.5304 1 12V8C1 7.46957 1.21071 6.96086 1.58579 6.58579C1.96086 6.21071 2.46957 6 3 6H17C17.5304 6 18.0391 6.21071 18.4142 6.58579C18.7893 6.96086 19 7.46957 19 8V12C19 12.5304 18.7893 13.0391 18.4142 13.4142C18.0391 13.7893 17.5304 14 17 14H15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        <rect x="5" y="11" width="10" height="7" stroke="currentColor" stroke-width="2"/>
                    </svg>
                    Print
                </button>
            </div>
            
            <div class="timetable-container" id="timetable-container">
                <div class="loading-spinner">
                    <div class="spinner"></div>
                    <p>Loading timetable...</p>
                </div>
            </div>
        `;
        
        this.attachListeners(main);
        
        return main;
    }
    
    renderTimetableGrid(timetableData) {
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
        const periods = this.extractPeriods(timetableData);
        
        if (periods.length === 0) {
            return `
                <div class="empty-state">
                    <svg width="120" height="120" viewBox="0 0 120 120" fill="none">
                        <rect x="20" y="20" width="80" height="80" rx="8" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                        <line x1="20" y1="40" x2="100" y2="40" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                        <line x1="20" y1="60" x2="100" y2="60" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                        <line x1="20" y1="80" x2="100" y2="80" stroke="currentColor" stroke-width="2" opacity="0.2"/>
                    </svg>
                    <h3>No schedule data</h3>
                    <p>Add period information to your classes to see your timetable</p>
                </div>
            `;
        }
        
        return `
            <div class="timetable-grid">
                <div class="timetable-header-row">
                    <div class="period-header">Period</div>
                    ${days.map(day => `
                        <div class="day-header">${day}</div>
                    `).join('')}
                </div>
                
                ${periods.map(period => `
                    <div class="timetable-row">
                        <div class="period-cell">${period}</div>
                        ${days.map(day => this.renderClassCell(timetableData, day, period)).join('')}
                    </div>
                `).join('')}
            </div>
            
            <div class="timetable-legend">
                <h3>Legend</h3>
                <div class="legend-items">
                    ${this.renderLegend(timetableData)}
                </div>
            </div>
        `;
    }
    
    extractPeriods(timetableData) {
        const periodsSet = new Set();
        
        State.classes.forEach(cls => {
            if (cls.period) {
                // Extract period number from formats like "Period 1", "P1", "1st Period", etc.
                const match = cls.period.match(/\d+/);
                if (match) {
                    periodsSet.add(`Period ${match[0]}`);
                } else {
                    periodsSet.add(cls.period);
                }
            }
        });
        
        // Sort periods numerically
        return Array.from(periodsSet).sort((a, b) => {
            const numA = parseInt(a.match(/\d+/)?.[0] || 0);
            const numB = parseInt(b.match(/\d+/)?.[0] || 0);
            return numA - numB;
        });
    }
    
    renderClassCell(timetableData, day, period) {
        // Find class matching this day and period
        // Note: This is a simplified version. In production, you'd store day info in the database
        const classForSlot = State.classes.find(cls => {
            return cls.period && cls.period.includes(period.match(/\d+/)?.[0]);
        });
        
        if (!classForSlot) {
            return '<div class="class-cell empty-cell">—</div>';
        }
        
        return `
            <div class="class-cell" style="border-left: 3px solid ${classForSlot.color || '#667eea'}">
                <div class="cell-class-name">${classForSlot.name}</div>
                <div class="cell-room">${classForSlot.room || ''}</div>
            </div>
        `;
    }
    
    renderLegend(timetableData) {
        return State.classes
            .filter(cls => cls.subject)
            .map(cls => `
                <div class="legend-item">
                    <span class="legend-color" style="background-color: ${cls.color || '#667eea'}"></span>
                    <span class="legend-label">${cls.subject}</span>
                </div>
            `).join('');
    }
    
    attachListeners(main) {
        const printBtn = main.querySelector('#print-timetable');
        printBtn?.addEventListener('click', () => this.printTimetable());
    }
    
    printTimetable() {
        window.print();
    }
    
    async loadTimetable() {
        const container = document.querySelector('#timetable-container');
        
        try {
            // Timetable data is derived from classes with period information
            this.timetableData = {
                classes: State.classes
            };
            
            container.innerHTML = this.renderTimetableGrid(this.timetableData);
            
        } catch (error) {
            container.innerHTML = `
                <div class="error-state">
                    <p>Failed to load timetable: ${error.message}</p>
                </div>
            `;
        }
    }
    
    destroy() {
        // Cleanup if needed
    }
}