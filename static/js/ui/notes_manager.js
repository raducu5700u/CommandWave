/**
 * NotesManager - Module for handling notes functionality
 * Controls global notes and tab-specific notes
 */
export default class NotesManager {
    constructor() {
        // Note buttons
        this.globalNotesBtn = document.getElementById('globalNotesBtn');
        this.tabNotesBtn = document.getElementById('tabNotesBtn');
        
        // Note panels
        this.globalNotesPanel = document.getElementById('globalNotesPanel');
        this.tabNotesPanel = document.getElementById('tabNotesPanel');
        
        // Note textareas - use correct IDs from HTML
        this.globalNotesTextarea = document.getElementById('globalNotesText');
        this.tabNotesTextarea = document.getElementById('tabNotesText');
        
        // Current tab name element
        this.currentTabNameEl = document.getElementById('currentTabName');
        
        // Close buttons
        this.closeButtons = document.querySelectorAll('.close-notes-btn');
        
        // Current active tab port (for tab-specific notes)
        this.currentTabPort = null;
        this.currentTabName = null;
        
        // Storage keys
        this.GLOBAL_NOTES_KEY = 'commandwave_global_notes';
        this.TAB_NOTES_PREFIX = 'commandwave_tab_notes_';
        
        // Debounce timer for auto-save
        this.debounceTimer = null;
        
        // Flag to prevent recursive sync events when updating from remote
        this.updatingFromRemote = false;
        
        // API Base URL
        const apiBaseUrlElem = document.getElementById('api-base-url');
        this.apiBaseUrl = apiBaseUrlElem && apiBaseUrlElem.dataset.url 
            ? apiBaseUrlElem.dataset.url 
            : window.location.origin + '/';
    }
    
    /**
     * Initialize notes manager
     */
    init() {
        try {
            this.setupEventListeners();
            
            // Load global notes from server first, fallback to localStorage if that fails
            this.loadGlobalNotesFromServer()
                .catch(error => {
                    console.warn('Failed to load global notes from server, falling back to localStorage:', error);
                    this.loadGlobalNotes();
                });
                
            console.log('Notes manager initialized');
        } catch (error) {
            console.error('Error initializing notes manager:', error);
        }
    }
    
    /**
     * Setup event listeners for notes buttons and panels
     */
    setupEventListeners() {
        // Global notes button
        if (this.globalNotesBtn) {
            this.globalNotesBtn.addEventListener('click', () => this.toggleGlobalNotes());
        }
        
        // Tab notes button
        if (this.tabNotesBtn) {
            this.tabNotesBtn.addEventListener('click', () => this.toggleTabNotes());
        }
        
        // Close buttons
        this.closeButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const panel = e.target.closest('.notes-panel');
                if (panel) {
                    panel.classList.remove('visible');
                    
                    // Save notes on close
                    if (panel.id === 'globalNotesPanel') {
                        this.saveGlobalNotes();
                        this.saveGlobalNotesToServer().catch(error => {
                            console.warn('Failed to save global notes to server:', error);
                        });
                    } else if (panel.id === 'tabNotesPanel') {
                        this.saveTabNotes();
                        this.saveTabNotesToServer().catch(error => {
                            console.warn('Failed to save tab notes to server:', error);
                        });
                    }
                }
            });
        });
        
        // Auto-save global notes when typing
        if (this.globalNotesTextarea) {
            // Listen for changes to global notes and dispatch event for sync
            this.globalNotesTextarea.addEventListener('input', () => {
                if (!this.updatingFromRemote) {
                    this.debounce(() => {
                        this.saveGlobalNotes();
                        this.saveGlobalNotesToServer().catch(error => {
                            console.warn('Failed to save global notes to server:', error);
                        });
                        // Dispatch custom event for sync manager to catch
                        document.dispatchEvent(new CustomEvent('local-global-notes-updated', {
                            detail: { 
                                content: this.globalNotesTextarea.value 
                            }
                        }));
                    }, 500);
                }
            });
        }
        
        // Auto-save tab notes when typing
        if (this.tabNotesTextarea) {
            // Listen for changes to tab notes and dispatch event for sync
            this.tabNotesTextarea.addEventListener('input', () => {
                if (!this.updatingFromRemote && this.currentTabName) {
                    this.debounce(() => {
                        this.saveTabNotes();
                        this.saveTabNotesToServer().catch(error => {
                            console.warn('Failed to save tab notes to server:', error);
                        });
                        // Dispatch custom event for sync manager to catch
                        document.dispatchEvent(new CustomEvent('local-tab-notes-updated', {
                            detail: { 
                                terminalId: this.currentTabName,
                                content: this.tabNotesTextarea.value 
                            }
                        }));
                    }, 500);
                }
            });
        }
        
        // Listen for tab changes from terminal manager
        document.addEventListener('terminal-tab-changed', (e) => {
            if (e.detail && e.detail.port) {
                this.handleTabChange(e.detail.port);
            }
        });
        
        // Initial tab detection
        this.detectCurrentTab();
    }
    
    /**
     * Detect current active terminal tab
     */
    detectCurrentTab() {
        const activeTab = document.querySelector('.tab-btn.active');
        if (activeTab) {
            const port = activeTab.getAttribute('data-port');
            if (port) {
                this.currentTabPort = port;
                this.updateTabNameDisplay(activeTab.textContent || 'Terminal');
            }
        }
    }
    
    /**
     * Update the tab name display in the notes panel
     * @param {string} name - Tab name to display
     */
    updateTabNameDisplay(name) {
        if (this.currentTabNameEl) {
            this.currentTabNameEl.textContent = name;
        }
        this.currentTabName = name;
    }
    
    /**
     * Debounce function to limit frequency of calls
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     */
    debounce(func, wait) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(func, wait);
    }
    
    /**
     * Sanitize terminal name for keys and filenames
     * @param {string} name
     * @returns {string}
     */
    sanitizeName(name) {
        return name.replace(/[^A-Za-z0-9_-]/g, '_')
                   .toLowerCase()
                   .replace(/^_+|_+$/g, '');
    }
    
    /**
     * Toggle global notes panel
     */
    toggleGlobalNotes() {
        if (this.globalNotesPanel) {
            const isVisible = this.globalNotesPanel.classList.contains('visible');
            
            // Close tab notes if open
            if (this.tabNotesPanel && this.tabNotesPanel.classList.contains('visible')) {
                this.tabNotesPanel.classList.remove('visible');
                this.saveTabNotes();
                this.saveTabNotesToServer().catch(error => {
                    console.warn('Failed to save tab notes to server:', error);
                });
            }
            
            // Toggle global notes
            this.globalNotesPanel.classList.toggle('visible');
            
            // Load notes if opening
            if (!isVisible) {
                // Try to load from server, fall back to localStorage
                this.loadGlobalNotesFromServer()
                    .catch(error => {
                        console.warn('Failed to load global notes from server, falling back to localStorage:', error);
                        this.loadGlobalNotes();
                    });
                
                // Focus textarea
                if (this.globalNotesTextarea) {
                    setTimeout(() => this.globalNotesTextarea.focus(), 100);
                }
            } else {
                // Save notes if closing
                this.saveGlobalNotes();
                this.saveGlobalNotesToServer().catch(error => {
                    console.warn('Failed to save global notes to server:', error);
                });
            }
        }
    }
    
    /**
     * Toggle tab notes panel
     */
    toggleTabNotes() {
        if (this.tabNotesPanel) {
            const isVisible = this.tabNotesPanel.classList.contains('visible');
            
            // Close global notes if open
            if (this.globalNotesPanel && this.globalNotesPanel.classList.contains('visible')) {
                this.globalNotesPanel.classList.remove('visible');
                this.saveGlobalNotes();
                this.saveGlobalNotesToServer().catch(error => {
                    console.warn('Failed to save global notes to server:', error);
                });
            }
            
            // Toggle tab notes
            this.tabNotesPanel.classList.toggle('visible');
            
            // Get current tab port
            const activeTab = document.querySelector('.tab-btn.active');
            if (activeTab) {
                this.currentTabPort = activeTab.getAttribute('data-port');
                this.updateTabNameDisplay(activeTab.textContent || 'Terminal');
            }
            
            // Load notes if opening
            if (!isVisible) {
                // Try to load from server, fall back to localStorage
                this.loadTabNotesFromServer()
                    .catch(error => {
                        console.warn('Failed to load tab notes from server, falling back to localStorage:', error);
                        this.loadTabNotes();
                    });
                
                // Focus textarea
                if (this.tabNotesTextarea) {
                    setTimeout(() => this.tabNotesTextarea.focus(), 100);
                }
            } else {
                // Save notes if closing
                this.saveTabNotes();
                this.saveTabNotesToServer().catch(error => {
                    console.warn('Failed to save tab notes to server:', error);
                });
            }
        }
    }
    
    /**
     * Handle tab change from terminal manager
     * @param {string} port - Port of the new active tab
     */
    handleTabChange(port) {
        this.currentTabPort = port;
        
        // Update tab name in the notes panel
        const activeTab = document.querySelector(`.tab-btn[data-port="${port}"]`);
        if (activeTab) {
            this.updateTabNameDisplay(activeTab.textContent || 'Terminal');
        }
        
        // If tab notes are open, load notes for the new tab
        if (this.tabNotesPanel && this.tabNotesPanel.classList.contains('visible')) {
            // Try to load from server, fall back to localStorage
            this.loadTabNotesFromServer()
                .catch(error => {
                    console.warn('Failed to load tab notes from server, falling back to localStorage:', error);
                    this.loadTabNotes();
                });
        }
    }
    
    /**
     * Load global notes from server
     * @returns {Promise<string>} - Promise resolving to the notes content
     */
    async loadGlobalNotesFromServer() {
        try {
            const response = await fetch(`${this.apiBaseUrl}api/notes/global`);
            
            if (!response.ok) {
                throw new Error(`Failed to load global notes: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.content !== undefined) {
                // Update textarea content
                if (this.globalNotesTextarea) {
                    this.globalNotesTextarea.value = data.content;
                    
                    // Also update in localStorage for offline access
                    localStorage.setItem(this.GLOBAL_NOTES_KEY, data.content);
                }
                
                console.log('Global notes loaded from server');
                return data.content;
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error('Error loading global notes from server:', error);
            throw error;
        }
    }
    
    /**
     * Save global notes to server
     * @returns {Promise<boolean>} - Promise resolving to whether the save was successful
     */
    async saveGlobalNotesToServer() {
        if (!this.globalNotesTextarea) return false;
        
        try {
            const content = this.globalNotesTextarea.value;
            
            const response = await fetch(`${this.apiBaseUrl}api/notes/global`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save global notes: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                console.log('Global notes saved to server');
                
                // Also update in localStorage for offline access
                localStorage.setItem(this.GLOBAL_NOTES_KEY, content);
                
                return true;
            } else {
                throw new Error(data.message || 'Failed to save global notes');
            }
        } catch (error) {
            console.error('Error saving global notes to server:', error);
            
            // Fall back to localStorage
            this.saveGlobalNotes();
            
            return false;
        }
    }
    
    /**
     * Load tab notes from server
     * @returns {Promise<string>} - Promise resolving to the notes content
     */
    async loadTabNotesFromServer() {
        if (!this.currentTabName) return "";
        
        try {
            const response = await fetch(
                `${this.apiBaseUrl}api/notes/terminal/${encodeURIComponent(this.currentTabName)}`
            );
            
            if (!response.ok) {
                throw new Error(`Failed to load tab notes: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success && data.content !== undefined) {
                // Update textarea content
                if (this.tabNotesTextarea) {
                    this.tabNotesTextarea.value = data.content;
                    
                    // Also update in localStorage for offline access
                    const key = this.TAB_NOTES_PREFIX + this.sanitizeName(this.currentTabName);
                    localStorage.setItem(key, data.content);
                }
                
                console.log(`Tab notes loaded from server for terminal ${this.currentTabName}`);
                return data.content;
            } else {
                throw new Error('Invalid response from server');
            }
        } catch (error) {
            console.error(`Error loading tab notes from server for terminal ${this.currentTabName}:`, error);
            throw error;
        }
    }
    
    /**
     * Save tab notes to server
     * @returns {Promise<boolean>} - Promise resolving to whether the save was successful
     */
    async saveTabNotesToServer() {
        if (!this.tabNotesTextarea || !this.currentTabName) return false;
        
        try {
            const content = this.tabNotesTextarea.value;
            
            const response = await fetch(
                `${this.apiBaseUrl}api/notes/terminal/${encodeURIComponent(this.currentTabName)}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    content
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to save tab notes: ${response.status} ${response.statusText}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`Tab notes saved to server for terminal ${this.currentTabName}`);
                
                // Also update in localStorage for offline access
                const key = this.TAB_NOTES_PREFIX + this.sanitizeName(this.currentTabName);
                localStorage.setItem(key, content);
                
                return true;
            } else {
                throw new Error(data.message || 'Failed to save tab notes');
            }
        } catch (error) {
            console.error(`Error saving tab notes to server for terminal ${this.currentTabName}:`, error);
            
            // Fall back to localStorage
            this.saveTabNotes();
            
            return false;
        }
    }
    
    /**
     * Load global notes from localStorage
     */
    loadGlobalNotes() {
        if (this.globalNotesTextarea) {
            const notes = localStorage.getItem(this.GLOBAL_NOTES_KEY) || '';
            this.globalNotesTextarea.value = notes;
        }
    }
    
    /**
     * Save global notes to localStorage
     */
    saveGlobalNotes() {
        if (this.globalNotesTextarea) {
            localStorage.setItem(this.GLOBAL_NOTES_KEY, this.globalNotesTextarea.value);
            console.log('Global notes saved to localStorage');
        }
    }
    
    /**
     * Load tab-specific notes from localStorage
     */
    loadTabNotes() {
        if (this.tabNotesTextarea && this.currentTabName) {
            const key = this.TAB_NOTES_PREFIX + this.sanitizeName(this.currentTabName);
            const notes = localStorage.getItem(key) || '';
            this.tabNotesTextarea.value = notes;
        }
    }
    
    /**
     * Save tab-specific notes to localStorage
     */
    saveTabNotes() {
        if (this.tabNotesTextarea && this.currentTabName) {
            const key = this.TAB_NOTES_PREFIX + this.sanitizeName(this.currentTabName);
            localStorage.setItem(key, this.tabNotesTextarea.value);
            console.log(`Notes saved to localStorage for tab ${this.currentTabName}`);
        }
    }
    
    /**
     * Update global notes UI with content from remote
     * @param {string} content - Remote notes content
     */
    updateGlobalNotesUI(content) {
        if (!this.globalNotesTextarea) return;
        
        // Set flag to prevent triggering sync while updating from remote
        this.updatingFromRemote = true;
        
        try {
            // Update textarea content
            this.globalNotesTextarea.value = content;
            
            // Save to localStorage
            localStorage.setItem(this.GLOBAL_NOTES_KEY, content);
            
            // Add visual indicator for updated content
            this.globalNotesPanel.classList.add('content-updated');
            setTimeout(() => {
                this.globalNotesPanel.classList.remove('content-updated');
            }, 1500);
            
            console.log('Global notes updated from remote');
        } catch (error) {
            console.error('Error updating global notes UI:', error);
        } finally {
            // Clear the flag
            this.updatingFromRemote = false;
        }
    }

    /**
     * Update tab notes UI with content from remote
     * @param {string} terminalId - Terminal ID
     * @param {string} content - Remote notes content
     */
    updateTabNotesUI(terminalId, content) {
        if (!this.tabNotesTextarea) return;
        
        // Only update if it's for the current tab
        if (this.currentTabName !== terminalId) {
            console.log(`Ignoring remote tab notes update for inactive tab ${terminalId}`);
            return;
        }
        
        // Set flag to prevent triggering sync while updating from remote
        this.updatingFromRemote = true;
        
        try {
            // Update textarea content
            this.tabNotesTextarea.value = content;
            
            // Save to localStorage
            const key = this.TAB_NOTES_PREFIX + this.sanitizeName(this.currentTabName);
            localStorage.setItem(key, content);
            
            // Add visual indicator for updated content
            this.tabNotesPanel.classList.add('content-updated');
            setTimeout(() => {
                this.tabNotesPanel.classList.remove('content-updated');
            }, 1500);
            
            console.log(`Tab notes updated from remote for terminal ${terminalId}`);
        } catch (error) {
            console.error('Error updating tab notes UI:', error);
        } finally {
            // Clear the flag
            this.updatingFromRemote = false;
        }
    }
}
