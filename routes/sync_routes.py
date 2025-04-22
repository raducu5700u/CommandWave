"""
routes/sync_routes.py
WebSocket event handlers for real-time synchronization.
"""

import logging
import json
import time
from typing import Dict, Any, Optional
from flask import Blueprint, request, session
from flask_socketio import emit, join_room, leave_room, disconnect

from core.sync_utils import client_tracker, broadcast_to_terminal, broadcast_global
from routes.variable_routes import get_tab_variables, save_tab_variables
from core.notes_storage import save_global_notes, save_terminal_notes
from core.playbook_utils import save_playbook  # Save playbook content to disk

# Configure logging
logger = logging.getLogger('commandwave')

# Create blueprint - note: this is for HTTP routes, SocketIO events are registered separately
sync_routes = Blueprint('sync_routes', __name__, url_prefix='/api/sync')

# Event handlers will be registered by the init_socketio_events function

def init_socketio_events(socketio):
    """Initialize all SocketIO event handlers."""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle new client connections."""
        client_id = request.sid
        # Get username from query params or session
        username = request.args.get('username', 'Anonymous User')
        
        # Add client to tracker
        client_tracker.add_client(client_id, username)
        
        # Broadcast updated client list to all clients
        broadcast_global('clients_updated', {
            'clients': client_tracker.get_all_clients(),
            'count': len(client_tracker.clients)
        }, include_sender=True)
        
        logger.info(f"Client connected: {client_id} ({username})")
        
        # Respond with initialization data
        emit('connection_established', {
            'client_id': client_id,
            'username': username,
            'timestamp': time.time(),
            'client_count': len(client_tracker.clients),
            'sync_status': 'active'
        })

    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnections."""
        client_id = request.sid
        
        # Get client info before removal
        client_info = client_tracker.clients.get(client_id, {})
        terminal_id = client_info.get('active_terminal')
        
        # Remove client from tracker
        client_tracker.remove_client(client_id)
        
        # If client was in a terminal, notify other clients in that terminal
        if terminal_id:
            broadcast_to_terminal(terminal_id, 'terminal_presence_update', {
                'clients': client_tracker.get_terminal_clients(terminal_id),
                'action': 'leave',
                'client_id': client_id,
                'timestamp': time.time()
            }, include_sender=True)
        
        # Broadcast updated client list to all clients
        broadcast_global('clients_updated', {
            'clients': client_tracker.get_all_clients(),
            'count': len(client_tracker.clients)
        }, include_sender=True)
        
        logger.info(f"Client disconnected: {client_id}")
    
    @socketio.on('join_terminal')
    def handle_join_terminal(data):
        """Handle a client joining a terminal tab."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        
        if not terminal_id:
            logger.warning(f"Invalid terminal ID in join request from {client_id}")
            return
        
        # Update client's active terminal
        client_tracker.update_client_terminal(client_id, terminal_id)
        
        # Join the socket.io room for this terminal
        room_name = f"terminal_{terminal_id}"
        join_room(room_name)
        
        # Get client info
        client_info = client_tracker.clients.get(client_id, {})
        username = client_info.get('username', 'Anonymous')
        
        # Notify other clients in this terminal
        clients_in_terminal = client_tracker.get_terminal_clients(terminal_id)
        broadcast_to_terminal(terminal_id, 'terminal_presence_update', {
            'clients': clients_in_terminal,
            'action': 'join',
            'client_id': client_id,
            'username': username,
            'timestamp': time.time()
        })
        
        logger.info(f"Client {client_id} ({username}) joined terminal {terminal_id}")
        
        # Respond with success and terminal clients
        emit('join_terminal_success', {
            'terminal_id': terminal_id,
            'clients': clients_in_terminal
        })
    
    @socketio.on('leave_terminal')
    def handle_leave_terminal(data):
        """Handle a client leaving a terminal tab."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        
        if not terminal_id:
            logger.warning(f"Invalid terminal ID in leave request from {client_id}")
            return
        
        # Get client info before update
        client_info = client_tracker.clients.get(client_id, {})
        current_terminal = client_info.get('active_terminal')
        
        # Only process if client is actually in this terminal
        if current_terminal != terminal_id:
            return
        
        # Leave the socket.io room for this terminal
        room_name = f"terminal_{terminal_id}"
        leave_room(room_name)
        
        # Update client tracker (set to None)
        client_tracker.update_client_terminal(client_id, None)
        
        # Notify other clients in this terminal
        broadcast_to_terminal(terminal_id, 'terminal_presence_update', {
            'clients': client_tracker.get_terminal_clients(terminal_id),
            'action': 'leave',
            'client_id': client_id,
            'username': client_info.get('username', 'Anonymous'),
            'timestamp': time.time()
        })
        
        logger.info(f"Client {client_id} left terminal {terminal_id}")
    
    @socketio.on('terminal_created')
    def handle_terminal_created(data):
        """Handle notification that a new terminal was created."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        terminal_name = data.get('name', 'New Terminal')
        port = data.get('port')
        
        if not terminal_id or not port:
            logger.warning(f"Invalid terminal data in creation notification from {client_id}")
            return
        
        # Broadcast to all clients
        broadcast_global('terminal_created', {
            'terminal_id': terminal_id,
            'name': terminal_name,
            'port': port,
            'timestamp': time.time()
        })
        
        logger.info(f"Terminal created broadcast: {terminal_id} ({terminal_name})")
    
    @socketio.on('terminal_renamed')
    def handle_terminal_renamed(data):
        """Handle notification that a terminal was renamed."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        new_name = data.get('name')
        
        if not terminal_id or not new_name:
            logger.warning(f"Invalid terminal data in rename notification from {client_id}")
            return
        
        # Broadcast to all clients
        broadcast_global('terminal_renamed', {
            'terminal_id': terminal_id,
            'name': new_name,
            'timestamp': time.time()
        })
        
        logger.info(f"Terminal renamed broadcast: {terminal_id} to {new_name}")
    
    @socketio.on('terminal_closed')
    def handle_terminal_closed(data):
        """Handle notification that a terminal was closed."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        
        if not terminal_id:
            logger.warning(f"Invalid terminal ID in close notification from {client_id}")
            return
        
        # Broadcast to all clients
        broadcast_global('terminal_closed', {
            'terminal_id': terminal_id,
            'port': terminal_id,  # For now, port and terminal_id are equivalent in this context
            'timestamp': time.time()
        })
        
        logger.info(f"Terminal closed broadcast: {terminal_id}")
    
    @socketio.on('playbook_updated')
    def handle_playbook_updated(data):
        """Handle notification that a playbook was updated."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        playbook_name = data.get('name')
        action = data.get('action', 'update')  # load, update, close
        content = data.get('content')
        # Persist content on update
        if action == 'update':
            if content is None:
                logger.warning(f"No content provided for playbook update from {client_id}")
                return
            success, result = save_playbook(playbook_name, content)
            if not success:
                logger.error(f"Failed to save playbook {playbook_name}: {result}")
                emit('playbook_update_response', {'resource_id': f"playbook:{playbook_name}", 'success': False, 'error': result})
                return
            # Reflect saved content for broadcast
            data['content'] = result.get('content', content)
         
        if not terminal_id or not playbook_name:
            logger.warning(f"Invalid playbook data from {client_id}")
            return
        
        # Prepare payload for broadcast
        payload = {
            'terminal_id': terminal_id,
            'name': playbook_name,
            'action': action,
            'timestamp': time.time()
        }
        # Include updated content if provided
        if action == 'update' and data.get('content') is not None:
            payload['content'] = data['content']
        # Broadcast to clients in the same terminal
        broadcast_to_terminal(terminal_id, 'playbook_changed', payload)
        
        logger.info(f"Playbook {action} broadcast: {terminal_id} - {playbook_name}")
    
    @socketio.on('notes_updated')
    def handle_notes_updated(data):
        """Handle notification that notes were updated."""
        client_id = request.sid
        client_info = client_tracker.clients.get(client_id, {})
        username = client_info.get('username', 'Anonymous')
        
        terminal_id = data.get('terminal_id')
        content = data.get('content')
        is_global = data.get('is_global', False)  # Check if these are global notes
        
        # Save notes to disk for persistence
        if is_global or terminal_id == 'global' or terminal_id is None:
            # Save global notes to disk
            save_success = save_global_notes(content)
            if not save_success:
                logger.error("Failed to persist global notes to disk")
                
            logger.info(f"Global notes updated by client {client_id} ({username})")
            # Broadcast global notes update to all clients except sender
            broadcast_global('global_notes_changed', {
                'content': content,
                'sender_id': client_id,
                'username': username,
                'timestamp': time.time()
            }, include_sender=False)
        else:
            # Save terminal notes to disk
            save_success = save_terminal_notes(terminal_id, content)
            if not save_success:
                logger.error(f"Failed to persist notes for terminal {terminal_id} to disk")
                
            logger.info(f"Tab notes updated for terminal {terminal_id} by client {client_id} ({username})")
            # Broadcast tab notes update to clients in the terminal except sender
            broadcast_to_terminal(terminal_id, 'notes_changed', {
                'terminal_id': terminal_id,
                'content': content,
                'sender_id': client_id,
                'username': username,
                'timestamp': time.time()
            }, include_sender=False)
    
    @socketio.on('playbook_list_update_request')
    def handle_playbook_list_update_request(data):
        """Handle notification that the playbook list was updated."""
        action = data.get('action')
        filename = data.get('filename')
        if not action or not filename:
            logger.warning(f"Invalid playbook list update data from {request.sid}")
            return
        # Broadcast to all clients except sender (default include_sender=False skips sender)
        broadcast_global('remote_playbook_list_update', {
            'action': action,
            'filename': filename,
            'timestamp': time.time()
        })
        logger.info(f"Playbook list update broadcast: {action} - {filename}")
    
    @socketio.on('editing_started')
    def handle_editing_started(data):
        """Handle notification that a client started editing a resource."""
        client_id = request.sid
        resource_id = data.get('resource_id')  # Format: "notes:global" or "notes:terminal_123" or "playbook:name.md"
        
        if not resource_id:
            logger.warning(f"Invalid resource ID in editing notification from {client_id}")
            return
        
        # Try to acquire lock
        success = client_tracker.acquire_editing_lock(resource_id, client_id)
        
        if success:
            # Get client info
            client_info = client_tracker.clients.get(client_id, {})
            username = client_info.get('username', 'Anonymous')
            
            # Determine if this is a terminal-specific resource
            is_terminal_resource = 'terminal_' in resource_id
            terminal_id = None
            
            if is_terminal_resource:
                # Extract terminal ID from resource ID
                parts = resource_id.split('terminal_')
                if len(parts) > 1:
                    terminal_id = 'terminal_' + parts[1].split(':')[0]
            
            # Broadcast based on resource scope
            if terminal_id:
                broadcast_to_terminal(terminal_id, 'resource_lock_changed', {
                    'resource_id': resource_id,
                    'locked': True,
                    'client_id': client_id,
                    'username': username,
                    'timestamp': time.time()
                })
            else:
                broadcast_global('resource_lock_changed', {
                    'resource_id': resource_id,
                    'locked': True,
                    'client_id': client_id,
                    'username': username,
                    'timestamp': time.time()
                })
            
            logger.info(f"Editing lock acquired: {resource_id} by {client_id} ({username})")
            
            # Respond with success
            emit('editing_lock_response', {
                'resource_id': resource_id,
                'success': True
            })
        else:
            # Get info about who holds the lock
            lock_info = client_tracker.get_lock_info(resource_id)
            
            # Respond with failure
            emit('editing_lock_response', {
                'resource_id': resource_id,
                'success': False,
                'lock_info': lock_info
            })
            
            logger.info(f"Editing lock denied: {resource_id} for {client_id}, already held by {lock_info['client_id'] if lock_info else 'unknown'}")
    
    @socketio.on('editing_stopped')
    def handle_editing_stopped(data):
        """Handle notification that a client stopped editing a resource."""
        client_id = request.sid
        resource_id = data.get('resource_id')
        
        if not resource_id:
            logger.warning(f"Invalid resource ID in editing stop notification from {client_id}")
            return
        
        # Release lock
        success = client_tracker.release_editing_lock(resource_id, client_id)
        
        if success:
            # Determine if this is a terminal-specific resource
            is_terminal_resource = 'terminal_' in resource_id
            terminal_id = None
            
            if is_terminal_resource:
                # Extract terminal ID from resource ID
                parts = resource_id.split('terminal_')
                if len(parts) > 1:
                    terminal_id = 'terminal_' + parts[1].split(':')[0]
            
            # Broadcast based on resource scope
            if terminal_id:
                broadcast_to_terminal(terminal_id, 'resource_lock_changed', {
                    'resource_id': resource_id,
                    'locked': False,
                    'timestamp': time.time()
                })
            else:
                broadcast_global('resource_lock_changed', {
                    'resource_id': resource_id,
                    'locked': False,
                    'timestamp': time.time()
                })
            
            logger.info(f"Editing lock released: {resource_id} by {client_id}")
        
        # Always send a success response even if the lock wasn't found
        # (it might have timed out or been released by the system)
        emit('editing_unlock_response', {
            'resource_id': resource_id,
            'success': True
        })

    @socketio.on('client_ping')
    def handle_client_ping():
        """Respond to client_ping with server_pong."""
        client_id = request.sid
        logger.debug(f"Received client_ping from {client_id}")
        emit('server_pong', {'timestamp': time.time()}, room=client_id)

    @socketio.on('variable_update_request')
    def handle_variable_update_request(data):
        """Handle variable update request from client."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        name = data.get('name')
        value = data.get('value')
        action = data.get('action', 'update')

        if not terminal_id or not name:
            logger.warning(f"Invalid variable update request from {client_id}")
            return

        try:
            variables = get_tab_variables(terminal_id)
            # Update or create variable
            variables[name] = {'display_name': name, 'reference': name.replace(' ',''), 'value': value}
            save_success = save_tab_variables(terminal_id, variables)
            if not save_success:
                logger.error(f"Failed to persist variable update for {terminal_id} - {name}")
            # Broadcast update to other clients in the terminal
            broadcast_to_terminal(terminal_id, 'remote_variable_update', {
                'terminal_id': terminal_id,
                'name': name,
                'value': value,
                'action': action,
                'timestamp': time.time()
            }, include_sender=False)
            logger.info(f"Broadcast remote_variable_update for {terminal_id} - {name}")
        except Exception as e:
            logger.error(f"Error handling variable update request: {e}")

    @socketio.on('code_block_updated')
    def handle_code_block_updated(data):
        """Handle granular code block update events (for real-time sync)."""
        client_id = request.sid
        terminal_id = data.get('terminal_id')
        playbook_id = data.get('playbook_id')
        code_block_index = data.get('code_block_index')
        new_code = data.get('new_code')
        if not all([terminal_id, playbook_id]) or code_block_index is None or new_code is None:
            logger.warning(f"Invalid code block update data from {client_id}")
            return
        # Optionally: Validate editing lock for playbook if needed
        # Broadcast to clients in the same terminal (including sender for now)
        broadcast_to_terminal(terminal_id, 'code_block_updated', {
            'terminal_id': terminal_id,
            'playbook_id': playbook_id,
            'code_block_index': code_block_index,
            'new_code': new_code,
            'timestamp': time.time(),
            'sender_id': client_id
        })
        logger.info(f"Code block {code_block_index} in playbook {playbook_id} updated by {client_id} (terminal {terminal_id})")

    logger.info("Initialized SocketIO event handlers")

# HTTP route to get current connected clients
@sync_routes.route('/clients', methods=['GET'])
def get_clients():
    """Get a list of all connected clients."""
    return {
        'success': True,
        'clients': client_tracker.get_all_clients(),
        'count': len(client_tracker.clients)
    }

# HTTP route to get clients in a specific terminal
@sync_routes.route('/terminals/<terminal_id>/clients', methods=['GET'])
def get_terminal_clients(terminal_id):
    """Get a list of clients in a specific terminal."""
    return {
        'success': True,
        'terminal_id': terminal_id,
        'clients': client_tracker.get_terminal_clients(terminal_id),
        'count': len(client_tracker.get_terminal_clients(terminal_id))
    }
