/**
 * Communications Modal Controller
 * Handles the communications interface functionality
 */

import { ModalController } from './modal_controller.js';

export class CommunicationsModal {
    constructor() {
        this.modalId = 'communicationsModal';
        this.modalController = new ModalController(this.modalId);
        
        // DOM Elements
        this.modal = document.getElementById(this.modalId);
        this.commContainer = document.getElementById('commContainer');
        this.commInput = document.getElementById('commInput');
        this.sendButton = document.getElementById('commSendBtn');
        this.clearButton = document.getElementById('clearCommBtn');
        this.cancelButton = document.getElementById('cancelCommBtn');
        this.closeButton = document.getElementById('closeCommModal');
        this.statusIndicator = document.getElementById('commStatusIndicator');
        this.statusText = document.getElementById('commStatusText');
        
        // Message history
        this.messages = [];
        
        // Bind event listeners
        this.bindEvents();
        
        // Initialize
        this.loadMessages();
        this.updateStatus('online');
    }
    
    /**
     * Bind all event listeners for the modal
     */
    bindEvents() {
        // Open/close modal
        this.closeButton.addEventListener('click', () => this.modalController.closeModal());
        this.cancelButton.addEventListener('click', () => this.modalController.closeModal());
        
        // Send message
        this.sendButton.addEventListener('click', () => this.sendMessage());
        this.commInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.commInput.addEventListener('input', this.autoResizeTextarea.bind(this));
        
        // Clear history
        this.clearButton.addEventListener('click', () => this.clearMessages());
    }
    
    /**
     * Open the communications modal
     */
    open() {
        this.modalController.openModal();
        this.scrollToBottom();
        this.commInput.focus();
    }
    
    /**
     * Close the communications modal
     */
    close() {
        this.modalController.closeModal();
    }
    
    /**
     * Send a new message from the input field
     */
    sendMessage() {
        const message = this.commInput.value.trim();
        if (!message) return;
        
        const newMessage = {
            id: Date.now(),
            content: message,
            sender: 'You',
            timestamp: new Date().toISOString(),
            type: 'outgoing'
        };
        
        this.addMessage(newMessage);
        this.saveMessages();
        
        // Clear input
        this.commInput.value = '';
        this.commInput.style.height = 'auto';
        
        // Simulate a response (in a real implementation, this would be an API call)
        this.simulateResponse();
    }
    
    /**
     * Add a message to the UI
     * @param {Object} message - Message object with content, sender, timestamp, type
     */
    addMessage(message) {
        this.messages.push(message);
        
        // Create message element
        const messageEl = document.createElement('div');
        messageEl.className = `comm-message ${message.type}`;
        messageEl.dataset.id = message.id;
        
        const date = new Date(message.timestamp);
        const timeStr = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        
        messageEl.innerHTML = `
            <div class="comm-message-header">
                <span class="comm-message-name">${message.sender}</span>
                <span class="comm-message-time">${timeStr}</span>
            </div>
            <div class="comm-message-content">${this.formatMessageContent(message.content)}</div>
        `;
        
        this.commContainer.appendChild(messageEl);
        this.scrollToBottom();
    }
    
    /**
     * Format message content (handle links, etc.)
     * @param {string} content - Raw message content
     * @returns {string} - Formatted HTML content
     */
    formatMessageContent(content) {
        // Convert URLs to clickable links
        const urlRegex = /(https?:\/\/[^\s]+)/g;
        return content.replace(urlRegex, url => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`)
                     .replace(/\n/g, '<br>');
    }
    
    /**
     * Clear all messages
     */
    clearMessages() {
        // Confirm before clearing
        if (confirm('Are you sure you want to clear all messages?')) {
            this.messages = [];
            this.commContainer.innerHTML = '';
            this.saveMessages();
            
            // Add system message
            this.addStatusMessage('History cleared');
        }
    }
    
    /**
     * Add a status message
     * @param {string} text - Status message text
     */
    addStatusMessage(text) {
        const statusEl = document.createElement('div');
        statusEl.className = 'comm-status';
        statusEl.textContent = text;
        this.commContainer.appendChild(statusEl);
        this.scrollToBottom();
    }
    
    /**
     * Save messages to localStorage
     */
    saveMessages() {
        localStorage.setItem('commandwave_messages', JSON.stringify(this.messages));
    }
    
    /**
     * Load messages from localStorage
     */
    loadMessages() {
        const saved = localStorage.getItem('commandwave_messages');
        if (saved) {
            try {
                this.messages = JSON.parse(saved);
                this.messages.forEach(msg => this.addMessage(msg));
            } catch (err) {
                console.error('Failed to load messages:', err);
                this.messages = [];
            }
        }
    }
    
    /**
     * Scroll container to the bottom
     */
    scrollToBottom() {
        this.commContainer.scrollTop = this.commContainer.scrollHeight;
    }
    
    /**
     * Update the connection status
     * @param {string} status - Status type: 'online', 'offline', or 'connecting'
     * @param {string} message - Optional status message
     */
    updateStatus(status, message) {
        this.statusIndicator.className = 'comm-status-indicator ' + status;
        
        let statusMessage = message;
        if (!statusMessage) {
            switch (status) {
                case 'online':
                    statusMessage = 'System Online';
                    break;
                case 'offline':
                    statusMessage = 'System Offline';
                    break;
                case 'connecting':
                    statusMessage = 'Connecting...';
                    break;
            }
        }
        
        this.statusText.textContent = statusMessage;
    }
    
    /**
     * Auto-resize the input textarea
     */
    autoResizeTextarea() {
        this.commInput.style.height = 'auto';
        this.commInput.style.height = (this.commInput.scrollHeight) + 'px';
        
        // Limit max height
        if (parseInt(this.commInput.style.height) > 100) {
            this.commInput.style.height = '100px';
        }
    }
    
    /**
     * Simulate a response (for demo purposes)
     * In a real implementation, this would be replaced with actual API communication
     */
    simulateResponse() {
        // Show typing indicator
        this.addStatusMessage('System is typing...');
        
        // Simulate delay
        setTimeout(() => {
            // Remove typing indicator (the last status message)
            const statusMessages = this.commContainer.querySelectorAll('.comm-status');
            if (statusMessages.length > 0) {
                statusMessages[statusMessages.length - this.hasNewStatusElement ? 2 : 1].remove();
            }
            
            // Add response
            const response = {
                id: Date.now(),
                content: 'This is a simulated response from the system.',
                sender: 'System',
                timestamp: new Date().toISOString(),
                type: 'incoming'
            };
            this.addMessage(response);
            this.saveMessages();
        }, 1500);
    }
}

// Initialize as a singleton
let communicationsModalInstance = null;

export function getCommunicationsModal() {
    if (!communicationsModalInstance) {
        communicationsModalInstance = new CommunicationsModal();
    }
    return communicationsModalInstance;
}
