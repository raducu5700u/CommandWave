#!/usr/bin/env python3
"""
CommandWave - Web-based interface for managing terminal sessions with playbooks
"""

import os
import sys
import json
import signal
import atexit
import logging
import argparse
import subprocess
import threading
import glob
import socket
import time
import re
from urllib.parse import quote
from flask import Flask, render_template, request, jsonify, abort, send_from_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), 
              logging.FileHandler(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'commandwave.log'))],
)
logger = logging.getLogger('commandwave')

# Constants
DEFAULT_PORT = 5000
DEFAULT_TERMINAL_PORT = 7681
TERMINAL_PORT_RANGE = (7682, 7781)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(BASE_DIR, 'notes_data')
PLAYBOOKS_DIR = os.path.join(BASE_DIR, 'playbooks')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
TMUX_CONFIG_PATH = os.path.join(BASE_DIR, 'commandwave_theme.tmux.conf')

# Create necessary directories if they don't exist
os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(PLAYBOOKS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(__name__, 
            static_folder=STATIC_DIR, 
            template_folder=TEMPLATES_DIR)

# Store information about running terminals
terminals = {}
process_lock = threading.Lock()

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='CommandWave - Terminal Management Web Application')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'Port to run the web server on (default: {DEFAULT_PORT})')
    parser.add_argument('--use-default-tmux-config', action='store_true',
                        help='Use the default CommandWave tmux configuration')
    return parser.parse_args()

def is_port_available(port):
    """Check if a port is available to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) != 0

def find_available_port(start_port, end_port):
    """Find an available port in the specified range."""
    for port in range(start_port, end_port + 1):
        if is_port_available(port) and port not in terminals:
            return port
    return None

def start_ttyd_process(port, tmux_session_name, use_tmux_config=False):
    """Start a ttyd process linked to a tmux session on the specified port."""
    try:
        # First check if the port is actually available
        if not is_port_available(port):
            logger.warning(f"Port {port} is already in use, trying to find an available port")
            new_port = find_available_port(TERMINAL_PORT_RANGE[0], TERMINAL_PORT_RANGE[1])
            if new_port:
                logger.info(f"Found available port {new_port}, using it instead of {port}")
                port = new_port
            else:
                logger.error("Could not find an available port for ttyd")
                return None
                
        # Check if tmux session already exists
        check_session = subprocess.run(
            ['tmux', 'has-session', '-t', tmux_session_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False
        )
        
        # If session exists, use it
        if check_session.returncode == 0:
            logger.info(f"Tmux session {tmux_session_name} already exists, reusing it")
            # If using custom config, source it in the existing session
            if use_tmux_config and os.path.exists(TMUX_CONFIG_PATH):
                try:
                    subprocess.run(
                        ['tmux', 'source-file', '-t', tmux_session_name, TMUX_CONFIG_PATH],
                        check=True
                    )
                    logger.info(f"Applied custom tmux config to existing session {tmux_session_name}")
                except Exception as e:
                    logger.warning(f"Failed to apply tmux config to existing session: {e}")
        else:
            # Create a new tmux session
            tmux_cmd = ['tmux', 'new-session', '-d', '-s', tmux_session_name]
            
            # Add tmux config if enabled
            if use_tmux_config and os.path.exists(TMUX_CONFIG_PATH):
                tmux_cmd.extend(['-f', TMUX_CONFIG_PATH])
                logger.info(f"Creating new tmux session with config: {TMUX_CONFIG_PATH}")
                
            subprocess.run(tmux_cmd, check=True)
            logger.info(f"Created tmux session: {tmux_session_name}")
        
        # Start ttyd linked to the tmux session
        ttyd_cmd = [
            'ttyd', 
            '-W',  # Add writable flag to enable terminal input
            '--port', str(port), 
        ]
        
        # Create helper script for tmux attachment that applies theme
        theme_script_path = os.path.join(BASE_DIR, f'apply_theme_{port}.sh')
        
        with open(theme_script_path, 'w') as f:
            if use_tmux_config and os.path.exists(TMUX_CONFIG_PATH):
                # Script that sources the config before attaching
                f.write('#!/bin/sh\n')
                f.write(f'tmux source-file "{TMUX_CONFIG_PATH}"\n')
                f.write(f'tmux attach-session -t {tmux_session_name}\n')
                logger.info(f"Created tmux helper script with theme at {theme_script_path}")
                os.chmod(theme_script_path, 0o755)  # Make executable
                ttyd_cmd.append(theme_script_path)
            else:
                # Standard attachment without theme
                ttyd_cmd.extend(['tmux', 'attach-session', '-t', tmux_session_name])
            
        # Start the ttyd process
        ttyd_process = subprocess.Popen(
            ttyd_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment to ensure the process starts
        time.sleep(0.5)
        
        # Check if process is still running (didn't exit with error)
        if ttyd_process.poll() is not None:
            # Process has exited, get error output
            _, stderr = ttyd_process.communicate()
            logger.error(f"ttyd process exited unexpectedly: {stderr}")
            return None
            
        logger.info(f"Started ttyd on port {port} linked to tmux session {tmux_session_name}")
        return ttyd_process
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start ttyd process: {e}")
        return None
    except Exception as e:
        logger.error(f"Error starting ttyd process: {e}")
        return None

def send_keys_to_tmux(tmux_session_name, keys):
    """Send keys to a tmux session."""
    try:
        # Ensure keys end with a newline if not already present
        if not keys.endswith('\n'):
            keys += '\n'
            
        # Send keys to the tmux session
        subprocess.run(
            ['tmux', 'send-keys', '-t', tmux_session_name, keys],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to send keys to tmux session {tmux_session_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending keys to tmux session {tmux_session_name}: {e}")
        return False

def kill_terminal(port):
    """Kill a ttyd process and its associated tmux session."""
    if port not in terminals:
        return False
        
    with process_lock:
        try:
            terminal_info = terminals[port]
            
            # Kill the ttyd process
            if terminal_info['process'] and terminal_info['process'].poll() is None:
                terminal_info['process'].terminate()
                terminal_info['process'].wait(timeout=3)
                logger.info(f"Terminated ttyd process for port {port}")
                
            # Kill the tmux session
            subprocess.run(
                ['tmux', 'kill-session', '-t', terminal_info['tmux_session']],
                check=True
            )
            logger.info(f"Killed tmux session {terminal_info['tmux_session']}")
            
            # Clean up the helper script if it exists
            theme_script_path = os.path.join(BASE_DIR, f'apply_theme_{port}.sh')
            if os.path.exists(theme_script_path):
                try:
                    os.remove(theme_script_path)
                    logger.info(f"Removed helper script: {theme_script_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove helper script {theme_script_path}: {e}")
            
            # Remove from terminals dict
            del terminals[port]
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to kill tmux session: {e}")
            return False
        except Exception as e:
            logger.error(f"Error killing terminal on port {port}: {e}")
            return False

def cleanup_all_terminals():
    """Clean up all terminal processes when the application exits."""
    logger.info("Cleaning up all terminal processes...")
    
    # Make a copy of the keys since we'll be modifying the dictionary
    ports = list(terminals.keys())
    
    for port in ports:
        kill_terminal(port)
        
    logger.info("Cleanup complete")

# Register cleanup function
atexit.register(cleanup_all_terminals)

# Handle signals
def signal_handler(sig, frame):
    """Handle termination signals by cleaning up and exiting."""
    logger.info(f"Received signal {sig}, shutting down...")
    cleanup_all_terminals()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Basic routes
@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html', default_terminal_port=app.config.get('DEFAULT_TERMINAL_PORT', DEFAULT_TERMINAL_PORT))

@app.route('/healthcheck')
def healthcheck():
    """Simple health check endpoint."""
    return jsonify({'status': 'ok'})

@app.route('/api/playbooks/<path:filepath>', methods=['GET'])
def get_playbook_file(filepath):
    """Get a playbook file from any subdirectory within the playbooks directory."""
    # Secure the filepath to prevent directory traversal
    # Ensure the requested file is within the playbooks directory
    abs_path = os.path.abspath(os.path.join(PLAYBOOKS_DIR, filepath))
    if not abs_path.startswith(os.path.abspath(PLAYBOOKS_DIR)):
        return jsonify({
            'success': False,
            'error': 'Invalid file path'
        }), 400
    
    # Check if the file exists
    if not os.path.exists(abs_path) or not os.path.isfile(abs_path):
        return jsonify({
            'success': False,
            'error': f'File not found: {filepath}'
        }), 404
    
    # Check if it's a markdown file
    if not abs_path.lower().endswith('.md'):
        return jsonify({
            'success': False,
            'error': 'Only .md files are supported'
        }), 400
    
    # Read the file content
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'filename': os.path.basename(filepath),
            'content': content
        })
    except Exception as e:
        logger.error(f"Error loading playbook {abs_path}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Terminal management endpoints
@app.route('/api/terminals/new', methods=['GET'])
def new_terminal():
    """Create a new terminal session and return its port."""
    try:
        # Find an available port
        port = find_available_port(TERMINAL_PORT_RANGE[0], TERMINAL_PORT_RANGE[1])
        
        if not port:
            return jsonify({
                'success': False,
                'error': 'No available ports'
            }), 503
        
        # Generate a unique session name
        session_name = f'commandwave-{port}'
        
        # Start ttyd process
        process = start_ttyd_process(port, session_name, parse_arguments().use_default_tmux_config)
        
        if not process:
            return jsonify({
                'success': False,
                'error': 'Failed to start terminal process'
            }), 500
        
        # Store process info
        with process_lock:
            terminals[port] = {
                'process': process,
                'tmux_session': session_name,
                'created_at': time.time()
            }
        
        return jsonify({
            'success': True,
            'port': port
        })
        
    except Exception as e:
        logger.error(f"Error creating new terminal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/terminals/sendkeys', methods=['POST'])
def send_keys():
    """Send keys to a specific terminal session."""
    data = request.json
    
    if not data or 'port' not in data or 'keys' not in data:
        return jsonify({
            'success': False,
            'error': 'Missing required fields: port, keys'
        }), 400
    
    port = int(data['port'])
    keys = data['keys']
    
    if port not in terminals:
        return jsonify({
            'success': False,
            'error': f'Terminal on port {port} not found'
        }), 404
    
    tmux_session = terminals[port]['tmux_session']
    
    # Send the keys to the tmux session
    if send_keys_to_tmux(tmux_session, keys):
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': f'Failed to send keys to terminal on port {port}'
        }), 500

@app.route('/api/terminals/<int:port>', methods=['DELETE'])
def delete_terminal(port):
    """Terminate a terminal session."""
    # Don't allow deleting the default terminal
    if port == app.config.get('DEFAULT_TERMINAL_PORT', DEFAULT_TERMINAL_PORT):
        return jsonify({
            'success': False,
            'error': 'Cannot delete the main terminal'
        }), 403
    
    if port not in terminals:
        return jsonify({
            'success': False,
            'error': f'Terminal on port {port} not found'
        }), 404
    
    # Kill the terminal
    if kill_terminal(port):
        return jsonify({'success': True})
    else:
        return jsonify({
            'success': False,
            'error': f'Failed to delete terminal on port {port}'
        }), 500

# Notes persistence endpoints
@app.route('/api/notes/global', methods=['GET', 'POST'])
def handle_global_notes():
    """Handle GET and POST requests for global notes."""
    notes_file = os.path.join(NOTES_DIR, 'global_notes.txt')
    
    if request.method == 'GET':
        # Read global notes from file
        try:
            if os.path.exists(notes_file):
                with open(notes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'success': True, 'content': content})
            else:
                # Return empty content if file doesn't exist
                return jsonify({'success': True, 'content': ''})
        except Exception as e:
            logger.error(f"Error reading global notes: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        # Write global notes to file
        try:
            data = request.json
            if not data or 'content' not in data:
                return jsonify({
                    'success': False, 
                    'error': 'Missing required field: content'
                }), 400
                
            os.makedirs(NOTES_DIR, exist_ok=True)
            with open(notes_file, 'w', encoding='utf-8') as f:
                f.write(data['content'])
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error writing global notes: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/notes/tab/<terminal_id>', methods=['GET', 'POST'])
def handle_tab_notes(terminal_id):
    """Handle GET and POST requests for tab-specific notes."""
    # Sanitize terminal_id to prevent directory traversal
    sanitized_id = re.sub(r'[^a-zA-Z0-9\-]', '', terminal_id)
    if sanitized_id != terminal_id:
        return jsonify({'success': False, 'error': 'Invalid terminal ID'}), 400
        
    notes_file = os.path.join(NOTES_DIR, f'tab_notes_{sanitized_id}.txt')
    
    if request.method == 'GET':
        # Read tab notes from file
        try:
            if os.path.exists(notes_file):
                with open(notes_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                return jsonify({'success': True, 'content': content})
            else:
                # Return empty content if file doesn't exist
                return jsonify({'success': True, 'content': ''})
        except Exception as e:
            logger.error(f"Error reading tab notes for {terminal_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        # Write tab notes to file
        try:
            data = request.json
            if not data or 'content' not in data:
                return jsonify({
                    'success': False, 
                    'error': 'Missing required field: content'
                }), 400
                
            os.makedirs(NOTES_DIR, exist_ok=True)
            with open(notes_file, 'w', encoding='utf-8') as f:
                f.write(data['content'])
            return jsonify({'success': True})
        except Exception as e:
            logger.error(f"Error writing tab notes for {terminal_id}: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

# Playbook search and load endpoints
@app.route('/api/playbooks/search', methods=['GET'])
def search_playbooks():
    """Search for lines in playbooks containing the query."""
    query = request.args.get('query', '')
    if not query:
        return jsonify({
            'success': False,
            'error': 'Missing query parameter'
        }), 400
    
    # Search in all .md files in the playbooks directory
    results = []
    try:
        # Create the playbooks directory if it doesn't exist
        os.makedirs(PLAYBOOKS_DIR, exist_ok=True)
        
        # Get all .md files in the playbooks directory
        md_files = glob.glob(os.path.join(PLAYBOOKS_DIR, '**/*.md'), recursive=True)
        
        for file_path in md_files:
            filename = os.path.basename(file_path)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if query.lower() in line.lower():
                            results.append({
                                'filename': filename,
                                'line_number': i,
                                'line': line.strip()
                            })
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")
                continue
                
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        logger.error(f"Error searching playbooks: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/playbooks/load/<path:filename>', methods=['GET'])
def load_playbook(filename):
    """Load a specific playbook file."""
    # Sanitize the filename to prevent directory traversal
    sanitized_filename = os.path.basename(filename)
    if sanitized_filename != filename:
        return jsonify({
            'success': False,
            'error': 'Invalid filename'
        }), 400
    
    file_path = os.path.join(PLAYBOOKS_DIR, sanitized_filename)
    
    # Check if the file exists
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return jsonify({
            'success': False,
            'error': f'File not found: {sanitized_filename}'
        }), 404
    
    # Check if the file has .md extension
    if not file_path.endswith('.md'):
        return jsonify({
            'success': False,
            'error': 'Only .md files are supported'
        }), 400
    
    # Read the file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'success': True,
            'filename': sanitized_filename,
            'content': content
        })
    except Exception as e:
        logger.error(f"Error loading playbook {file_path}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Main entry point
if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        args = parse_arguments()
        logger.info(f"Starting CommandWave on port {args.port}")
        
        # Check if default terminal port is available, try alternative if needed
        initial_port = DEFAULT_TERMINAL_PORT
        if not is_port_available(initial_port):
            logger.warning(f"Default terminal port {initial_port} is already in use, finding an alternative")
            initial_port = find_available_port(TERMINAL_PORT_RANGE[0], TERMINAL_PORT_RANGE[1])
            if not initial_port:
                logger.error("Could not find an available port for the initial terminal")
                sys.exit(1)
            logger.info(f"Using alternative port {initial_port} for initial terminal")
        
        # Create initial terminal
        main_tmux_session = "commandwave-main"
        main_terminal_process = start_ttyd_process(
            initial_port, 
            main_tmux_session,
            args.use_default_tmux_config
        )
        
        if main_terminal_process:
            logger.info(f"Started main terminal on port {initial_port}")
            
            # Store information about this terminal
            with process_lock:
                terminals[initial_port] = {
                    'process': main_terminal_process,
                    'tmux_session': main_tmux_session,
                    'created_at': time.time()
                }
            
            # Set the default terminal port for the template
            app.config['DEFAULT_TERMINAL_PORT'] = initial_port
            
            # Start Flask app
            app.run(host='0.0.0.0', port=args.port, debug=False, use_reloader=False)
        else:
            logger.error("Failed to start initial terminal. Check if ttyd and tmux are installed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        cleanup_all_terminals()
