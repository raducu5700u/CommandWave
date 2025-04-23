// settings_modal.js
// Handles opening, closing, and saving settings in the modal

document.addEventListener('DOMContentLoaded', function () {
    const openBtn = document.getElementById('settingsBtn');
    const modal = document.getElementById('settingsModal');
    const closeBtn = document.getElementById('closeSettingsModalBtn');
    const cancelBtn = document.getElementById('cancelSettingsBtn');
    const saveBtn = document.getElementById('saveSettingsBtn');
    const resetBtn = document.getElementById('resetSettingsBtn');
    const searchInput = document.getElementById('settingsSearch');
    const prevBtn = document.getElementById('prevSettingsBtn');
    const nextBtn = document.getElementById('nextSettingsBtn');

    // Open modal
    if (openBtn && modal) {
        openBtn.addEventListener('click', function () {
            modal.classList.add('show');
            // Initially focus on search field for keyboard navigation
            if (searchInput) {
                setTimeout(() => {
                    searchInput.focus();
                }, 100);
            }
        });
    }
    
    // Close modal
    [closeBtn, cancelBtn].forEach(btn => {
        if (btn && modal) {
            btn.addEventListener('click', function () {
                modal.classList.remove('show');
                // Revert any unsaved theme changes
                const savedTheme = localStorage.getItem('commandwave-theme') || 'dark';
                document.body.setAttribute('data-theme', savedTheme);
            });
        }
    });
    
    // Save settings
    if (saveBtn && modal) {
        saveBtn.addEventListener('click', function (e) {
            e.preventDefault();
            saveSettings();
            modal.classList.remove('show');
            
            // Show feedback toast
            showToast('Settings saved successfully!', 'success');
        });
    }
    
    // Reset settings to defaults
    if (resetBtn) {
        resetBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            if (confirm('Are you sure you want to reset all settings to defaults?')) {
                resetSettingsToDefaults();
                
                // Show feedback toast
                showToast('Settings reset to defaults', 'info');
            }
        });
    }
    
    // Close modal on outside click
    window.addEventListener('click', function (event) {
        if (event.target === modal) {
            modal.classList.remove('show');
            // Revert any unsaved theme changes
            const savedTheme = localStorage.getItem('commandwave-theme') || 'dark';
            document.body.setAttribute('data-theme', savedTheme);
        }
    });
    
    // Escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('show')) {
            modal.classList.remove('show');
            // Revert any unsaved theme changes
            const savedTheme = localStorage.getItem('commandwave-theme') || 'dark';
            document.body.setAttribute('data-theme', savedTheme);
        }
    });

    // Category navigation
    initCategoryNavigation();
    
    // Initialize all settings panels
    initializeThemeSettings();
    initializeNoteSizeSettings();
    initializeGeneralSettings();
    initializeEditorSettings();
    
    // Initialize navigation buttons
    initNavigationButtons();
    
    // Initialize settings search
    initSettingsSearch();
    
    // Initialize custom number inputs
    initNumberInputs();
});

// Initialize category navigation
function initCategoryNavigation() {
    const categoryItems = document.querySelectorAll('.category-item');
    const settingsPanels = document.querySelectorAll('.settings-panel');
    
    if (categoryItems.length > 0) {
        categoryItems.forEach(item => {
            // Click handler
            item.addEventListener('click', function() {
                handleCategoryChange(this);
            });
            
            // Keyboard handler
            item.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleCategoryChange(this);
                }
            });
        });
    }
    
    // Function to handle category change
    function handleCategoryChange(selectedItem) {
        // Remove active class from all items
        categoryItems.forEach(catItem => {
            catItem.classList.remove('active');
            catItem.setAttribute('aria-selected', 'false');
        });
        
        // Add active class to clicked item
        selectedItem.classList.add('active');
        selectedItem.setAttribute('aria-selected', 'true');
        
        // Hide all panels
        settingsPanels.forEach(panel => panel.classList.remove('active'));
        
        // Show the corresponding panel
        const targetCategory = selectedItem.dataset.category;
        const targetPanel = document.querySelector(`.settings-panel[data-panel="${targetCategory}"]`);
        if (targetPanel) {
            targetPanel.classList.add('active');
            
            // Update navigation buttons state
            updateNavigationButtons();
        }
    }
}

// Navigation buttons
function initNavigationButtons() {
    const prevBtn = document.getElementById('prevSettingsBtn');
    const nextBtn = document.getElementById('nextSettingsBtn');
    
    if (prevBtn && nextBtn) {
        prevBtn.addEventListener('click', function() {
            navigateCategories('prev');
        });
        
        nextBtn.addEventListener('click', function() {
            navigateCategories('next');
        });
        
        // Initial state
        updateNavigationButtons();
    }
}

function navigateCategories(direction) {
    const categories = Array.from(document.querySelectorAll('.category-item'));
    const activeIndex = categories.findIndex(cat => cat.classList.contains('active'));
    
    if (activeIndex === -1) return;
    
    let newIndex;
    if (direction === 'prev') {
        newIndex = activeIndex - 1;
        if (newIndex < 0) newIndex = categories.length - 1;
    } else {
        newIndex = activeIndex + 1;
        if (newIndex >= categories.length) newIndex = 0;
    }
    
    // Simulate click on the new category
    categories[newIndex].click();
    categories[newIndex].focus();
}

function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevSettingsBtn');
    const nextBtn = document.getElementById('nextSettingsBtn');
    const categories = document.querySelectorAll('.category-item');
    
    if (!prevBtn || !nextBtn || categories.length <= 1) return;
    
    // Always enable both buttons for circular navigation
    prevBtn.disabled = false;
    nextBtn.disabled = false;
}

// Settings search functionality
function initSettingsSearch() {
    const searchInput = document.getElementById('settingsSearch');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase().trim();
            searchSettings(searchTerm);
        });
        
        // Clear search on Escape key
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                searchSettings('');
                // Don't propagate to avoid closing the modal
                e.stopPropagation();
            }
        });
    }
}

function searchSettings(term) {
    if (term === '') {
        // Reset all categories and options visibility
        document.querySelectorAll('.category-item').forEach(item => {
            item.style.display = '';
        });
        
        document.querySelectorAll('.settings-option').forEach(option => {
            option.style.display = '';
        });
        
        return;
    }
    
    // Search in category names
    document.querySelectorAll('.category-item').forEach(item => {
        const categoryName = item.querySelector('span').textContent.toLowerCase();
        if (categoryName.includes(term)) {
            item.style.display = '';
            // If a category matches, show its panel
            const categoryId = item.dataset.category;
            document.querySelector(`.category-item[data-category="${categoryId}"]`).click();
        } else {
            // Don't hide categories completely to maintain navigation
            // item.style.display = 'none';
        }
    });
    
    // Search in settings options
    document.querySelectorAll('.settings-option').forEach(option => {
        const label = option.querySelector('label')?.textContent.toLowerCase() || '';
        const tooltip = option.querySelector('.tooltip')?.getAttribute('data-tooltip')?.toLowerCase() || '';
        
        if (label.includes(term) || tooltip.includes(term)) {
            option.style.display = '';
            // Highlight matching option
            option.classList.add('search-highlight');
            
            // Make sure the panel containing this option is visible
            const panel = option.closest('.settings-panel');
            if (panel) {
                const panelId = panel.dataset.panel;
                document.querySelector(`.category-item[data-category="${panelId}"]`).click();
            }
        } else {
            option.classList.remove('search-highlight');
        }
    });
}

// Custom number input handlers
function initNumberInputs() {
    document.querySelectorAll('.number-input-wrapper').forEach(wrapper => {
        const input = wrapper.querySelector('input[type="number"]');
        const upBtn = wrapper.querySelector('.number-up');
        const downBtn = wrapper.querySelector('.number-down');
        
        if (input && upBtn && downBtn) {
            // Up button
            upBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value, 10) || 0;
                const max = parseInt(input.getAttribute('max'), 10) || Infinity;
                input.value = Math.min(currentValue + 1, max);
                input.dispatchEvent(new Event('change'));
                input.focus();
            });
            
            // Down button
            downBtn.addEventListener('click', function() {
                const currentValue = parseInt(input.value, 10) || 0;
                const min = parseInt(input.getAttribute('min'), 10) || 0;
                input.value = Math.max(currentValue - 1, min);
                input.dispatchEvent(new Event('change'));
                input.focus();
            });
            
            // Validate number input on change
            input.addEventListener('change', function() {
                const min = parseInt(this.getAttribute('min'), 10) || 0;
                const max = parseInt(this.getAttribute('max'), 10) || Infinity;
                const value = parseInt(this.value, 10) || min;
                
                // Ensure value is within range
                if (value < min) this.value = min;
                if (value > max) this.value = max;
            });
        }
    });
}

// Initialize theme settings
function initializeThemeSettings() {
    const themePicker = document.getElementById('themePicker');
    if (themePicker) {
        // Set initial selection based on current theme
        const savedTheme = localStorage.getItem('commandwave-theme') || 'dark';
        const currentTheme = document.body.getAttribute('data-theme') || savedTheme;
        const options = themePicker.querySelectorAll('.theme-card');
        
        // Mark initially selected theme
        options.forEach(card => {
            if (card.dataset.theme === currentTheme) {
                card.classList.add('selected');
                // Show preview indicator
                card.querySelector('.preview-active-indicator').style.opacity = '1';
            }
            
            // Add click handlers
            card.addEventListener('click', function (e) {
                e.preventDefault();
                
                // Update selected state
                options.forEach(opt => {
                    opt.classList.remove('selected');
                    opt.querySelector('.preview-active-indicator').style.opacity = '';
                });
                
                card.classList.add('selected');
                card.querySelector('.preview-active-indicator').style.opacity = '1';
                
                // Preview theme instantly:
                document.body.setAttribute('data-theme', card.dataset.theme);
            });
        });
    }
}

// Initialize Note Size Settings
function initializeNoteSizeSettings() {
    const noteSizeSelector = document.querySelector('.note-size-selector');
    if (noteSizeSelector) {
        // Get currently saved note size or use default
        const currentSize = localStorage.getItem('commandwave-note-size') || 'medium';
        
        // Mark initially selected size
        const sizeOptions = noteSizeSelector.querySelectorAll('.note-size-option');
        sizeOptions.forEach(option => {
            if (option.dataset.size === currentSize) {
                option.classList.add('selected');
            }
            
            // Add click handlers
            option.addEventListener('click', function(e) {
                e.preventDefault();
                const newSize = this.dataset.size;
                
                // Update selected state
                sizeOptions.forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                
                // Save preference
                localStorage.setItem('commandwave-note-size', newSize);
                
                // Apply size to all note panels
                document.documentElement.setAttribute('data-note-size', newSize);
                
                // Dispatch event for NotesManager to handle
                document.dispatchEvent(new CustomEvent('note-size-changed', { 
                    detail: { size: newSize } 
                }));
            });
            
            // Keyboard navigation
            option.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    this.click();
                }
            });
        });
        
        // Initial application of size
        document.documentElement.setAttribute('data-note-size', currentSize);
    }
}

// Initialize default values for general settings
function initializeGeneralSettings() {
    // Collapse Variables by Default setting
    const collapseVariablesToggle = document.getElementById('collapseVariables');
    if (collapseVariablesToggle) {
        // Get saved preference or set default
        const collapseByDefault = localStorage.getItem('commandwave-collapse-variables') === 'true';
        collapseVariablesToggle.checked = collapseByDefault;
        
        // Update on change
        collapseVariablesToggle.addEventListener('change', function() {
            localStorage.setItem('commandwave-collapse-variables', this.checked);
        });
    }
    
    // Startup behavior
    const startupBehavior = document.getElementById('startupBehavior');
    if (startupBehavior) {
        const savedBehavior = localStorage.getItem('commandwave-startup-behavior') || 'last';
        startupBehavior.value = savedBehavior;
        
        // Update on change
        startupBehavior.addEventListener('change', function() {
            localStorage.setItem('commandwave-startup-behavior', this.value);
        });
    }
    
    // Autosave interval
    const autosaveInterval = document.getElementById('autosaveInterval');
    if (autosaveInterval) {
        const savedInterval = localStorage.getItem('commandwave-autosave-interval') || '60';
        autosaveInterval.value = savedInterval;
        
        // Update on change and validate
        autosaveInterval.addEventListener('change', function() {
            let value = parseInt(this.value, 10);
            if (isNaN(value) || value < 10) value = 10;
            if (value > 300) value = 300;
            
            this.value = value;
            localStorage.setItem('commandwave-autosave-interval', value);
        });
    }
}

// Initialize default values for editor settings
function initializeEditorSettings() {
    // Editor font size
    const editorFontSize = document.getElementById('editorFontSize');
    if (editorFontSize) {
        const savedFontSize = localStorage.getItem('commandwave-editor-font-size') || '14';
        editorFontSize.value = savedFontSize;
        
        // Update on change
        editorFontSize.addEventListener('change', function() {
            let value = parseInt(this.value, 10);
            if (isNaN(value) || value < 10) value = 10;
            if (value > 24) value = 24;
            
            this.value = value;
            localStorage.setItem('commandwave-editor-font-size', value);
            document.documentElement.style.setProperty('--editor-font-size', `${value}px`);
        });
    }
    
    // Word wrap
    const editorWordWrap = document.getElementById('editorWordWrap');
    if (editorWordWrap) {
        const wordWrapEnabled = localStorage.getItem('commandwave-editor-word-wrap') !== 'false'; // Default to true
        editorWordWrap.checked = wordWrapEnabled;
        
        // Update on change
        editorWordWrap.addEventListener('change', function() {
            localStorage.setItem('commandwave-editor-word-wrap', this.checked);
        });
    }
    
    // Line numbers
    const editorLineNumbers = document.getElementById('editorLineNumbers');
    if (editorLineNumbers) {
        const lineNumbersEnabled = localStorage.getItem('commandwave-editor-line-numbers') !== 'false'; // Default to true
        editorLineNumbers.checked = lineNumbersEnabled;
        
        // Update on change
        editorLineNumbers.addEventListener('change', function() {
            localStorage.setItem('commandwave-editor-line-numbers', this.checked);
        });
    }
    
    // Auto-indent
    const editorAutoIndent = document.getElementById('editorAutoIndent');
    if (editorAutoIndent) {
        const autoIndentEnabled = localStorage.getItem('commandwave-editor-auto-indent') !== 'false'; // Default to true
        editorAutoIndent.checked = autoIndentEnabled;
        
        // Update on change
        editorAutoIndent.addEventListener('change', function() {
            localStorage.setItem('commandwave-editor-auto-indent', this.checked);
        });
    }
}

// Save all settings
function saveSettings() {
    // Theme
    const selectedThemeCard = document.querySelector('.theme-card.selected');
    if (selectedThemeCard) {
        const theme = selectedThemeCard.dataset.theme;
        localStorage.setItem('commandwave-theme', theme);
    }
    
    // Note size - already saved on click
    
    // General settings
    const startupBehavior = document.getElementById('startupBehavior');
    if (startupBehavior) {
        localStorage.setItem('commandwave-startup-behavior', startupBehavior.value);
    }
    
    const autosaveInterval = document.getElementById('autosaveInterval');
    if (autosaveInterval) {
        localStorage.setItem('commandwave-autosave-interval', autosaveInterval.value);
    }
    
    const collapseVariables = document.getElementById('collapseVariables');
    if (collapseVariables) {
        localStorage.setItem('commandwave-collapse-variables', collapseVariables.checked);
    }
    
    // Editor settings
    const editorFontSize = document.getElementById('editorFontSize');
    if (editorFontSize) {
        localStorage.setItem('commandwave-editor-font-size', editorFontSize.value);
        document.documentElement.style.setProperty('--editor-font-size', `${editorFontSize.value}px`);
    }
    
    const editorWordWrap = document.getElementById('editorWordWrap');
    if (editorWordWrap) {
        localStorage.setItem('commandwave-editor-word-wrap', editorWordWrap.checked);
    }
    
    const editorLineNumbers = document.getElementById('editorLineNumbers');
    if (editorLineNumbers) {
        localStorage.setItem('commandwave-editor-line-numbers', editorLineNumbers.checked);
    }
    
    const editorAutoIndent = document.getElementById('editorAutoIndent');
    if (editorAutoIndent) {
        localStorage.setItem('commandwave-editor-auto-indent', editorAutoIndent.checked);
    }
    
    // Dispatch event to notify rest of app about settings change
    document.dispatchEvent(new CustomEvent('settings-saved'));
}

// Reset all settings to defaults
function resetSettingsToDefaults() {
    // Define default settings
    const defaults = {
        theme: 'dark',
        noteSize: 'medium',
        startupBehavior: 'last',
        autosaveInterval: '60',
        collapseVariables: false,
        editorFontSize: '14',
        editorWordWrap: true,
        editorLineNumbers: true,
        editorAutoIndent: true
    };
    
    // Apply defaults
    document.body.setAttribute('data-theme', defaults.theme);
    document.documentElement.setAttribute('data-note-size', defaults.noteSize);
    document.documentElement.style.setProperty('--editor-font-size', `${defaults.editorFontSize}px`);
    
    // Update form controls
    const themePicker = document.getElementById('themePicker');
    if (themePicker) {
        const options = themePicker.querySelectorAll('.theme-card');
        options.forEach(card => {
            card.classList.remove('selected');
            card.querySelector('.preview-active-indicator').style.opacity = '';
            if (card.dataset.theme === defaults.theme) {
                card.classList.add('selected');
                card.querySelector('.preview-active-indicator').style.opacity = '1';
            }
        });
    }
    
    const noteSizeSelector = document.querySelector('.note-size-selector');
    if (noteSizeSelector) {
        const options = noteSizeSelector.querySelectorAll('.note-size-option');
        options.forEach(option => {
            option.classList.remove('selected');
            if (option.dataset.size === defaults.noteSize) {
                option.classList.add('selected');
            }
        });
    }
    
    const startupBehavior = document.getElementById('startupBehavior');
    if (startupBehavior) startupBehavior.value = defaults.startupBehavior;
    
    const autosaveInterval = document.getElementById('autosaveInterval');
    if (autosaveInterval) autosaveInterval.value = defaults.autosaveInterval;
    
    const collapseVariables = document.getElementById('collapseVariables');
    if (collapseVariables) collapseVariables.checked = defaults.collapseVariables;
    
    const editorFontSize = document.getElementById('editorFontSize');
    if (editorFontSize) editorFontSize.value = defaults.editorFontSize;
    
    const editorWordWrap = document.getElementById('editorWordWrap');
    if (editorWordWrap) editorWordWrap.checked = defaults.editorWordWrap;
    
    const editorLineNumbers = document.getElementById('editorLineNumbers');
    if (editorLineNumbers) editorLineNumbers.checked = defaults.editorLineNumbers;
    
    const editorAutoIndent = document.getElementById('editorAutoIndent');
    if (editorAutoIndent) editorAutoIndent.checked = defaults.editorAutoIndent;
    
    // Clear localStorage settings
    localStorage.removeItem('commandwave-theme');
    localStorage.removeItem('commandwave-note-size');
    localStorage.removeItem('commandwave-startup-behavior');
    localStorage.removeItem('commandwave-autosave-interval');
    localStorage.removeItem('commandwave-collapse-variables');
    localStorage.removeItem('commandwave-editor-font-size');
    localStorage.removeItem('commandwave-editor-word-wrap');
    localStorage.removeItem('commandwave-editor-line-numbers');
    localStorage.removeItem('commandwave-editor-auto-indent');
}

// Toast notification system
function showToast(message, type = 'info') {
    // Remove any existing toasts
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());
    
    // Create a new toast
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    
    // Create toast content
    const icon = document.createElement('i');
    if (type === 'success') {
        icon.className = 'fas fa-check-circle';
    } else if (type === 'error') {
        icon.className = 'fas fa-exclamation-circle';
    } else {
        icon.className = 'fas fa-info-circle';
    }
    
    const messageSpan = document.createElement('span');
    messageSpan.textContent = message;
    
    toast.appendChild(icon);
    toast.appendChild(messageSpan);
    
    // Add to body
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Automatically remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}
