"""
routes/terminal_routes.py
Flask Blueprint for terminal-related API endpoints.
"""

from flask import Blueprint, request, jsonify
import logging
import core.terminal_manager as terminal_manager

# Configure logging
logger = logging.getLogger('commandwave')

# Create blueprint
terminal_routes = Blueprint('terminal_routes', __name__, url_prefix='/api/terminals')

@terminal_routes.route('/new', methods=['POST'])
def create_terminal():
    """Create a new terminal session and return its port."""
    try:
        # Get terminal name from request
        data = request.get_json()
        tab_name = data.get('name', 'Terminal')
        
        # Find an available port
        port = terminal_manager.find_available_port(
            terminal_manager.TERMINAL_PORT_RANGE[0], 
            terminal_manager.TERMINAL_PORT_RANGE[1]
        )
        
        if not port:
            logger.error("Could not find available port for new terminal")
            return jsonify({
                'success': False,
                'error': 'No available ports'
            }), 500
            
        # Create new tmux session name
        tmux_session = f"commandwave-{port}"
        
        # Determine if we should use tmux config (could be passed in app config or default)
        # For now, defaulting to True if it exists, similar to original logic logic
        use_tmux_config = True
        
        terminal_process = terminal_manager.start_ttyd_process(port, tmux_session, use_tmux_config)
        
        if terminal_process:
            # Store information about this terminal
            import time
            with terminal_manager.process_lock:
                terminal_manager.terminals[port] = {
                    'process': terminal_process,
                    'tmux_session': tmux_session,
                    'created_at': time.time(),
                    'name': tab_name
                }
                
            logger.info(f"Created new terminal on port {port} with name '{tab_name}'")
            return jsonify({
                'success': True,
                'port': port,
                'name': tab_name
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create terminal process'
            }), 500
            
    except Exception as e:
        logger.error(f"Error creating new terminal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_routes.route('/rename/<int:port>', methods=['POST'])
def rename_terminal(port):
    """Rename a terminal session."""
    try:
        # Check if the terminal exists
        if port not in terminal_manager.terminals:
            return jsonify({
                'success': False,
                'error': 'Terminal not found'
            }), 404
        
        # Get the new name from the request
        data = request.get_json()
        new_name = data.get('name', f'Terminal {port}')
        
        # Update the terminal name
        with terminal_manager.process_lock:
            terminal_manager.terminals[port]['name'] = new_name
            
        logger.info(f"Renamed terminal on port {port} to '{new_name}'")
        return jsonify({
            'success': True
        })
    except Exception as e:
        logger.error(f"Error renaming terminal: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_routes.route('/delete/<int:port>', methods=['POST'])
def delete_terminal_post(port):
    """Terminate a terminal session (POST endpoint)."""
    return delete_terminal(port)

@terminal_routes.route('/<int:port>', methods=['DELETE'])
def delete_terminal(port):
    """Terminate a terminal session."""
    try:
        # Check if the terminal exists
        if port not in terminal_manager.terminals:
            return jsonify({
                'success': False,
                'error': 'Terminal not found'
            }), 404
            
        # Kill the terminal
        if terminal_manager.kill_terminal(port):
            logger.info(f"Deleted terminal on port {port}")
            return jsonify({
                'success': True
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to delete terminal on port {port}'
            }), 500
    except Exception as e:
        logger.error(f"Error deleting terminal on port {port}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@terminal_routes.route('/list', methods=['GET'])
def list_terminals():
    """Get a list of all active terminals."""
    terminal_list = []
    with terminal_manager.process_lock:
        for port, terminal in terminal_manager.terminals.items():
            terminal_list.append({
                'port': port,
                'name': terminal.get('name', f'Terminal {port}'),
                'tmux_session': terminal.get('tmux_session', ''),
                'created_at': terminal.get('created_at', 0)
            })
    
    return jsonify({
        'success': True,
        'terminals': terminal_list
    })

@terminal_routes.route('/send-command', methods=['POST'])
def send_command():
    """Send a command to a terminal."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        port = data.get('port')
        command = data.get('command')
        
        if not port:
            return jsonify({'success': False, 'error': 'No port specified'}), 400
        
        if not command:
            return jsonify({'success': False, 'error': 'No command specified'}), 400
        
        logger.info(f"Sending command to terminal {port}")
        
        # Convert port to int for dictionary lookup
        try:
            port_int = int(port)
        except ValueError:
             return jsonify({'success': False, 'error': 'Invalid port format'}), 400
        
        terminal_info = None
        if port_int in terminal_manager.terminals:
            terminal_info = terminal_manager.terminals[port_int]
        
        if not terminal_info or 'tmux_session' not in terminal_info:
            logger.error(f"No terminal information found for port {port}")
            return jsonify({
                'success': False,
                'error': f'No tmux session found for terminal {port}'
            }), 404
            
        tmux_session = terminal_info['tmux_session']
        
        # Use simple send_keys_to_tmux which is now safe/doesn't use shell=True
        # command sent as keys + Enter
        if terminal_manager.send_keys_to_tmux(tmux_session, command + '\n'):
            return jsonify({
                'success': True,
                'message': f'Command sent to terminal {port}'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Failed to send keys to tmux'
            }), 500
        
    except Exception as e:
        logger.exception(f"Error sending command: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
