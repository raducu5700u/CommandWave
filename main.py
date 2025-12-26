#!/usr/bin/env python3
"""
CommandWave - Web-based interface for managing terminal sessions with playbooks
"""

import os
import sys
import signal
import atexit
import logging
import argparse
import time
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO

# Import core modules
import core.terminal_manager as terminal_manager
from core.sync_utils import init_socketio

# Import route blueprints
from routes.playbook_routes import playbook_routes
from routes.variable_routes import variable_routes
from routes.terminal_routes import terminal_routes
from routes.sync_routes import sync_routes, init_socketio_events
from routes.notes_routes import notes_routes

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
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NOTES_DIR = os.path.join(BASE_DIR, 'notes_data')
PLAYBOOKS_DIR = os.path.join(BASE_DIR, 'playbooks')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
HOSTNAME = 'localhost'  # Default hostname, will be updated from args

# Create necessary directories if they don't exist
os.makedirs(NOTES_DIR, exist_ok=True)
os.makedirs(PLAYBOOKS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(__name__, 
            static_folder=STATIC_DIR, 
            template_folder=TEMPLATES_DIR)

# Register cleanup function
atexit.register(terminal_manager.cleanup_all_terminals)

# Flag to prevent multiple signal handler executions
_shutdown_in_progress = False

def signal_handler(sig, frame):
    """Handle termination signals by cleaning up and exiting."""
    global _shutdown_in_progress
    
    # Prevent multiple executions of the shutdown sequence
    if _shutdown_in_progress:
        return
    
    _shutdown_in_progress = True
    logger.info(f"Received signal {sig}, shutting down...")
    terminal_manager.cleanup_all_terminals()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Register blueprints
app.register_blueprint(playbook_routes)
app.register_blueprint(variable_routes)
app.register_blueprint(terminal_routes)
app.register_blueprint(sync_routes)
app.register_blueprint(notes_routes)

# Initialize SocketIO
socketio = init_socketio(app)
init_socketio_events(socketio)


# Basic routes
@app.route('/')
def index():
    """Render the main application page."""
    return render_template('index.html', 
                          default_terminal_port=app.config.get('DEFAULT_TERMINAL_PORT', DEFAULT_TERMINAL_PORT),
                          hostname=app.config.get('HOSTNAME', HOSTNAME))

@app.route('/healthcheck')
def healthcheck():
    """Simple health check endpoint."""
    return jsonify({'status': 'ok'})

@app.route('/api/playbooks/<path:filepath>', methods=['GET'])
def get_playbook_file(filepath):
    """Get a playbook file from any subdirectory within the playbooks directory."""
    # Secure the filepath to prevent directory traversal
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

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='CommandWave - Terminal Management Web Application')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'Port to run the web server on (default: {DEFAULT_PORT})')
    parser.add_argument('--use-default-tmux-config', action='store_true',
                        help='Use the default CommandWave tmux configuration')
    parser.add_argument('--hostname', type=str, default='localhost',
                        help='Hostname to use for terminal connections (default: localhost)')
    parser.add_argument('--remote', action='store_true',
                        help='Enable remote access by binding to all interfaces')
    return parser.parse_args()

# Main entry point
if __name__ == '__main__':
    try:
        args = parse_arguments()
        logger.info(f"Starting CommandWave on port {args.port}")
        
        # Update hostname from command-line arguments
        HOSTNAME = args.hostname
        # Update in terminal_manager as well to ensure it knows the hostname
        # (Though checks usually use localhost for local port checks, but good to be consistent if needed)
        
        logger.info(f"Using hostname: {HOSTNAME}")
        
        # Set the hostname in Flask app config for template access
        app.config['HOSTNAME'] = HOSTNAME
        
        # Check if default terminal port is available, try alternative if needed
        initial_port = DEFAULT_TERMINAL_PORT
        if not terminal_manager.is_port_available(initial_port):
            logger.warning(f"Default terminal port {initial_port} is already in use, finding an alternative")
            initial_port = terminal_manager.find_available_port(
                terminal_manager.TERMINAL_PORT_RANGE[0], 
                terminal_manager.TERMINAL_PORT_RANGE[1]
            )
            if not initial_port:
                logger.error("Could not find an available port for the initial terminal")
                sys.exit(1)
            logger.info(f"Using alternative port {initial_port} for initial terminal")
        
        # Create initial terminal
        main_tmux_session = "commandwave-main"
        main_terminal_process = terminal_manager.start_ttyd_process(
            initial_port, 
            main_tmux_session,
            args.use_default_tmux_config
        )
        
        if main_terminal_process:
            logger.info(f"Started main terminal on port {initial_port}")
            
            # Store information about this terminal in the manager
            with terminal_manager.process_lock:
                terminal_manager.terminals[initial_port] = {
                    'process': main_terminal_process,
                    'tmux_session': main_tmux_session,
                    'created_at': time.time(),
                    'name': 'Main Terminal'
                }
            
            # Set the default terminal port for the template
            app.config['DEFAULT_TERMINAL_PORT'] = initial_port
            
            # Start Flask app with SocketIO
            host = '0.0.0.0' if args.remote else '127.0.0.1'
            
            # Use socketio.run instead of app.run
            socketio.run(app, host=host, port=args.port, debug=False, allow_unsafe_werkzeug=True)
        else:
            logger.error("Failed to start initial terminal. Check if ttyd and tmux are installed.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting application: {e}")
        terminal_manager.cleanup_all_terminals()
