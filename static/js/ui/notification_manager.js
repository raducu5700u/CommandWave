/**
 * notification_manager.js - UI module for notification system
 * Provides a stylish, non-intrusive toast notification system
 */

class NotificationManager {
    constructor() {
        this.notificationHistory = [];
        this.maxHistory = 25;
        this.counter = 0;
    }
    
    /**
     * Show a notification toast
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {string} type - Notification type (success, error, info)
     * @param {number} duration - Duration in ms before auto-close (0 for no auto-close)
     * @returns {string} Notification ID
     */
    show(title, message, type = 'info', duration = 5000) {
        const timestamp = Date.now();
        this.notificationHistory.unshift({
            title,
            message,
            type,
            timestamp
        });
        if (this.notificationHistory.length > this.maxHistory) {
            this.notificationHistory.length = this.maxHistory;
        }
        // Update header notification count
        const countElem = document.querySelector('.notification-count');
        if (countElem) {
            let count = parseInt(countElem.textContent, 10) || 0;
            countElem.textContent = count + 1;
        }
        console.log('[NotificationManager] Notification logged:', { title, message, type, timestamp });
        return `notification-${++this.counter}`;
    }
    
    /**
     * Get the notification history
     * @returns {Array} Notification history
     */
    getNotificationHistory() {
        return this.notificationHistory;
    }
    
    /**
     * Reset the notification count
     */
    resetNotificationCount() {
        const countElem = document.querySelector('.notification-count');
        if (countElem) countElem.textContent = '0';
    }
    
    /**
     * Show a success notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {number} duration - Duration in ms before auto-close (0 for no auto-close)
     * @returns {string} Notification ID
     */
    success(title, message, duration = 5000) {
        return this.show(title, message, 'success', duration);
    }
    
    /**
     * Show an error notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {number} duration - Duration in ms before auto-close (0 for no auto-close)
     * @returns {string} Notification ID
     */
    error(title, message, duration = 8000) {
        return this.show(title, message, 'error', duration);
    }
    
    /**
     * Show an info notification
     * @param {string} title - Notification title
     * @param {string} message - Notification message
     * @param {number} duration - Duration in ms before auto-close (0 for no auto-close)
     * @returns {string} Notification ID
     */
    info(title, message, duration = 5000) {
        return this.show(title, message, 'info', duration);
    }
    
    /**
     * Close all notifications (no-op)
     */
    closeAll() { /* No-op for new system */ }
}

// Export as a singleton
export default new NotificationManager();
