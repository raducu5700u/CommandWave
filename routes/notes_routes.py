"""
routes/notes_routes.py
Flask Blueprint for notes-related API endpoints.
"""

import logging
from flask import Blueprint, request, jsonify

from core.notes_storage import (
    load_global_notes, save_global_notes,
    load_terminal_notes, save_terminal_notes,
    list_all_notes, rename_terminal_notes
)

# Configure logging
logger = logging.getLogger('commandwave')

# Create blueprint
notes_routes = Blueprint('notes_routes', __name__, url_prefix='/api/notes')

@notes_routes.route('/global', methods=['GET'])
def get_global_notes():
    """API endpoint to get global notes."""
    try:
        content = load_global_notes()
        return jsonify({
            'success': True,
            'content': content
        })
    except Exception as e:
        logger.error(f"Error retrieving global notes: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@notes_routes.route('/global', methods=['POST'])
def save_global_notes_endpoint():
    """API endpoint to save global notes."""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if save_global_notes(content):
            return jsonify({
                'success': True,
                'message': 'Global notes saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to save global notes'
            }), 500
    except Exception as e:
        logger.error(f"Error saving global notes: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@notes_routes.route('/terminal/<terminal_id>', methods=['GET'])
def get_terminal_notes(terminal_id):
    """API endpoint to get terminal-specific notes."""
    try:
        content = load_terminal_notes(terminal_id)
        return jsonify({
            'success': True,
            'terminal_id': terminal_id,
            'content': content
        })
    except Exception as e:
        logger.error(f"Error retrieving notes for terminal {terminal_id}: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@notes_routes.route('/terminal/<terminal_id>', methods=['POST'])
def save_terminal_notes_endpoint(terminal_id):
    """API endpoint to save terminal-specific notes."""
    try:
        data = request.get_json()
        content = data.get('content', '')
        
        if save_terminal_notes(terminal_id, content):
            return jsonify({
                'success': True,
                'message': f'Notes for terminal {terminal_id} saved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to save notes for terminal {terminal_id}'
            }), 500
    except Exception as e:
        logger.error(f"Error saving notes for terminal {terminal_id}: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@notes_routes.route('/list', methods=['GET'])
def list_notes():
    """API endpoint to list all available notes."""
    try:
        notes = list_all_notes()
        return jsonify({
            'success': True,
            'notes': notes
        })
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@notes_routes.route('/terminal/rename', methods=['POST'])
def rename_terminal_notes_endpoint():
    """API endpoint to rename a terminal's notes file."""
    try:
        data = request.get_json() or {}
        old_name = data.get('old_name')
        new_name = data.get('new_name')
        if not old_name or not new_name:
            return jsonify(success=False, message='old_name and new_name required'), 400
        if rename_terminal_notes(old_name, new_name):
            return jsonify(success=True, message='Notes file renamed')
        else:
            return jsonify(success=False, message='Failed to rename notes file'), 500
    except Exception as e:
        logger.error(f"Error renaming notes file: {e}")
        return jsonify(success=False, message=str(e)), 500
