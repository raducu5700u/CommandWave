/**
 * CommandWave - Main JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Custom error handler to suppress non-critical errors
    window.addEventListener('error', function(event) {
        // Check if it's a WebGL or non-critical error
        if (event.message && (
            event.message.includes('WebGL') || 
            event.message.includes('ReadPixels') || 
            event.message.includes('swiftshader')
        )) {
            // Prevent the error from appearing in console
            event.preventDefault();
            return true;
        }
    }, true);
    
    // Override console methods to filter out non-critical messages
    const originalConsoleError = console.error;
    console.error = function() {
        // Filter WebGL and ttyd related non-critical errors
        if (arguments.length > 0 && 
            typeof arguments[0] === 'string' && (
                arguments[0].includes('WebGL') || 
                arguments[0].includes('ReadPixels') ||
                arguments[0].includes('Failed to load resource: favicon')
            )) {
            return;
        }
        originalConsoleError.apply(console, arguments);
    };

    // Global state
    const state = {
        terminals: {
            // Example: 'terminal-7681': { port: 7681, name: 'Main', variables: {}, playbooks: {} }
        },
        activeTerminal: null,
        globalPlaybooks: {
            // Example: 'playbook1.md': { content: '', blocks: [] }
        }
    };

    // Initialize state with the default terminal
    const defaultTerminalElement = document.querySelector('.terminal-iframe');
    if (defaultTerminalElement) {
        const defaultPort = defaultTerminalElement.dataset.port;
        state.terminals[`terminal-${defaultPort}`] = {
            port: defaultPort,
            name: 'Main',
            variables: {},
            playbooks: {}
        };
        state.activeTerminal = `terminal-${defaultPort}`;

        // Initialize variables for the default terminal
        initializeVariables(state.activeTerminal);
        
        // Migrate any existing global playbooks to the default terminal for backward compatibility
        setTimeout(() => {
            migrateGlobalPlaybooks();
        }, 100);
    }

    // Load initial notes
    loadGlobalNotes();
    loadTabNotes(state.activeTerminal);

    // Terminal Tab Management
    const addTabBtn = document.getElementById('addTabBtn');
    if (addTabBtn) {
        addTabBtn.addEventListener('click', function(event) {
            event.preventDefault();
            openNewTerminalModal();
        });
    }

    // Setup tab switching
    setupTabSwitching();

    // Variable Input handling
    setupVariableInputs();

    // Playbook upload
    const uploadPlaybookInput = document.getElementById('uploadPlaybook');
    if (uploadPlaybookInput) {
        uploadPlaybookInput.addEventListener('change', handlePlaybookUpload);
    }

    // Playbook search
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handlePlaybookSearch, 500));
    }
    
    // Clear search button functionality
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    if (clearSearchBtn) {
        clearSearchBtn.addEventListener('click', function() {
            const searchInput = document.getElementById('searchInput');
            if (searchInput) {
                searchInput.value = '';
                const resultsContainer = document.getElementById('searchResults');
                if (resultsContainer) {
                    resultsContainer.style.display = 'none';
                }
            }
        });
    }

    // Notes panel toggles
    setupNotesPanel();

    // Setup custom variable functionality
    setupCustomVariables();

    // Setup create playbook functionality
    setupCreatePlaybook();

    /**
     * Terminal Management Functions
     */
    
    function openNewTerminalModal() {
        // Get modal elements
        const modal = document.getElementById('newTerminalModal');
        const closeBtn = modal.querySelector('.close-modal-btn');
        const cancelBtn = document.getElementById('cancelTerminalBtn');
        const submitBtn = document.getElementById('createTerminalSubmitBtn');
        const nameInput = document.getElementById('newTerminalName');
        
        // Show modal
        modal.style.display = 'block';
        nameInput.focus();
        
        // Clear any existing event listeners
        submitBtn.replaceWith(submitBtn.cloneNode(true));
        const newSubmitBtn = document.getElementById('createTerminalSubmitBtn');
        nameInput.replaceWith(nameInput.cloneNode(true));
        const newNameInput = document.getElementById('newTerminalName');
        newNameInput.focus();
        
        // Close modal functions
        function closeModal() {
            modal.style.display = 'none';
            newNameInput.value = '';
            
            // Remove event listeners
            window.removeEventListener('click', windowClickHandler);
        }
        
        // Setup event listeners
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // Close when clicking outside of the modal content
        const windowClickHandler = function(event) {
            if (event.target === modal) {
                closeModal();
            }
        };
        window.addEventListener('click', windowClickHandler);
        
        // Handle form submission
        newSubmitBtn.addEventListener('click', submitHandler);
        
        function submitHandler() {
            const name = newNameInput.value.trim();
            
            if (!name) {
                alert('Please enter a name for the terminal');
                return;
            }
            
            // Create the terminal
            createTerminalWithName(name);
            
            // Close modal
            closeModal();
        }
        
        // Handle Enter key press
        newNameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitHandler();
            }
        });
    }
    
    function createTerminalWithName(tabName) {
        if (!tabName) return;
        
        // Immediately store name to prevent browser prompt
        localStorage.setItem('new_terminal_name', tabName);

        fetch('/api/terminals/new')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const newPort = data.port;
                    
                    // Create new tab button
                    const tabsContainer = document.querySelector('.terminal-tabs');
                    const newTab = document.createElement('button');
                    newTab.className = 'tab-btn';
                    newTab.dataset.port = newPort;
                    
                    // Separate span for content and close button
                    const tabContent = document.createElement('span');
                    tabContent.className = 'tab-btn-content';
                    tabContent.textContent = tabName;
                    newTab.appendChild(tabContent);
                    
                    // Add close button
                    const closeBtn = document.createElement('span');
                    closeBtn.className = 'tab-close';
                    closeBtn.innerHTML = '&times;';
                    closeBtn.addEventListener('click', function(e) {
                        e.stopPropagation();
                        closeTerminal(newPort);
                    });
                    
                    newTab.appendChild(closeBtn);
                    
                    // Add double-click for rename
                    newTab.addEventListener('dblclick', function(e) {
                        if (e.target === this) {
                            // Open a rename modal instead of using browser prompt
                            openRenameModal(this, newPort, tabName);
                        }
                    });
                    
                    // Add tab button before the add-tab button
                    const addTabBtn = document.querySelector('.add-tab');
                    tabsContainer.insertBefore(newTab, addTabBtn);
                    
                    // Create iframe
                    const terminalsContainer = document.querySelector('.terminal-container');
                    const iframe = document.createElement('iframe');
                    iframe.id = `terminal-${newPort}`;
                    iframe.className = 'terminal-iframe';
                    iframe.src = `http://localhost:${newPort}`;
                    iframe.dataset.port = newPort;
                    
                    terminalsContainer.appendChild(iframe);
                    
                    // Update state
                    state.terminals[`terminal-${newPort}`] = {
                        port: newPort,
                        name: tabName,
                        variables: {},
                        playbooks: {}
                    };
                    
                    // Activate the new tab
                    activateTab(newTab);
                    
                    // Initialize variables for the new terminal
                    initializeVariables(`terminal-${newPort}`);
                }
            })
            .catch(error => {
                console.error('Error creating new terminal:', error);
                alert('Failed to create new terminal');
            });
    }
    
    function openRenameModal(tabElement, port, currentName) {
        // Get the rename terminal modal
        const modal = document.getElementById('renameTerminalModal') || createRenameModal();
        const nameInput = document.getElementById('renameTerminalName');
        const submitBtn = document.getElementById('renameTerminalSubmitBtn');
        const cancelBtn = document.getElementById('cancelRenameBtn');
        const closeBtn = modal.querySelector('.close-modal-btn');
        
        // Set current name
        nameInput.value = currentName;
        
        // Show modal
        modal.style.display = 'block';
        nameInput.focus();
        nameInput.select();
        
        // Close modal function
        function closeModal() {
            modal.style.display = 'none';
            window.removeEventListener('click', windowClickHandler);
        }
        
        // Setup event listeners
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // Close when clicking outside
        const windowClickHandler = function(event) {
            if (event.target === modal) {
                closeModal();
            }
        };
        window.addEventListener('click', windowClickHandler);
        
        // Handle rename
        function handleRename() {
            const newName = nameInput.value.trim();
            if (newName && newName !== currentName) {
                tabElement.querySelector('.tab-btn-content').textContent = newName;
                state.terminals[`terminal-${port}`].name = newName;
                if (state.activeTerminal === `terminal-${port}`) {
                    const tabNameEl = document.getElementById('currentTabName');
                    if (tabNameEl) tabNameEl.textContent = newName;
                }
            }
            closeModal();
        }
        
        // Set up submit handler
        submitBtn.onclick = handleRename;
        
        // Handle Enter key
        nameInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                handleRename();
            }
        });
    }
    
    function createRenameModal() {
        // Create modal element if it doesn't exist
        const modal = document.createElement('div');
        modal.id = 'renameTerminalModal';
        modal.className = 'modal';
        
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Rename Terminal</h3>
                    <button class="close-modal-btn">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="renameTerminalName">Terminal Name:</label>
                        <input type="text" id="renameTerminalName" class="modal-input">
                    </div>
                </div>
                <div class="modal-footer">
                    <button id="cancelRenameBtn" class="modal-btn cancel">Cancel</button>
                    <button id="renameTerminalSubmitBtn" class="modal-btn submit">Rename</button>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        return modal;
    }

    function closeTerminal(port) {
        if (confirm(`Close terminal ${port}?`)) {
            fetch(`/api/terminals/${port}`, {
                method: 'DELETE'
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Remove tab and iframe
                    const tab = document.querySelector(`.tab-btn[data-port="${port}"]`);
                    const iframe = document.getElementById(`terminal-${port}`);
                    
                    if (tab && iframe) {
                        // If active tab is being closed, activate the main tab
                        if (tab.classList.contains('active')) {
                            const mainTab = document.querySelector('.tab-btn[data-port]:not([data-port="' + port + '"])');
                            if (mainTab) {
                                activateTab(mainTab);
                            }
                        }
                        
                        tab.remove();
                        iframe.remove();
                        
                        // Remove from state
                        delete state.terminals[`terminal-${port}`];
                    }
                }
            })
            .catch(error => {
                console.error('Error closing terminal:', error);
                alert('Failed to close terminal');
            });
        }
    }

    function setupTabSwitching() {
        document.querySelector('.terminal-tabs').addEventListener('click', function(e) {
            const clickedTab = e.target.closest('.tab-btn');
            if (clickedTab && !clickedTab.classList.contains('add-tab')) {
                activateTab(clickedTab);
            }
        });
    }

    function activateTab(tabElement) {
        // Deactivate all tabs and iframes
        document.querySelectorAll('.tab-btn').forEach(tab => {
            tab.classList.remove('active');
        });
        document.querySelectorAll('.terminal-iframe').forEach(iframe => {
            iframe.classList.remove('active');
        });
        
        // Activate selected tab and iframe
        tabElement.classList.add('active');
        const port = tabElement.dataset.port;
        const iframe = document.getElementById(`terminal-${port}`);
        if (iframe) {
            iframe.classList.add('active');
            state.activeTerminal = iframe.id;
            
            // Update tab notes title and content
            const tabName = state.terminals[state.activeTerminal].name;
            const tabNameElement = document.getElementById('currentTabName');
            tabNameElement.textContent = tabName;
            tabNameElement.className = 'tab-name neon-pink';
            loadTabNotes(state.activeTerminal);
            
            // Refresh variable values
            updateVariableInputsFromState();
            
            // Display playbooks for the active terminal
            displayTerminalPlaybooks(state.activeTerminal);
        }
    }

    /**
     * Variable Management Functions
     */
    
    function initializeVariables(terminalId) {
        if (!state.terminals[terminalId].variables) {
            state.terminals[terminalId].variables = {};
        }
        
        // Initialize with empty values for all variable inputs
        document.querySelectorAll('.variable-input input').forEach(input => {
            const varName = input.id;
            state.terminals[terminalId].variables[varName] = '';
        });
    }

    function setupVariableInputs() {
        // Variable input handler
        document.getElementById('addVariableInput').addEventListener('click', function() {
            openNewVariableModal();
        });
        
        // Initial variables setup
        initializeVariables('terminal-' + document.querySelector('.tab-btn.active').dataset.port);
        
        document.querySelectorAll('.variable-input input').forEach(input => {
            input.addEventListener('input', function() {
                if (state.activeTerminal) {
                    state.terminals[state.activeTerminal].variables[this.name] = this.value;
                    updateVariableSubstitutions();
                }
            });
        });
        
        // Add functionality for remove buttons
        document.querySelectorAll('.variable-input .remove-variable-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const varInput = this.closest('.variable-input');
                if (varInput && state.activeTerminal) {
                    const varName = varInput.querySelector('input').name;
                    delete state.terminals[state.activeTerminal].variables[varName];
                    varInput.remove();
                    updateVariableSubstitutions();
                }
            });
        });
    }

    function updateVariableInputsFromState() {
        if (state.activeTerminal && state.terminals[state.activeTerminal]) {
            const variables = state.terminals[state.activeTerminal].variables;
            
            document.querySelectorAll('.variable-input input').forEach(input => {
                const varName = input.name;
                if (variables[varName] !== undefined) {
                    input.value = variables[varName];
                } else {
                    input.value = '';
                }
            });
        }
    }

    function updateVariableSubstitutions() {
        if (!state.activeTerminal) return;
        
        const variables = state.terminals[state.activeTerminal].variables;
        document.querySelectorAll('.code-container pre code').forEach(codeBlock => {
            // Get the raw code
            let content = codeBlock.dataset.rawCode || codeBlock.textContent;
            
            // Perform variable substitution
            for (const [key, value] of Object.entries(variables)) {
                if (value) {
                    // Convert variable name to match the format in the playbooks
                    // For example, 'targetIP' becomes '$TargetIP'
                    const placeholder = '$' + key.charAt(0).toUpperCase() + key.slice(1);
                    const regex = new RegExp(escapeRegExp(placeholder), 'g');
                    content = content.replace(regex, `<span class="substituted">${value}</span>`);
                }
            }
            
            // Update the HTML with substitutions
            codeBlock.innerHTML = content;
            
            // Re-apply Prism.js highlighting
            Prism.highlightElement(codeBlock);
        });
    }

    function getSubstitutedCode(codeElement) {
        if (!state.activeTerminal) return codeElement.textContent;
        
        const variables = state.terminals[state.activeTerminal].variables;
        let content = codeElement.dataset.rawCode || codeElement.textContent;
        
        // Perform variable substitution
        for (const [key, value] of Object.entries(variables)) {
            if (value) {
                // Convert variable name to match the format in the playbooks
                const placeholder = '$' + key.charAt(0).toUpperCase() + key.slice(1);
                const regex = new RegExp(escapeRegExp(placeholder), 'g');
                content = content.replace(regex, value);
            }
        }
        
        return content;
    }

    function openNewVariableModal() {
        // Get modal elements
        const modal = document.getElementById('newVariableModal');
        const closeBtn = modal.querySelector('.close-modal-btn');
        const cancelBtn = document.getElementById('cancelVariableBtn');
        const submitBtn = document.getElementById('createVariableSubmitBtn');
        const nameInput = document.getElementById('newVariableName');
        const valueInput = document.getElementById('newVariableValue');
        
        // Show modal
        modal.style.display = 'block';
        nameInput.focus();
        
        // Close modal functions
        function closeModal() {
            modal.style.display = 'none';
            nameInput.value = '';
            valueInput.value = '';
        }
        
        // Setup event listeners
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // Close when clicking outside of the modal content
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeModal();
            }
        });
        
        // Handle form submission
        submitBtn.addEventListener('click', function() {
            const name = nameInput.value.trim();
            const value = valueInput.value.trim();
            
            if (!name) {
                alert('Please enter a name for the variable');
                return;
            }
            
            // Create the variable
            addCustomVariable(name, value);
            
            // Close modal
            closeModal();
        });
        
        // Handle Enter key press
        valueInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                submitBtn.click();
            }
        });
    }
    
    function addCustomVariable(name, value = '') {
        if (!state.activeTerminal || !name) return;
        
        // Add to state
        state.terminals[state.activeTerminal].variables[name] = value;
        
        // Create variable input row
        const varContainer = document.querySelector('.variable-inputs');
        
        // Check if variable already exists
        const existingVar = document.getElementById(`var-${name}`);
        if (existingVar) {
            // Update the value
            existingVar.querySelector('input').value = value;
            return;
        }
        
        // Create new variable input
        const varInput = document.createElement('div');
        varInput.className = 'variable-input custom-variable';
        varInput.id = `var-${name}`;
        
        varInput.innerHTML = `
            <label for="var-input-${name}">${name}:</label>
            <input type="text" id="var-input-${name}" name="${name}" placeholder="$${name.charAt(0).toUpperCase() + name.slice(1)}" value="${value || ''}">
            <button class="remove-variable-btn" title="Remove variable">&times;</button>
        `;
        
        // Add event listener to remove button
        varInput.querySelector('.remove-variable-btn').addEventListener('click', function() {
            varInput.remove();
            delete state.terminals[state.activeTerminal].variables[name];
            updateVariableSubstitutions();
        });
        
        // Add event listener to input
        varInput.querySelector('input').addEventListener('input', function() {
            state.terminals[state.activeTerminal].variables[name] = this.value;
            updateVariableSubstitutions();
        });
        
        // Add to container
        varContainer.appendChild(varInput);
        
        // Update any code that might use this variable
        updateVariableSubstitutions();
    }

    /**
     * Playbook Management Functions
     */
    
    function handlePlaybookUpload(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        // Ensure we have an active terminal
        if (!state.activeTerminal || !state.terminals[state.activeTerminal]) {
            console.error('No active terminal for playbook upload');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            const playbook = {
                filename: file.name,
                content: content,
                blocks: parseMarkdown(content)
            };
            
            // Store in active terminal's playbooks
            state.terminals[state.activeTerminal].playbooks[file.name] = playbook;
            
            // Display the playbook
            displayPlaybook(playbook);
            
            // Reset the file input
            event.target.value = '';
        };
        
        reader.readAsText(file);
    }

    function parseMarkdown(content) {
        // Use marked.js to parse the Markdown
        const tokens = marked.lexer(content);
        const blocks = [];
        let currentTextBlock = '';
        
        tokens.forEach(token => {
            if (token.type === 'code') {
                // If we have accumulated text, add it as a block first
                if (currentTextBlock) {
                    blocks.push({
                        type: 'text',
                        content: currentTextBlock
                    });
                    currentTextBlock = '';
                }
                
                // Add the code block
                blocks.push({
                    type: 'code',
                    language: token.lang || '',
                    content: token.text
                });
            } else {
                // For other token types, accumulate them into a text block
                const html = marked.parser([token]);
                currentTextBlock += html;
            }
        });
        
        // Add any remaining text block
        if (currentTextBlock) {
            blocks.push({
                type: 'text',
                content: currentTextBlock
            });
        }
        
        return blocks;
    }

    function displayPlaybook(playbook, terminalId = null) {
        const playbooksContainer = document.getElementById('playbooks');
        if (!playbooksContainer) return;
        
        // Clear the playbooks container first if we're switching tabs
        if (terminalId) {
            playbooksContainer.innerHTML = '';
        }
        
        // Use the active terminal if no specific terminal ID provided
        const targetTerminal = terminalId || state.activeTerminal;
        if (!targetTerminal) return;
        
        // Create a unique ID for the playbook within this terminal context
        const playbookId = `${targetTerminal}-${playbook.filename.replace(/\s+/g, '-').replace(/\./g, '-')}`;
        
        // Check if this playbook is already displayed
        if (document.getElementById(`playbook-${playbookId}`)) {
            return;
        }
        
        // Create playbook container
        const playbookElement = createPlaybookContainer(playbookId, playbook.filename);
        
        // Create content area
        const content = playbookElement.querySelector('.playbook-content');
        
        // Populate with blocks
        playbook.blocks.forEach((block, blockIndex) => {
            if (block.type === 'text') {
                const textBlock = document.createElement('div');
                textBlock.className = 'markdown-block markdown-text';
                textBlock.innerHTML = block.content;
                content.appendChild(textBlock);
            } else if (block.type === 'code') {
                const codeBlock = document.createElement('div');
                codeBlock.className = 'markdown-block code-block';
                codeBlock.innerHTML = `
                    <div class="code-header">
                        <button class="code-action-btn copy" title="Copy to clipboard"><i class="fas fa-copy"></i> Copy</button>
                        <button class="code-action-btn execute" title="Execute in current terminal"><i class="fas fa-play"></i> Execute</button>
                    </div>
                    <div class="code-container" data-block-index="${blockIndex}" data-playbook-id="${playbookId}">
                        <pre><code class="language-${block.language}">${block.content}</code></pre>
                    </div>
                `;
                
                // Store the raw code for variable substitution
                const codeElement = codeBlock.querySelector('code');
                codeElement.dataset.rawCode = block.content;
                
                // Set up copy button
                const copyBtn = codeBlock.querySelector('.copy');
                copyBtn.addEventListener('click', function() {
                    copyToClipboard(getSubstitutedCode(codeElement));
                    this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                    setTimeout(() => {
                        this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    }, 2000);
                });
                
                // Set up execute button
                const executeBtn = codeBlock.querySelector('.execute');
                executeBtn.addEventListener('click', function() {
                    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Executing...';
                    executeCode(getSubstitutedCode(codeElement))
                        .then(() => {
                            this.innerHTML = '<i class="fas fa-check"></i> Done!';
                            setTimeout(() => {
                                this.innerHTML = '<i class="fas fa-play"></i> Execute';
                            }, 2000);
                        })
                        .catch(() => {
                            this.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                            setTimeout(() => {
                                this.innerHTML = '<i class="fas fa-play"></i> Execute';
                            }, 2000);
                        });
                });
                
                // Set up double-click to edit
                const codeContainer = codeBlock.querySelector('.code-container');
                codeContainer.addEventListener('dblclick', function() {
                    editCodeBlock(this, blockIndex, playbook);
                });
                
                content.appendChild(codeBlock);
            }
        });
        
        // Add to document
        playbooksContainer.appendChild(playbookElement);
        
        // Add event listener for remove button
        playbookElement.querySelector('.remove-playbook').addEventListener('click', function() {
            playbookElement.remove();
            
            // Delete from terminal's playbooks or global playbooks
            if (playbook.filename in state.terminals[targetTerminal].playbooks) {
                delete state.terminals[targetTerminal].playbooks[playbook.filename];
            } else if (playbook.filename in state.globalPlaybooks) {
                delete state.globalPlaybooks[playbook.filename];
            }
        });
        
        // Apply variable substitutions
        updateVariableSubstitutions();
        
        // Apply syntax highlighting
        Prism.highlightAllUnder(playbookElement);
    }

    function createPlaybookContainer(name, title) {
        const playbookContainer = document.createElement('div');
        playbookContainer.className = 'playbook-container';
        playbookContainer.id = `playbook-${name}`;
        
        // Create header
        const header = document.createElement('div');
        header.className = 'playbook-header';
        
        // Create dropdown indicator (just one)
        const dropdownIndicator = document.createElement('span');
        dropdownIndicator.className = 'dropdown-indicator';
        dropdownIndicator.textContent = '▼'; // Down arrow for collapsed state
        
        // Create title
        const titleElement = document.createElement('h3');
        titleElement.className = 'playbook-title';
        titleElement.textContent = title;
        
        // Create actions container
        const actionsContainer = document.createElement('div');
        actionsContainer.className = 'playbook-actions';
        
        // Create close button
        const closeButton = document.createElement('button');
        closeButton.className = 'playbook-action-btn remove-playbook';
        closeButton.innerHTML = '&times;';
        closeButton.title = 'Remove playbook';
        
        // Assemble header - only add one dropdown indicator
        header.appendChild(dropdownIndicator);
        header.appendChild(titleElement);
        header.appendChild(actionsContainer);
        actionsContainer.appendChild(closeButton);
        
        // Create content area
        const content = document.createElement('div');
        content.className = 'playbook-content collapsed'; // Start collapsed
        
        // Assemble container
        playbookContainer.appendChild(header);
        playbookContainer.appendChild(content);
        
        // Add event listeners
        closeButton.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent triggering header click
            playbookContainer.remove();
            delete state.globalPlaybooks[name];
        });
        
        // Add event listener to header for toggling content
        header.addEventListener('click', function() {
            content.classList.toggle('collapsed');
            const indicator = this.querySelector('.dropdown-indicator');
            if (indicator) {
                indicator.textContent = content.classList.contains('collapsed') ? '▼' : '▲';
            }
        });
        
        return playbookContainer;
    }

    function copyToClipboard(text) {
        navigator.clipboard.writeText(text)
            .then(() => {
                // Find the button that triggered the copy and show visual feedback
                const activeButton = document.activeElement;
                if (activeButton && activeButton.classList.contains('code-action-btn')) {
                    const originalText = activeButton.textContent;
                    const originalClass = activeButton.className;
                    
                    // Change button text and add success class
                    activeButton.textContent = 'Copied!';
                    activeButton.className = 'code-action-btn copy-success';
                    
                    // Reset button after 1.5 seconds
                    setTimeout(() => {
                        activeButton.textContent = originalText;
                        activeButton.className = originalClass;
                    }, 1500);
                }
            })
            .catch(err => {
                console.error('Failed to copy text: ', err);
                
                // Visual indication of failure
                const activeButton = document.activeElement;
                if (activeButton && activeButton.classList.contains('code-action-btn')) {
                    const originalText = activeButton.textContent;
                    const originalClass = activeButton.className;
                    
                    // Change button text and add failure class
                    activeButton.textContent = 'Failed!';
                    activeButton.className = 'code-action-btn copy-fail';
                    
                    // Reset button after 1.5 seconds
                    setTimeout(() => {
                        activeButton.textContent = originalText;
                        activeButton.className = originalClass;
                    }, 1500);
                }
            });
    }

    function executeCode(code) {
        if (!state.activeTerminal) return;
        
        const port = state.terminals[state.activeTerminal].port;
        
        // Find the button that triggered the execution and show visual feedback
        const activeButton = document.activeElement;
        if (activeButton && activeButton.classList.contains('code-action-btn')) {
            const originalText = activeButton.textContent;
            const originalClass = activeButton.className;
            
            // Change button text and add progress class
            activeButton.textContent = 'Executing...';
            activeButton.className = 'code-action-btn execute-progress';
        }
        
        fetch('/api/terminals/sendkeys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                port: port,
                keys: code
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Failed to execute code:', data.error);
                
                // Show failure feedback if we have the active button
                const activeButton = document.activeElement;
                if (activeButton && activeButton.classList.contains('code-action-btn')) {
                    activeButton.textContent = 'Failed!';
                    activeButton.className = 'code-action-btn execute-fail';
                    
                    // Reset button after 1.5 seconds
                    setTimeout(() => {
                        activeButton.textContent = 'Execute';
                        activeButton.className = 'code-action-btn execute';
                    }, 1500);
                }
            } else {
                // Show success feedback if we have the active button
                const activeButton = document.activeElement;
                if (activeButton && activeButton.classList.contains('code-action-btn')) {
                    activeButton.textContent = 'Executed!';
                    activeButton.className = 'code-action-btn execute-success';
                    
                    // Reset button after 1.5 seconds
                    setTimeout(() => {
                        activeButton.textContent = 'Execute';
                        activeButton.className = 'code-action-btn execute';
                    }, 1500);
                }
            }
        })
        .catch(error => {
            console.error('Error executing code:', error);
            
            // Show failure feedback if we have the active button
            const activeButton = document.activeElement;
            if (activeButton && activeButton.classList.contains('code-action-btn')) {
                activeButton.textContent = 'Failed!';
                activeButton.className = 'code-action-btn execute-fail';
                
                // Reset button after 1.5 seconds
                setTimeout(() => {
                    activeButton.textContent = 'Execute';
                    activeButton.className = 'code-action-btn execute';
                }, 1500);
            }
        });
    }

    function editCodeBlock(codeContainer, blockIndex, playbook) {
        // Get the playbook from active terminal's state
        const activeTerminal = state.activeTerminal;
        if (!activeTerminal) return;
        
        // Extract the actual playbook filename from the playbook-id (format: terminal-id-playbook-name)
        let playbookFilename;
        if (typeof playbook === 'object') {
            // If playbook object is passed directly
            playbookFilename = playbook.filename;
        } else if (typeof playbook === 'string') {
            // If it's a string, it could be either a filename or a playbook-id
            if (playbook.startsWith(activeTerminal)) {
                // It's a playbook-id from the DOM
                const parts = playbook.split('-');
                // Remove terminal part from the ID
                parts.shift();
                playbookFilename = parts.join('-').replace(/-/g, '.'); // Convert hyphens back to dots for filename
            } else {
                // It's a direct filename
                playbookFilename = playbook;
            }
        } else {
            console.error('Invalid playbook identifier:', playbook);
            return;
        }
        
        // Get the playbook data
        const playbookData = state.terminals[activeTerminal].playbooks[playbookFilename];
        if (!playbookData) {
            console.error(`Playbook ${playbookFilename} not found in terminal ${activeTerminal}`);
            return;
        }
        
        // Get the pre and code elements
        const pre = codeContainer.querySelector('pre');
        const codeElement = pre.querySelector('code');
        
        // Get the raw code content
        const rawCode = playbookData.blocks[blockIndex].content;
        
        // Create a textarea to edit the code
        const textarea = document.createElement('textarea');
        textarea.className = 'code-textarea';
        textarea.value = rawCode;
        
        // Replace the pre element with textarea
        codeContainer.replaceChild(textarea, pre);
        
        // Function to save the edited code
        function saveEdit() {
            const newCode = textarea.value;
            
            // Update the state
            playbookData.blocks[blockIndex].content = newCode;
            
            // Create new pre and code elements
            const newPre = document.createElement('pre');
            const newCodeElement = document.createElement('code');
            newCodeElement.className = codeElement.className;
            newCodeElement.textContent = newCode;
            newCodeElement.dataset.rawCode = newCode;
            
            newPre.appendChild(newCodeElement);
            
            // Replace the textarea with the pre element
            codeContainer.replaceChild(newPre, textarea);
            
            // Apply syntax highlighting
            Prism.highlightElement(newCodeElement);
            
            // Apply variable substitutions
            updateVariableSubstitutions();
            
            // Re-bind execute and copy buttons to the new code element
            const codeBlock = codeContainer.closest('.code-block');
            if (codeBlock) {
                // Completely replace the copy button with a new one
                const oldCopyBtn = codeBlock.querySelector('.copy');
                if (oldCopyBtn) {
                    const newCopyBtn = document.createElement('button');
                    newCopyBtn.className = 'code-action-btn copy';
                    newCopyBtn.textContent = 'Copy';
                    newCopyBtn.addEventListener('click', function() {
                        copyToClipboard(getSubstitutedCode(newCodeElement));
                    });
                    
                    // Replace the old button
                    oldCopyBtn.parentNode.replaceChild(newCopyBtn, oldCopyBtn);
                }
                
                // Completely replace the execute button with a new one
                const oldExecuteBtn = codeBlock.querySelector('.execute');
                if (oldExecuteBtn) {
                    const newExecuteBtn = document.createElement('button');
                    newExecuteBtn.className = 'code-action-btn execute';
                    newExecuteBtn.textContent = 'Execute';
                    newExecuteBtn.addEventListener('click', function() {
                        executeCode(getSubstitutedCode(newCodeElement));
                    });
                    
                    // Replace the old button
                    oldExecuteBtn.parentNode.replaceChild(newExecuteBtn, oldExecuteBtn);
                }
            }
        }
        
        // Set up events for saving
        textarea.addEventListener('blur', saveEdit);
        textarea.addEventListener('keydown', function(e) {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                saveEdit();
            }
        });
        
        // Focus the textarea
        textarea.focus();
    }

    function handlePlaybookSearch() {
        const query = document.getElementById('searchInput').value.trim();
        const resultsContainer = document.getElementById('searchResults');
        
        if (query.length < 2) {
            resultsContainer.style.display = 'none';
            return;
        }
        
        // Show a loading indicator
        resultsContainer.innerHTML = '<div class="search-result-item">Searching...</div>';
        resultsContainer.style.display = 'block';
        
        fetch(`/api/playbooks/search?query=${encodeURIComponent(query)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Search request failed with status ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                resultsContainer.innerHTML = '';
                
                if (data.results && data.results.length > 0) {
                    data.results.forEach(result => {
                        const resultItem = document.createElement('div');
                        resultItem.className = 'search-result-item';
                        
                        // Highlight the matched text
                        let highlightedContent = result.line;
                        const queryRegex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
                        highlightedContent = highlightedContent.replace(queryRegex, '<span class="highlight">$1</span>');
                        
                        resultItem.innerHTML = `
                            <div class="result-header">
                                <span class="filename">${result.filename}</span>
                                <span class="line-number">Line ${result.line_number}</span>
                                <div class="result-actions">
                                    <button class="result-action-btn copy" title="Copy to clipboard"><i class="fas fa-copy"></i> Copy</button>
                                    <button class="result-action-btn execute" title="Execute in current terminal"><i class="fas fa-play"></i> Execute</button>
                                    <button class="result-action-btn import" title="Import playbook"><i class="fas fa-file-import"></i> Import</button>
                                </div>
                            </div>
                            <div class="content">${highlightedContent}</div>
                        `;
                        
                        // Add event listeners for the buttons
                        resultItem.querySelector('.import').addEventListener('click', function() {
                            importPlaybook(result.filename);
                        });
                        
                        resultItem.querySelector('.copy').addEventListener('click', function() {
                            copyToClipboard(result.line);
                            this.innerHTML = '<i class="fas fa-check"></i> Copied!';
                            setTimeout(() => {
                                this.innerHTML = '<i class="fas fa-copy"></i> Copy';
                            }, 2000);
                        });
                        
                        resultItem.querySelector('.execute').addEventListener('click', function() {
                            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Running...';
                            
                            // Get the command with variable substitution
                            let commandToExecute = result.line;
                            
                            // Apply variable substitution if we have an active terminal
                            if (state.activeTerminal && state.terminals[state.activeTerminal]) {
                                const variables = state.terminals[state.activeTerminal].variables;
                                
                                // Perform variable substitution
                                for (const [key, value] of Object.entries(variables)) {
                                    if (value) {
                                        // Convert variable name to match the format in the playbooks
                                        const placeholder = '$' + key.charAt(0).toUpperCase() + key.slice(1);
                                        const regex = new RegExp(escapeRegExp(placeholder), 'g');
                                        commandToExecute = commandToExecute.replace(regex, value);
                                    }
                                }
                            }
                            
                            executeInTerminal(commandToExecute)
                                .then(() => {
                                    this.innerHTML = '<i class="fas fa-check"></i> Done!';
                                    setTimeout(() => {
                                        this.innerHTML = '<i class="fas fa-play"></i> Execute';
                                    }, 2000);
                                })
                                .catch(() => {
                                    this.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
                                    setTimeout(() => {
                                        this.innerHTML = '<i class="fas fa-play"></i> Execute';
                                    }, 2000);
                                });
                        });
                        
                        resultsContainer.appendChild(resultItem);
                    });
                    
                    resultsContainer.style.display = 'block';
                } else {
                    resultsContainer.innerHTML = '<div class="search-result-item">No results found</div>';
                    resultsContainer.style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error searching playbooks:', error);
                resultsContainer.innerHTML = `<div class="search-result-item">Error searching playbooks: ${error.message}</div>`;
                resultsContainer.style.display = 'block';
            });
    }

    // Helper function to copy text to clipboard
    function copyToClipboard(text) {
        // Create a temporary textarea element
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.setAttribute('readonly', '');
        textarea.style.position = 'absolute';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        
        // Select and copy the text
        textarea.select();
        document.execCommand('copy');
        
        // Remove the temporary element
        document.body.removeChild(textarea);
        
        // Show a brief notification
        const notification = document.createElement('div');
        notification.className = 'copy-notification';
        notification.innerHTML = '<i class="fas fa-clipboard-check"></i> Copied to clipboard!';
        document.body.appendChild(notification);
        
        // Remove the notification after a short time
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 2000);
    }

    // Function to execute a command in the current terminal
    function executeInTerminal(command) {
        if (!state.activeTerminal) {
            alert('No active terminal found');
            return Promise.reject(new Error('No active terminal'));
        }
        
        const terminalPort = state.activeTerminal.replace('terminal-', '');
        
        // Send the command to the terminal
        return fetch('/api/terminals/sendkeys', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                port: terminalPort,
                keys: command
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Failed to execute command:', data.error);
                return Promise.reject(new Error(data.error || 'Failed to execute command'));
            }
            return data;
        })
        .catch(error => {
            console.error('Error executing command:', error);
            throw error;
        });
    }

    function importPlaybook(filename) {
        // Ensure we have an active terminal
        if (!state.activeTerminal || !state.terminals[state.activeTerminal]) {
            console.error('No active terminal for playbook import');
            return;
        }
        
        // Encode the filename to handle spaces and special characters
        const encodedFilename = encodeURIComponent(filename);
        
        fetch(`/api/playbooks/load/${encodedFilename}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.content) {
                    const playbook = {
                        filename: filename,
                        content: data.content,
                        blocks: parseMarkdown(data.content)
                    };
                    
                    // Store in active terminal's playbooks
                    state.terminals[state.activeTerminal].playbooks[filename] = playbook;
                    
                    // Display the playbook
                    displayPlaybook(playbook);
                    
                    // Clear the search input and hide results after importing
                    const searchInput = document.getElementById('searchInput');
                    const resultsContainer = document.getElementById('searchResults');
                    if (searchInput) {
                        searchInput.value = '';
                    }
                    if (resultsContainer) {
                        resultsContainer.style.display = 'none';
                    }
                }
            })
            .catch(error => {
                console.error('Error importing playbook:', error);
                alert('Failed to import playbook');
            });
    }

    /**
     * Notes Management Functions
     */
    
    function setupNotesPanel() {
        // Global notes toggle
        const globalNotesBtn = document.getElementById('globalNotesBtn');
        const globalNotesPanel = document.getElementById('globalNotesPanel');
        const tabNotesBtn = document.getElementById('tabNotesBtn');
        const tabNotesPanel = document.getElementById('tabNotesPanel');
        
        if (globalNotesBtn && globalNotesPanel) {
            globalNotesBtn.addEventListener('click', function() {
                // If tab notes is visible, hide it when showing global notes
                if (tabNotesPanel && tabNotesPanel.classList.contains('visible')) {
                    tabNotesPanel.classList.remove('visible');
                }
                
                globalNotesPanel.classList.toggle('visible');
            });
            
            globalNotesPanel.querySelector('.close-notes-btn').addEventListener('click', function() {
                globalNotesPanel.classList.remove('visible');
            });
        }
        
        // Tab notes toggle
        if (tabNotesBtn && tabNotesPanel) {
            tabNotesBtn.addEventListener('click', function() {
                // If global notes is visible, hide it when showing tab notes
                if (globalNotesPanel && globalNotesPanel.classList.contains('visible')) {
                    globalNotesPanel.classList.remove('visible');
                }
                
                tabNotesPanel.classList.toggle('visible');
            });
            
            tabNotesPanel.querySelector('.close-notes-btn').addEventListener('click', function() {
                tabNotesPanel.classList.remove('visible');
            });
        }
        
        // Setup notes saving
        const globalNotesText = document.getElementById('globalNotesText');
        if (globalNotesText) {
            globalNotesText.addEventListener('input', debounce(saveGlobalNotes, 500));
        }
        
        const tabNotesText = document.getElementById('tabNotesText');
        if (tabNotesText) {
            tabNotesText.addEventListener('input', debounce(saveTabNotes, 500));
        }
    }

    function loadGlobalNotes() {
        fetch('/api/notes/global')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('globalNotesText').value = data.content;
                }
            })
            .catch(error => {
                console.error('Error loading global notes:', error);
            });
    }

    function loadTabNotes(terminalId) {
        if (!terminalId) return;
        
        const port = state.terminals[terminalId].port;
        fetch(`/api/notes/tab/term-${port}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('tabNotesText').value = data.content;
                }
            })
            .catch(error => {
                console.error('Error loading tab notes:', error);
            });
    }

    function saveGlobalNotes() {
        const content = document.getElementById('globalNotesText').value;
        
        fetch('/api/notes/global', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content
            })
        })
        .catch(error => {
            console.error('Error saving global notes:', error);
        });
    }

    function saveTabNotes() {
        if (!state.activeTerminal) return;
        
        const content = document.getElementById('tabNotesText').value;
        const port = state.terminals[state.activeTerminal].port;
        
        fetch(`/api/notes/tab/term-${port}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                content: content
            })
        })
        .catch(error => {
            console.error('Error saving tab notes:', error);
        });
    }

    /**
     * Utility Functions
     */
    
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); // $& means the whole matched string
    }

    // Setup custom variable management
    function setupCustomVariables() {
        const addVariableBtn = document.getElementById('addVariableBtn');
        if (addVariableBtn) {
            addVariableBtn.addEventListener('click', function() {
                // Prompt for variable name
                const variableName = prompt('Enter variable name (camelCase recommended):');
                if (!variableName) return;
                
                // Validate variable name
                if (!/^[a-zA-Z][a-zA-Z0-9]*$/.test(variableName)) {
                    alert('Variable name must start with a letter and contain only letters and numbers');
                    return;
                }
                
                // Check if variable already exists
                if (document.getElementById(variableName)) {
                    alert('A variable with this name already exists');
                    return;
                }
                
                // Create variable input
                const variableInput = document.createElement('div');
                variableInput.className = 'variable-input custom-variable';
                
                // First letter uppercase for display, camelCase for ID
                const displayName = variableName.charAt(0).toUpperCase() + variableName.slice(1);
                const placeholderName = '$' + displayName;
                
                // Create the HTML structure
                variableInput.innerHTML = `
                    <label for="${variableName}">${displayName}:</label>
                    <input type="text" id="${variableName}" name="${variableName}" placeholder="${placeholderName}">
                    <button class="remove-variable-btn" title="Remove Variable">&times;</button>
                `;
                
                // Add to DOM
                const container = document.getElementById('variableInputsContainer');
                if (container) {
                    container.appendChild(variableInput);
                }
                
                // Add event listener for input
                const input = variableInput.querySelector('input');
                if (input) {
                    input.addEventListener('input', function() {
                        if (state.activeTerminal) {
                            state.terminals[state.activeTerminal].variables[this.id] = this.value;
                            updateVariableSubstitutions();
                        }
                    });
                }
                
                // Add event listener for remove button
                const removeBtn = variableInput.querySelector('.remove-variable-btn');
                if (removeBtn) {
                    removeBtn.addEventListener('click', function() {
                        if (confirm(`Remove ${displayName} variable?`)) {
                            // Remove from state if it exists
                            if (state.activeTerminal) {
                                delete state.terminals[state.activeTerminal].variables[variableName];
                            }
                            
                            // Remove from DOM
                            variableInput.remove();
                            
                            // Update displays
                            updateVariableSubstitutions();
                        }
                    });
                }
                
                // Initialize this variable in all terminals
                Object.keys(state.terminals).forEach(terminalId => {
                    if (!state.terminals[terminalId].variables) {
                        state.terminals[terminalId].variables = {};
                    }
                    state.terminals[terminalId].variables[variableName] = '';
                });
            });
        }
    }

    function migrateGlobalPlaybooks() {
        // Check if there are any global playbooks
        if (Object.keys(state.globalPlaybooks).length > 0) {
            // Get the active terminal
            const activeTerminal = state.activeTerminal;
            
            // Migrate each global playbook to the active terminal
            Object.keys(state.globalPlaybooks).forEach(playbookName => {
                const playbook = state.globalPlaybooks[playbookName];
                
                // Store in active terminal's playbooks
                state.terminals[activeTerminal].playbooks[playbookName] = playbook;
                
                // Remove from global playbooks
                delete state.globalPlaybooks[playbookName];
            });
        }
    }

    function displayTerminalPlaybooks(terminalId) {
        const playbooksContainer = document.getElementById('playbooks');
        if (!playbooksContainer) return;
        
        // Clear the playbooks container
        playbooksContainer.innerHTML = '';
        
        // Display playbooks for the active terminal
        Object.keys(state.terminals[terminalId].playbooks).forEach(playbookName => {
            const playbook = state.terminals[terminalId].playbooks[playbookName];
            displayPlaybook(playbook, terminalId);
        });
    }

    /**
     * Playbook Creation Functions
     */
    
    function setupCreatePlaybook() {
        // Get modal elements
        const modal = document.getElementById('createPlaybookModal');
        const createBtn = document.getElementById('createPlaybookBtn');
        const closeBtn = modal.querySelector('.close-modal-btn');
        const cancelBtn = document.getElementById('cancelPlaybookBtn');
        const submitBtn = document.getElementById('createPlaybookSubmitBtn');
        const nameInput = document.getElementById('newPlaybookName');
        const contentInput = document.getElementById('newPlaybookContent');
        
        // Open modal when create button is clicked
        createBtn.addEventListener('click', function() {
            // Default content with template
            if (!contentInput.value) {
                contentInput.value = `# New Playbook

## Step 1: Getting Started
\`\`\`bash
echo "This is my first step"
\`\`\`

## Step 2: Next Action
\`\`\`bash
# Add your commands here
\`\`\``;
            }
            
            modal.style.display = 'block';
        });
        
        // Close modal functions
        function closeModal() {
            modal.style.display = 'none';
        }
        
        closeBtn.addEventListener('click', closeModal);
        cancelBtn.addEventListener('click', closeModal);
        
        // Close when clicking outside of the modal content
        window.addEventListener('click', function(event) {
            if (event.target === modal) {
                closeModal();
            }
        });
        
        // Handle form submission
        submitBtn.addEventListener('click', function() {
            // Validate inputs
            const name = nameInput.value.trim();
            const content = contentInput.value.trim();
            
            if (!name) {
                alert('Please enter a playbook name');
                return;
            }
            
            if (!content) {
                alert('Please add content to your playbook');
                return;
            }
            
            // Ensure filename has .md extension
            let filename = name;
            if (!filename.toLowerCase().endsWith('.md')) {
                filename += '.md';
            }
            
            // Create the playbook
            createNewPlaybook(filename, content);
            
            // Reset form and close modal
            nameInput.value = '';
            contentInput.value = '';
            closeModal();
        });
    }
    
    function createNewPlaybook(filename, content) {
        // Ensure we have an active terminal
        if (!state.activeTerminal || !state.terminals[state.activeTerminal]) {
            console.error('No active terminal for playbook creation');
            return;
        }
        
        try {
            // Parse the markdown content
            const blocks = parseMarkdown(content);
            
            // Create the playbook object
            const playbook = {
                filename: filename,
                content: content,
                blocks: blocks
            };
            
            // Check if filename already exists in this terminal
            if (state.terminals[state.activeTerminal].playbooks[filename]) {
                if (!confirm(`A playbook named "${filename}" already exists in this terminal. Do you want to replace it?`)) {
                    return;
                }
            }
            
            // Store in active terminal's playbooks
            state.terminals[state.activeTerminal].playbooks[filename] = playbook;
            
            // Display the playbook
            displayPlaybook(playbook);
            
            console.log(`Playbook "${filename}" created successfully`);
        } catch (error) {
            console.error('Error creating playbook:', error);
            alert(`Failed to create playbook: ${error.message}`);
        }
    }
});

// Setup collapsible sections
function setupCollapsibleSections() {
    document.querySelectorAll('.playbook-header').forEach(header => {
        if (!header.hasAttribute('listener-added')) {
            header.setAttribute('listener-added', 'true');
            header.addEventListener('click', function() {
                const content = this.nextElementSibling;
                const indicator = this.querySelector('.dropdown-indicator');
                
                if (content && content.classList.contains('playbook-content')) {
                    content.classList.toggle('collapsed');
                    
                    if (indicator) {
                        indicator.textContent = content.classList.contains('collapsed') ? '▼' : '▲';
                    }
                }
            });
        }
    });
}
