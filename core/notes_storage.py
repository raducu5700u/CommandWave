"""
core/notes_storage.py
Handles persistent storage for notes.
"""

import os
import logging
import time
from pathlib import Path
import re

# Configure logging
logger = logging.getLogger('commandwave')

# Notes storage directory
NOTES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'notes')

# Ensure notes directory exists
if not os.path.exists(NOTES_DIR):
    try:
        os.makedirs(NOTES_DIR, exist_ok=True)
        logger.info(f"Created notes directory: {NOTES_DIR}")
    except Exception as e:
        logger.error(f"Failed to create notes directory: {e}")

def get_global_notes_path():
    """Get the path to the global notes file."""
    return os.path.join(NOTES_DIR, 'global_notes.md')

def get_terminal_notes_path(terminal_name):
    """Get path to a terminal's notes file using its name."""
    # Sanitize terminal_name: keep alphanumerics, hyphens, underscores
    safe_name = re.sub(r'[^A-Za-z0-9_-]', '_', str(terminal_name))
    safe_name = safe_name.strip('_').lower()
    return os.path.join(NOTES_DIR, f'{safe_name}.md')

def save_global_notes(content):
    """
    Save global notes to disk.
    
    Args:
        content (str): The notes content to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        with open(get_global_notes_path(), 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info("Global notes saved to disk")
        return True
    except Exception as e:
        logger.error(f"Error saving global notes: {e}")
        return False

def load_global_notes():
    """
    Load global notes from disk.
    
    Returns:
        str: The notes content or empty string if not found
    """
    try:
        path = get_global_notes_path()
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info("Global notes loaded from disk")
            return content
        else:
            logger.info("No global notes file found, returning empty string")
            return ""
    except Exception as e:
        logger.error(f"Error loading global notes: {e}")
        return ""

def save_terminal_notes(terminal_name, content):
    """
    Save terminal-specific notes to disk.
    
    Args:
        terminal_name (str): The terminal name
        content (str): The notes content to save
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        with open(get_terminal_notes_path(terminal_name), 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Notes saved for terminal {terminal_name}")
        return True
    except Exception as e:
        logger.error(f"Error saving notes for terminal {terminal_name}: {e}")
        return False

def load_terminal_notes(terminal_name):
    """
    Load terminal-specific notes from disk.
    
    Args:
        terminal_name (str): The terminal name
        
    Returns:
        str: The notes content or empty string if not found
    """
    try:
        path = get_terminal_notes_path(terminal_name)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"Notes loaded for terminal {terminal_name}")
            return content
        else:
            logger.info(f"No notes file found for terminal {terminal_name}, returning empty string")
            return ""
    except Exception as e:
        logger.error(f"Error loading notes for terminal {terminal_name}: {e}")
        return ""

def list_all_notes():
    """
    List all saved notes files.
    
    Returns:
        dict: Dictionary with global and terminal notes info
    """
    try:
        result = {
            'global': False,
            'terminals': []
        }
        
        if not os.path.exists(NOTES_DIR):
            return result
            
        files = os.listdir(NOTES_DIR)
        
        for file in files:
            if file == 'global_notes.md':
                result['global'] = True
            elif file.endswith('.md'):
                # Name is filename without extension
                name = file[:-3]
                file_path = os.path.join(NOTES_DIR, file)
                stat = os.stat(file_path)
                result['terminals'].append({
                    'name': name,
                    'size': stat.st_size,
                    'modified': stat.st_mtime
                })
                
        return result
    except Exception as e:
        logger.error(f"Error listing notes: {e}")
        return {'global': False, 'terminals': []}

def rename_terminal_notes(old_name, new_name):
    """Rename a terminal's notes file from old_name to new_name."""
    old_path = get_terminal_notes_path(old_name)
    new_path = get_terminal_notes_path(new_name)
    try:
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            logger.info(f"Renamed notes file from {old_path} to {new_path}")
        return True
    except Exception as e:
        logger.error(f"Error renaming notes file from {old_name} to {new_name}: {e}")
        return False
