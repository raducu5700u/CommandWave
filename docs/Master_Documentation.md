# CommandWave Master Documentation

## File: `core/playbook_utils.py`

**Overall Purpose:** Core logic for validating, parsing, and managing playbooks, including metadata extraction and file I/O.

### Key Components:

* **Directory initialization block**:
  * Type: Initialization code
  * Purpose: Ensure the `playbooks` directory exists at startup (`PLAYBOOKS_DIR`).
  * Apparent Usage: Executed on import to prepare storage for playbooks. **Used**
  * Line Range: 11–13

* **validate_playbook**:
  * Type: Function
  * Purpose: Basic check that content is non-empty; placeholder for more advanced markdown validation.
  * Apparent Usage: Called by `save_playbook` to validate before writing. **Used**
  * Line Range: 14–31

* **process_playbook**:
  * Type: Function
  * Purpose: Parses playbook content to extract title, description, code blocks (IDs, languages, code text, start/end), commands (from bash blocks), and variables (`$VAR`/`${VAR}`). Returns metadata dict.
  * Apparent Usage: Used by `load_playbook` and `save_playbook` to build frontend data. **Used**
  * Line Range: 33–99

* **get_playbook_path**:
  * Type: Function
  * Purpose: Constructs full filesystem path of a playbook file under `PLAYBOOKS_DIR`.
  * Apparent Usage: Utility used by `load_playbook` and `save_playbook`. **Used**
  * Line Range: 101–110

* **load_playbook**:
  * Type: Function
  * Purpose: Reads content from disk, invokes `process_playbook`, packs metadata, content, path, and last-modified timestamp into a tuple.
  * Apparent Usage: Back-end for the `/api/playbooks/<filename>` GET route. **Used**
  * Line Range: 113–140

* **save_playbook**:
  * Type: Function
  * Purpose: Validates content, writes to disk, re-processes playbook, returns updated metadata and content.
  * Apparent Usage: Back-end for the `/api/playbooks` POST route. **Used**
  * Line Range: 141–170

---

## File: `core/sync_utils.py`

**Overall Purpose:** Core utilities for real-time synchronization and client management using SocketIO.

### Key Components:

* **ClientTracker**:
    * Type: Class
    * Purpose: Tracks connected clients, their active terminal tabs, and editing locks for collaborative editing. Provides methods to add/remove clients, update terminal rooms, and manage locks.
    * Apparent Usage: Used by real-time event handlers to manage client state and resource locks. **Used**
    * Line Range: 14–142

* **client_tracker**:
    * Type: Singleton Instance
    * Purpose: Global instance of `ClientTracker` for application-wide client tracking.
    * Apparent Usage: Imported by routes and sync modules to access client registry. **Used**
    * Line Range: 143–148

* **broadcast_to_terminal**:
    * Type: Function
    * Purpose: Emits a named event with payload to all clients in a specific terminal room via SocketIO.
    * Apparent Usage: Invoked when terminal-specific updates occur (e.g., new command output). **Used**
    * Line Range: 149–180

* **broadcast_global**:
    * Type: Function
    * Purpose: Emits a named event with payload to all connected clients via SocketIO.
    * Apparent Usage: Used for global notifications (e.g., new terminal created). **Used**
    * Line Range: 183–208

* **init_socketio**:
    * Type: Function
    * Purpose: Initializes the Flask SocketIO instance with CORS and logging configured. Ensures a singleton for the app.
    * Apparent Usage: Called in `main.py` to set up real-time communication. **Used**
    * Line Range: 214–223

* **get_socketio**:
    * Type: Function
    * Purpose: Returns the existing SocketIO singleton instance for event emission.
    * Apparent Usage: Used by broadcasting functions to access SocketIO. **Used**
    * Line Range: 225–227

---

## File: [main.py](cci:7://file:///home/kali/Tools/CommandWave/main.py:0:0-0:0)

**Overall Purpose:**  
Entry point for the CommandWave Flask application. Configures logging, parses CLI arguments, initializes directories, tmux/ttyd processes, registers routes & SocketIO events, and starts the web server.

### Key Components:

* **parse_arguments**  
  * Type: Function  
  * Purpose: Defines and parses command‐line options (`--port`, `--use-default-tmux-config`, `--hostname`, `--remote`). Supplies startup configuration.  
  * Apparent Usage: Used in `if __name__ == '__main__'` to control server & terminal launch. **Used**  
  * Line Range: 66–77

* **is_port_available**  
  * Type: Function  
  * Purpose: Attempts a TCP connection to `HOSTNAME:port` to detect if the port is free.  
  * Apparent Usage: Called by `find_available_port` and during startup to choose terminal ports. **Used**  
  * Line Range: 79–82

* **find_available_port**  
  * Type: Function  
  * Purpose: Iterates a port range, returns the first free port not already tracked in `app.terminals`.  
  * Apparent Usage: Falls back to this when default terminal port is occupied. **Used**  
  * Line Range: 84–89

* **start_ttyd_process**  
  * Type: Function  
  * Purpose: Creates or reuses a tmux session, then launches a `ttyd` process bound to that session on a given port. Returns the process handle.  
  * Apparent Usage: Invoked to create the “Main Terminal” at startup and for each new terminal via API. **Used**  
  * Line Range: 91–202

* **send_keys_to_tmux**  
  * Type: Function  
  * Purpose: Sends keystrokes to a named tmux session (for programmatic input into terminals).  
  * Apparent Usage: Called by the `send_keys` route. **Used**  
  * Line Range: 204–222

* **kill_terminal**  
  * Type: Function  
  * Purpose: Terminates a ttyd process and its tmux session; cleans up resources for a given port.  
  * Apparent Usage: Used by both `delete_terminal` and cleanup routines. **Used**  
  * Line Range: 224–263

* **cleanup_all_terminals**  
  * Type: Function  
  * Purpose: Iterates over all active terminals in `app.terminals` and calls `kill_terminal` on each. Registered with `atexit`.  
  * Apparent Usage: Automatically runs on application exit. **Used**  
  * Line Range: 265–290

* **signal_handler**  
  * Type: Function  
  * Purpose: Catches SIGINT/SIGTERM, ensures `cleanup_all_terminals` runs once, then exits.  
  * Apparent Usage: Registered for process signals at startup. **Used**  
  * Line Range: 298–309

* **index**  
  * Type: Route (`@app.route('/')`)  
  * Purpose: Renders the main UI (`templates/index.html`), passing initial config (e.g., `HOSTNAME`, `DEFAULT_TERMINAL_PORT`).  
  * Apparent Usage: Entry point for browser clients. **Used**  
  * Line Range: 328–333

* **healthcheck**  
  * Type: Route (`@app.route('/health')` or similar)  
  * Purpose: Returns basic success status for monitoring.  
  * Apparent Usage: Used by uptime checks. **Used**  
  * Line Range: 335–338

* **get_playbook_file**  
  * Type: Route Helper / Route  
  * Purpose: Serves raw playbook files from any nested directory under `playbooks/`.  
  * Apparent Usage: Used by playbook‐related routes to fetch file contents. **Used**  
  * Line Range: 340–381

* **list_terminals**  
  * Type: Route (`@app.route('/api/terminals', methods=['GET'])`)  
  * Purpose: Returns JSON array of active terminals (ports, names, timestamps).  
  * Apparent Usage: Frontend polls to display available sessions. **Used**  
  * Line Range: 384–400

* **new_terminal**  
  * Type: Route (`@app.route('/api/terminals', methods=['POST'])`)  
  * Purpose: Allocates an available port, spawns a new tmux/ttyd session, stores it in `app.terminals`, returns its port.  
  * Apparent Usage: Triggered when user opens a new terminal tab. **Used**  
  * Line Range: 402–452

* **send_keys**  
  * Type: Route (`@app.route('/api/terminals/<port>/keys', methods=['POST'])`)  
  * Purpose: Accepts keystroke payload, forwards it via `send_keys_to_tmux` to the specified terminal.  
  * Apparent Usage: Wired to frontend “type” events. **Used**  
  * Line Range: 454–483

* **delete_terminal**  
  * Type: Route (`@app.route('/api/terminals/<port>', methods=['DELETE'])`)  
  * Purpose: Invokes `kill_terminal` for the given port, removes it from `app.terminals`.  
  * Apparent Usage: Called when user closes a terminal tab. **Used**  
  * Line Range: 485–516

* **delete_terminal_post**  
  * Type: Route (`@app.route('/api/terminals/<port>/delete', methods=['POST'])`)  
  * Purpose: Alternate POST-based delete endpoint for environments restricted against DELETE.  
  * Apparent Usage: Fallback for clients not supporting DELETE. **Used**  
  * Line Range: 518–521

* **rename_terminal**  
  * Type: Route (`@app.route('/api/terminals/<port>/rename', methods=['POST'])`)  
  * Purpose: Updates the display name of a terminal session in `app.terminals`.  
  * Apparent Usage: Invoked by UI when user renames a tab. **Used**  
  * Line Range: 523–551

* **handle_global_notes**  
  * Type: Route (`@app.route('/api/notes/global', methods=['GET','POST'])`)  
  * Purpose: Persists or retrieves shared notes stored under `notes_data/`.  
  * Apparent Usage: Frontend note widget for global notes. **Used**  
  * Line Range: 554–589

* **handle_tab_notes**  
  * Type: Route (`@app.route('/api/notes/<terminal_id>', methods=['GET','POST'])`)  
  * Purpose: Persists or retrieves notes scoped to a specific terminal tab.  
  * Apparent Usage: Frontend manages per-tab note state. **Used**  
  * Line Range: 591–631

* **search_playbooks**  
  * Type: Route (`@app.route('/api/playbooks/search', methods=['GET'])`)  
  * Purpose: Searches all playbook files for a query string, returns matching lines.  
  * Apparent Usage: UI “search in playbooks” feature. **Used**  
  * Line Range: 634–677

* **save_playbook**  
  * Type: Route (`@app.route('/api/playbooks', methods=['POST'])`)  
  * Purpose: Creates or overwrites a playbook file in `playbooks/`.  
  * Apparent Usage: Called when user saves edits. **Used**  
  * Line Range: 679–723

* **load_playbook**  
  * Type: Route (`@app.route('/api/playbooks/<filename>', methods=['GET'])`)  
  * Purpose: Loads the contents of a specified playbook file.  
  * Apparent Usage: Frontend loads files into editor. **Used**  
  * Line Range: 725–791

* **list_all_playbooks**  
  * Type: Route (`@app.route('/api/playbooks', methods=['GET'])`)  
  * Purpose: Lists filenames of all playbooks in the shared directory.  
  * Apparent Usage: Populates file browser in UI. **Used**  
  * Line Range: 793–807

* **sync_playbook**  
  * Type: Route (`@app.route('/api/playbooks/<filename>/sync', methods=['POST'])`)  
  * Purpose: Updates a shared playbook’s content and emits SocketIO events to clients.  
  * Apparent Usage: Real-time collaborative editing. **Used**  
  * Line Range: 809–844

* **get_playbook_state**  
  * Type: Route (`@app.route('/api/playbooks/<filename>/state', methods=['GET'])`)  
  * Purpose: Retrieves current content & metadata of a playbook for late-joining clients.  
  * Apparent Usage: Supports SocketIO-based state sync. **Used**  
  * Line Range: 846–868

* **sync_variables**  
  * Type: Route (`@app.route('/api/variables/<terminal_id>/sync', methods=['POST'])`)  
  * Purpose: Saves or broadcasts variable state for a terminal session.  
  * Apparent Usage: Tied to the variable‐panel real‑time sync feature. **Used**  
  * Line Range: 870–902

* **list_all_variables**  
  * Type: Route (`@app.route('/api/variables/list/all', methods=['GET'])`)  
  * Purpose: Aggregates all stored variable JSON files under `variables_data/`.  
  * Apparent Usage: UI option to import/export variables across sessions. **Used**  
  * Line Range: ~944–987

## File: `routes/playbook_routes.py`

**Overall Purpose:** Flask Blueprint providing CRUD, import, and search endpoints for playbooks stored on disk and in-memory.

### Key Components:

* **load_playbooks_from_disk**:
    * Type: Function
    * Purpose: Scans `PLAYBOOKS_DIR` for `.md` files on import, processes each via `process_playbook`, and populates the `playbooks` dict with metadata and content.
    * Apparent Usage: Executed automatically on module import. **Used**
    * Line Range: ~24–64

* **import_playbook**:
    * Type: Route (`POST /api/playbooks/import`)
    * Purpose: Accepts JSON (`content`, `filename`), validates using `validate_playbook`, saves the file, and updates in-memory store.
    * Apparent Usage: Frontend “Import Playbook” feature. **Used**
    * Line Range: 69–120

* **list_playbooks**:
    * Type: Route (`GET /api/playbooks`)
    * Purpose: Returns JSON list of all available playbooks from the in-memory `playbooks` dictionary.
    * Apparent Usage: Populates playbook browser. **Used**
    * Line Range: 122–131

* **get_playbook**:
    * Type: Route (`GET /api/playbooks/<playbook_id>`)
    * Purpose: Retrieves a single playbook’s metadata and content by its ID.
    * Apparent Usage: Used by editor to load selected playbook. **Used**
    * Line Range: 133–145

* **delete_playbook**:
    * Type: Route (`DELETE /api/playbooks/<playbook_id>`)
    * Purpose: Deletes the playbook file on disk and removes its entry from the in-memory store.
    * Apparent Usage: Frontend delete action. **Used**
    * Line Range: 147–170

* **update_playbook**:
    * Type: Route (`POST /api/playbooks/<playbook_id>/update`)
    * Purpose: Validates updated content, writes to disk, updates in-memory metadata (title, description, timestamps).
    * Apparent Usage: Frontend code block editing endpoint. **Used**
    * Line Range: 172–213

* **search_playbooks**:
    * Type: Route (`GET /api/playbooks/search`)
    * Purpose: Searches all playbooks for a query string, returns matching lines with context.
    * Apparent Usage: UI search functionality. **Used**
    * Line Range: 215–243

* **create_playbook**:
    * Type: Route (`POST /api/playbooks/create`)
    * Purpose: Creates a new playbook file from scratch, ensuring unique filename and validation.
    * Apparent Usage: New playbook creation feature. **Used**
    * Line Range: 246–294

---

## File: `routes/sync_routes.py`

**Overall Purpose:** Registers WebSocket event handlers and HTTP endpoints for real-time synchronization and client management using Flask-SocketIO.

### Key Components:

* **init_socketio_events**:
    * Type: Function
    * Purpose: Binds SocketIO event handlers for `connect`, `disconnect`, `join_terminal`, `leave_terminal`, `terminal_created`, `terminal_renamed`, `terminal_closed`, `playbook_updated`, `notes_updated`, `playbook_list_update_request`, `editing_started`, `editing_stopped`, `client_ping`, `variable_update_request`, and `code_block_updated` to enable real-time collaboration.
    * Apparent Usage: Called on server startup to set up event handling. **Used**
    * Line Range: ~25–493

* **get_clients**:
    * Type: Route (`GET /api/sync/clients`)
    * Purpose: Returns JSON listing all connected clients and total count.
    * Apparent Usage: Debugging/admin interface. **Used**
    * Line Range: ~496–503

* **get_terminal_clients**:
    * Type: Route (`GET /api/sync/terminals/<terminal_id>/clients`)
    * Purpose: Returns JSON listing clients connected to a specific terminal tab.
    * Apparent Usage: Provides terminal-specific presence data. **Used**
    * Line Range: ~504–514

---

## File: `routes/variable_routes.py`

**Overall Purpose:** Flask Blueprint for managing tab-specific variables: persistence, CRUD operations, legacy support, and debug fallback.

### Key Components:

* **get_variable_filename**:
    * Type: Function
    * Purpose: Sanitizes tab_id for filesystem, returns JSON storage path for variables.
    * Apparent Usage: Used by load/save routines. **Used**
    * Line Range: 26–30

* **load_tab_variables**:
    * Type: Function
    * Purpose: Reads persisted JSON variables for a tab; returns empty dict if missing or on error.
    * Apparent Usage: Called by `get_tab_variables`. **Used**
    * Line Range: 32–41

* **save_tab_variables**:
    * Type: Function
    * Purpose: Writes variable dict to disk as JSON for a tab; logs errors on failure.
    * Apparent Usage: Called after create/update/delete. **Used**
    * Line Range: 43–52

* **get_tab_variables**:
    * Type: Function
    * Purpose: Retrieves in-memory variables for a tab, loading from disk on first access.
    * Apparent Usage: Base for all variable retrieval endpoints. **Used**
    * Line Range: 54–58

* **create_variable**:
    * Type: Route (`POST /api/variables/create/<tab_id>`)
    * Purpose: Adds a new variable with display_name and reference (spaces removed), persists to disk.
    * Apparent Usage: Triggered by frontend “Add Variable” modal. **Used**
    * Line Range: 60–97

* **update_variable**:
    * Type: Route (`POST /api/variables/update/<tab_id>`)
    * Purpose: Updates variable name/value, handles renaming references, persists change.
    * Apparent Usage: Invoked when editing existing variable. **Used**
    * Line Range: 99–137

* **delete_variable**:
    * Type: Route (`POST /api/variables/delete/<tab_id>`)
    * Purpose: Deletes a variable from memory and storage.
    * Apparent Usage: Frontend variable delete action. **Used**
    * Line Range: 139–169

* **list_variables**:
    * Type: Route (`GET /api/variables/list/<tab_id>`)
    * Purpose: Returns JSON and HTML snippet of all variables for UI rendering.
    * Apparent Usage: Populates variable panel in templates. **Used**
    * Line Range: 171–201

* **list_variables_direct**:
    * Type: Route (`GET /api/variables/list-direct/<tab_id>`)
    * Purpose: Alias to `list_variables` to address routing constraints. **Used**
    * Line Range: 203–206

* **load_variables**:
    * Type: Route (`GET /api/variables/load/<tab_id>`)
    * Purpose: Provides simplified JSON mapping of variable references to values. **Used**
    * Line Range: 208–228

* **Legacy endpoints** (`create_variable_legacy`, `update_variable_legacy`, `delete_variable_legacy`, `list_variables_legacy`):
    * Type: Routes
    * Purpose: Forward calls without tab_id to default tab for backward compatibility. **Used**
    * Line Range: 231–249

* **catch_all_route**:
    * Type: Route (`GET/POST/PUT/DELETE /api/variables/<path>`)
    * Purpose: Fallback debug route returning error JSON for unrecognized paths. **Used**
    * Line Range: 252–259

---

## File: `routes/notes_routes.py`

**Overall Purpose:** Flask Blueprint for notes-related API endpoints handling global and terminal-specific notes operations.

### Key Components:

* **get_global_notes**:
    * Type: Route (`GET /api/notes/global`)
    * Purpose: Retrieves content via `load_global_notes` and returns JSON.
    * Apparent Usage: Frontend global notes panel. **Used**
    * Line Range: ~20–34

* **save_global_notes_endpoint**:
    * Type: Route (`POST /api/notes/global`)
    * Purpose: Persists content via `save_global_notes` and returns success status.
    * Apparent Usage: Save global notes action. **Used**
    * Line Range: ~36–58

* **get_terminal_notes**:
    * Type: Route (`GET /api/notes/terminal/<terminal_id>`)
    * Purpose: Loads per-terminal notes via `load_terminal_notes` and returns JSON.
    * Apparent Usage: Load terminal notes on tab open. **Used**
    * Line Range: ~60–75

* **save_terminal_notes_endpoint**:
    * Type: Route (`POST /api/notes/terminal/<terminal_id>`)
    * Purpose: Persists terminal notes via `save_terminal_notes`.
    * Apparent Usage: Save terminal notes action. **Used**
    * Line Range: ~77–99

* **list_notes**:
    * Type: Route (`GET /api/notes/list`)
    * Purpose: Returns list via `list_all_notes`.
    * Apparent Usage: Notes browser. **Used**
    * Line Range: ~101–115

* **rename_terminal_notes_endpoint**:
    * Type: Route (`POST /api/notes/terminal/rename`)
    * Purpose: Renames notes file via `rename_terminal_notes`.
    * Apparent Usage: Rename notes file action. **Used**
    * Line Range: ~117–132

---

## File: `routes/terminal_routes.py`

**Overall Purpose:** Flask Blueprint for creating, renaming, deleting, listing, and sending commands to terminal sessions.

### Key Components:

* **create_terminal**:
    * Type: Route (`POST /api/terminals/new`)
    * Purpose: Starts a new tmux session via `start_ttyd_process` and registers it in the app.
    * Apparent Usage: Frontend new terminal action. **Used**
    * Line Range: ~18–95

* **rename_terminal**:
    * Type: Route (`POST /api/terminals/rename/<int:port>`)
    * Purpose: Updates the tab name for a given terminal port.
    * Apparent Usage: Tab rename feature. **Used**
    * Line Range: ~97–126

* **delete_terminal_post**:
    * Type: Route (`POST /api/terminals/delete/<int:port>`)
    * Purpose: Terminates a terminal session via POST.
    * Apparent Usage: Frontend delete button fallback. **Used**
    * Line Range: ~128–131

* **delete_terminal**:
    * Type: Route (`DELETE /api/terminals/<int:port>`)
    * Purpose: Terminates a terminal session via DELETE.
    * Apparent Usage: RESTful deletion endpoint. **Used**
    * Line Range: ~133–170

* **list_terminals**:
    * Type: Route (`GET /api/terminals/list`)
    * Purpose: Returns JSON of active terminals and metadata.
    * Apparent Usage: Populates terminal list UI. **Used**
    * Line Range: ~172–195

* **send_command**:
    * Type: Route (`POST /api/terminals/send-command`)
    * Purpose: Sends raw command strings to the tmux session via `tmux send-keys`.
    * Apparent Usage: Terminal input handler. **Used**
    * Line Range: ~197–257

---

## File: `core/notes_storage.py`

**Overall Purpose:** Persistent storage utilities for global and per-terminal notes under `data/notes`.

### Key Components:

* **Directory initialization block**:
    * Type: Initialization code
    * Purpose: Ensure the `data/notes` directory exists, creating it if missing.
    * Apparent Usage: Executed on import to prepare note storage. **Used**
    * Line Range: ~9–15

* **get_global_notes_path**:
    * Type: Function
    * Purpose: Returns the file path for the global notes markdown file (`global_notes.md`).
    * Apparent Usage: Called by `save_global_notes` and `load_global_notes`. **Used**
    * Line Range: 25–27

* **get_terminal_notes_path**:
    * Type: Function
    * Purpose: Sanitizes a terminal name (alphanumeric, hyphens, underscores) and constructs its notes file path (`<name>.md`).
    * Apparent Usage: Used by terminal note functions (`save_terminal_notes`, `load_terminal_notes`, `rename_terminal_notes`). **Used**
    * Line Range: 29–34

* **save_global_notes**:
    * Type: Function
    * Purpose: Writes provided content to the global notes file, returns success boolean.
    * Apparent Usage: Used by the `handle_global_notes` route for persisting notes. **Used**
    * Line Range: 36–53

* **load_global_notes**:
    * Type: Function
    * Purpose: Reads and returns global notes content; returns empty string if file not found.
    * Apparent Usage: Used by the `handle_global_notes` route to load notes. **Used**
    * Line Range: 55–74

* **save_terminal_notes**:
    * Type: Function
    * Purpose: Writes content to a terminal-specific notes file. Returns success boolean.
    * Apparent Usage: Used by the `handle_tab_notes` route for per-tab persistence. **Used**
    * Line Range: 76–94

* **load_terminal_notes**:
    * Type: Function
    * Purpose: Reads and returns notes for a specific terminal; returns empty string if missing.
    * Apparent Usage: Used by the `handle_tab_notes` route. **Used**
    * Line Range: 96–118

* **list_all_notes**:
    * Type: Function
    * Purpose: Scans the `data/notes` directory, reports whether global notes exist and lists terminal note files with metadata (name, size, modification time).
    * Apparent Usage: Used by notes routes to populate note listings in the UI. **Used**
    * Line Range: 120–155

* **rename_terminal_notes**:
    * Type: Function
    * Purpose: Renames a terminal-specific notes file when a terminal session is renamed.
    * Apparent Usage: Called by the `rename_terminal` route to keep note filenames in sync. **Used**
    * Line Range: 157–168

---

*No significant unused components detected in [main.py](cci:7://file:///home/kali/Tools/CommandWave/main.py:0:0-0:0). All functions and routes are referenced by startup logic or frontend API calls.*

---

## Directories

### Directory: `data/`

**Overall Purpose:** Stores initial sample content for notes and variables used by the app.

#### Subdirectories:

* `notes/`: Sample global and terminal-specific note files.
* `variables/`: Sample variable definition JSON files per terminal.

---

### Directory: `notes_data/`

**Overall Purpose:** Persistent storage for global and terminal-specific notes. Managed via `core/notes_storage.py`.

---

### Directory: `variables_data/`

**Overall Purpose:** Persistent storage for variable definitions per terminal. Managed via `routes/variable_routes.py`.

---

### Directory: `playbooks/`

**Overall Purpose:** Contains markdown `.md` playbooks. Each file is parsed and executed via the playbook API. Supports nested folders (e.g., `tutorials/`).

---

## Key Files

### File: `main.py`

**Overall Purpose:** Entry point that initializes the Flask app, registers blueprints, configures Socket.IO, and manages ttyd/tmux lifecycles.

### File: `commandwave.log`

**Overall Purpose:** Runtime log file capturing server events, errors, and debug information.

---

## Templates

### File: `templates/index.html`

**Overall Purpose:** Main HTML template defining the UI structure, links CSS and JS assets, and includes partial modals.

### Key Sections:

* **Head**:
  * Meta tags and `title`
  * Links to global styles (`css/style.css`, `css/base.css`), component styles, and theme CSS under `static/css/`
  * Inline Prism.js theme overrides and Markdown-It CDN script

* **Body**:
  * Hidden `hostname` input for API base resolution
  * `<header>` with app title, controls (new terminal, settings, notifications)
  * `<main>` container with sections for Variables (toggleable), Terminals, Notes, Playbooks, Search, etc.
  * Includes for partials: `_settings_modal.html`, `_variable_modal.html`
  * Footer scripts: Socket.IO client, Prism.js, Markdown-It, and `<script type="module" src="js/main.js">`
  * Hidden `api-base-url` element for front-end API calls

---

### File: `templates/partials/_settings_modal.html`

**Overall Purpose:** Modal dialog for configuring themes, note size, editor preferences, sync settings, and general options.

### Key Components:

* **Category navigation** bar with tabs (Appearance, Note Size, General, Sync, Editor)
* **Settings panels** for each category, containing form controls (toggles, number inputs, dropdowns)
* **Search** within settings and Prev/Next navigation
* **Save/Cancel** and **Reset** buttons in modal footer

---

### File: `templates/partials/_variable_modal.html`

**Overall Purpose:** Modal for creating or editing variables (display name and value) via a form.

### Key Components:

* Form fields: **Name** (allow spaces), **Reference** (auto-generated, no spaces), and **Value**
* Validation hints and error messages
* Submit (`Add`/`Save`) and Cancel buttons

---

### File: `templates/partials/_variable_list.html`

**Overall Purpose:** Partial template for rendering a list of variables in the Variables panel.

### Key Components:

* Jinja loop over `variables` to generate `<div>` entries with labels and inputs
* Data attributes for variable names and references for front-end binding

---

## Static Assets

### CSS (`static/css`)

* **`base.css`**: Global reset and foundational styles
* **`style.css`**: Main layout, typography, and common component overrides
* **`components/`**: Per-component styles (e.g., `terminal_area.css`, `notes_panel.css`, `playbook_panel.css`, `variables_panel.css`, `modal.css`, etc.)
* **`themes/`**: Theme files (e.g., `digital-rain.css`, `outrun-sunset.css`, `corporate-dystopia.css`, `holographic.css`, `tokyo-night.css`, `amber-interface.css`)

### JavaScript (`static/js`)

* **`main.js`**: ES6 module entry point; initializes Socket.IO, binds UI event handlers, coordinates API and sync modules
* **`script.js`**: Legacy bundle with older UI logic (candidates for refactor/removal)
* **`utils.js`**: Utility functions (DOM helpers, formatters, storage abstractions)
* **`api/`**: Modules wrapping AJAX calls for each backend endpoint (`notes_api.js`, `playbook_api.js`, `variable_api.js`, `terminal_api.js`, `sync_api.js`)
* **`ui/`**: UI component modules (e.g., `terminal_component.js`, `notes_component.js`, `variable_component.js`, `playbook_component.js`)
* **`sync/`**: Modules handling real-time events from Socket.IO and updating UI accordingly

---

## Repository Metadata and Configuration Files

### File: `.gitignore`

**Overall Purpose:** Specifies files and directories to ignore in Git version control (e.g., `__pycache__`, `logs/`, `data/`).

### File: `CHANGELOG.md`

**Overall Purpose:** Chronicles application changes, bug fixes, and version history.

### File: `LICENSE`

**Overall Purpose:** Contains the project’s software license (MIT License).

### File: `README.md`

**Overall Purpose:** Provides project overview, features, installation instructions, and usage guide.

### File: `requirements.txt`

**Overall Purpose:** Lists Python dependencies with pinned versions for reproducible environments.

### File: `commandwave_theme.tmux.conf`

**Overall Purpose:** Custom tmux configuration file matching the application’s cyberpunk theme.

### Files: `apply_theme_7683.sh`, `apply_theme_7684.sh`

**Overall Purpose:** Shell scripts to apply the custom tmux theme to active sessions on ports 7683 and 7684.

### File: `ffuf_results.json`

**Overall Purpose:** Sample JSON output from `ffuf` fuzzing tool, used for security testing or examples.

### Directory: `.github/workflows`

**Overall Purpose:** Defines GitHub Actions CI workflows for building, testing, and linting the project.

---

## Routes

### File: `routes/variable_routes.py`

**Overall Purpose:** Flask Blueprint for per-tab variable management, providing persistent storage and CRUD HTTP API.

#### Key Components:

* **get_variable_filename**: Generates a safe JSON filename for a tab (lines 26–30).
* **load_tab_variables**: Loads variables from disk if existing (32–41).
* **save_tab_variables**: Persists variable dict to disk (43–52).
* **get_tab_variables**: Retrieves in-memory or loads from disk (54–58).
* **create_variable**: POST /api/variables/create/<tab_id> – Create and save new variable (60–97).
* **update_variable**: POST /api/variables/update/<tab_id> – Rename/update variable data (99–137).
* **delete_variable**: POST /api/variables/delete/<tab_id> – Remove variable entry (139–169).
* **list_variables**: GET /api/variables/list/<tab_id> – List saved variables with HTML snippet (171–201).
* **list_variables_direct**: GET /api/variables/list-direct/<tab_id> – Direct list for routing workarounds (203–206).
* **load_variables**: GET /api/variables/load/<tab_id> – Return simplified name:value pairs (208–228).
* **Legacy Endpoints**: create/update/delete/list without tab for default (‘default’) tab (231–249).
* **catch_all_route**: Debug catch-all for unmatched variable routes (252–259).

### File: `routes/sync_routes.py`

**Overall Purpose:** Flask Blueprint plus Socket.IO event registration for real-time sync: terminals, playbooks, variables, and notes.

#### Key Components:

* **init_socketio_events**: Registers all Socket.IO handlers on app start (25–493).
* **handle_connect** & **handle_disconnect**: Track client sessions, broadcast client list (28–82).
* **handle_join_terminal** & **handle_leave_terminal**: Manage terminal room membership and presence updates (84–157).
* **handle_terminal_created**, **handle_terminal_renamed**, **handle_terminal_closed**: Broadcast terminal lifecycle events (159–218).
* **handle_playbook_updated**, **handle_notes_updated**, **handle_playbook_list_update_request**: Broadcast content updates (220–316).
* **handle_editing_started** & **handle_editing_stopped**: Lock/unlock collaborative edits (318–429).
* **handle_client_ping**: Respond with server_pong (431–436).
* **handle_variable_update_request**: Persist & emit variable changes (438–468).
* **handle_code_block_updated**: Emit granular code block edits (470–491).
* **get_clients**: GET /api/sync/clients – List all connected clients (496–503).
* **get_terminal_clients**: GET /api/sync/terminals/<terminal_id>/clients – Clients by terminal (506–514).

### File: `routes/notes_routes.py`

**Overall Purpose:** Flask Blueprint for global and tab-specific notes persistence via HTTP.

#### Key Components:

* **handle_global_notes**: GET/POST /notes/global – Load or save shared notes in notes_data/ (554–589).
* **handle_tab_notes**: GET/POST /notes/<terminal_id> – Load or save per-tab notes (591–631).

### File: `routes/terminal_routes.py`

**Overall Purpose:** Flask Blueprint to create, rename, delete, and send commands to ttyd/tmux terminal sessions.

#### Key Components:

* **list_terminals**: GET /terminals – List active terminal sessions (384–400).
* **new_terminal**: POST /terminals – Create a new terminal and start ttyd (402–452).
* **send_keys**: POST /terminals/<port>/keys – Inject keystrokes into tmux session (454–483).
* **delete_terminal**: DELETE /terminals/<port> – Kill ttyd process and tmux session (485–516).
* **delete_terminal_post**: POST /terminals/<port>/delete – Legacy delete endpoint (518–521).
* **rename_terminal**: POST /terminals/<port>/rename – Rename session and update notes file (523–551).

---

## Refactoring & Legacy Components

* **static/js/script.js**: Legacy UI bundle; core logic has moved to `js/main.js` and modular components. Candidate for removal or replacement.
* **core/config.py**: Empty scaffold removed; verify no future configuration entries are needed.
* **apply_theme_*.sh scripts**: Simple wrappers for tmux theming; consider integrating theme application into a CLI command or UI toggle.
* **ffuf_results.json**: Sample fuzzing output; archive or remove if not used in documentation or testing.

## Summary

This document covers all major parts of the CommandWave application:

* Core modules (`core/`) for playbook parsing, sync, and notes storage.  
* Entry point (`main.py`) for app setup and lifecycle management.  
* Flask routes (`routes/`) for terminals, variables, playbooks, sync, and notes.  
* Templates (`templates/`) and partials for UI structure and modals.  
* Static assets (`static/`) including CSS themes, JS modules, and images.  
* Directories and configuration files for persistent storage and CI.  
* Identified refactoring candidates and legacy code for future cleanup.

---

## Appendix: Additional Files

### File: `core/__init__.py`
**Overall Purpose:** Python package initializer for the `core` module; currently empty.

### Directory: `playbooks/tutorials/`
**Overall Purpose:** Collection of tutorial markdown playbooks grouped by topic.

### Images (`static/img`)
* **`commandwave-logo.png`**: Main logo used in README and UI.
* **`screenshot.png`**: Demo screenshot for documentation.
* **`favicon.ico`**, **`favicon.png`**: Browser tab icons.

### File: `.github/workflows/pages-deploy.yml`
**Overall Purpose:** GitHub Actions workflow for deploying the docs site to GitHub Pages.

### File: `core/notes_storage.py`

**Overall Purpose:** Persistent storage for global and terminal-specific notes, including saving, loading, listing, and renaming note files.

#### Key Components:

* **get_global_notes_path**: Returns the filepath for the global notes.
* **get_terminal_notes_path**: Returns the filepath for a terminal-specific notes file.
* **save_global_notes**: Writes global notes content to disk.
* **load_global_notes**: Reads global notes content from disk.
* **save_terminal_notes**: Writes notes for a specific terminal.
* **load_terminal_notes**: Reads notes for a specific terminal.
* **list_global_notes**: Lists available global notes entries.
* **list_terminal_notes**: Lists note files by terminal.
* **rename_terminal_notes_file**: Renames a terminal notes file when a session is renamed.

### File: `.nojekyll`

**Overall Purpose:** Prevents Jekyll processing on GitHub Pages, ensuring directories/files starting with `_` are published.

### File: `docs/index.html`

**Overall Purpose:** The compiled HTML entry point for the Jekyll-based documentation site.

### File: `docs/index.md`

**Overall Purpose:** Markdown source for the documentation site's home page.

### Directory: `docs/css/`

**Overall Purpose:** Stylesheets for the docs site, including main layout and themes.

### File: `docs/css/main.css`

**Overall Purpose:** Main stylesheet for the docs site (layout, typography).

### Directory: `docs/css/components/`

**Overall Purpose:** Component-specific styles for the docs site (e.g., terminal demo).

### Directory: `docs/css/themes/`

**Overall Purpose:** Theme CSS files for the docs site styling.

### Directory: `docs/js/`

**Overall Purpose:** JavaScript assets for the docs site interactivity.

### File: `docs/js/main.js`

**Overall Purpose:** Main script for docs site functionality.

### Directory: `docs/js/components/`

**Overall Purpose:** Modular JavaScript components for the docs site (hero, terminal demo).

### File: `docs/js/components/hero.js`

**Overall Purpose:** Controls hero section animations and interactions.

### File: `docs/js/components/terminal_demo.js`

**Overall Purpose:** Powers the interactive terminal demo on the docs site.

### Directory: `docs/partials/`

**Overall Purpose:** HTML partial templates included in the docs site.

### Directory: `docs/images/`

**Overall Purpose:** Image assets for the docs site (logos, screenshots, icons).

### Directories: `__pycache__`

**Overall Purpose:** Python bytecode cache directories, auto-generated and typically ignored.

### File: `docs/README.md`

**Overall Purpose:** Provides overview and instructions specific to the Jekyll-based documentation site.

### Files: `docs/favicon.ico`, `docs/favicon.png`

**Overall Purpose:** Browser tab icons for the documentation site.

---

## Directory: `docs/`

**Overall Purpose:** Source and build artifacts for the Jekyll-based documentation site.

#### Key Entries:

* **File: `.nojekyll`**: Prevents Jekyll processing on GitHub Pages.
* **File: `README.md`**: Overview and instructions for the docs site.
* **File: `index.html`**: Compiled HTML home page for documentation.
* **File: `index.md`**: Markdown source for the docs home page.
*
* **Directory: `css/`**
  * **File: `main.css`**: Main stylesheet (layout, typography).
  * **Directory: `components/`**
    * **File: `terminal_demo.css`**: Styles for terminal demo component.
  * **Directory: `themes/`**
    * **File: `amber-interface.css`**
    * **File: `corporate-dystopia.css`**
    * **File: `cyberpunk-dark.css`**
    * **File: `digital-rain.css`**
    * **File: `holographic.css`**
    * **File: `light.css`**
    * **File: `outrun-sunset.css`**
    * **File: `tokyo-night.css`**
    * **File: `witchhazel.css`**

* **Directory: `js/`**
  * **File: `main.js`**: Main script for docs site interactivity.
  * **Directory: `components/`**
    * **File: `hero.js`**: Hero section animations.
    * **File: `terminal_demo.js`**: Interactive terminal demo logic.

* **Directory: `partials/`**: HTML partial templates for docs.
* **Directory: `images/`**: Image assets (logos, screenshots, icons).
* **File: `favicon.ico`**, **`favicon.png`**: Browser tab icons for docs.
---
