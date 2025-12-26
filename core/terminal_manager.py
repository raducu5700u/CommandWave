import os
import subprocess
import socket
import logging
import threading
import time
import sys

logger = logging.getLogger('commandwave')

# Global state for terminals
terminals = {}
process_lock = threading.Lock()

# Constants
DEFAULT_TERMINAL_PORT = 7681
TERMINAL_PORT_RANGE = (7682, 7781)
HOSTNAME = 'localhost'

# Paths - Assumes this file is in core/ so we go up one level
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TMUX_CONFIG_PATH = os.path.join(BASE_DIR, 'commandwave_theme.tmux.conf')

def get_base_dir():
    return BASE_DIR

def is_port_available(port):
    """Check if a port is available to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((HOSTNAME, port)) != 0

def find_available_port(start_port, end_port):
    """Find an available port in the specified range."""
    for port in range(start_port, end_port + 1):
        # We need to check if it's in our local terminals dict too
        if is_port_available(port) and port not in terminals:
            return port
    return None

def send_keys_to_tmux(tmux_session_name, keys):
    """Send keys to a tmux session."""
    try:
        # Ensure keys end with a newline if not already present
        if not keys.endswith('\n'):
            keys += '\n'
            
        # Send keys to the tmux session safely without shell=True
        # keys argument in send-keys is taken literally by tmux, but we pass it as a list arg
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

def start_ttyd_process(port, tmux_session_name, use_tmux_config=False):
    """
    Start a ttyd process linked to a tmux session on the specified port.
    """
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
            # Create a new tmux session safely
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
            '--client-option', 'fontSize=12',
            '--client-option', 'disableLeaveAlert=true',
            '--client-option', 'fontFamily=monospace',
            '--client-option', 'rendererType=canvas',
            '--client-option', 'letterSpacing=0',
            '--client-option', 'lineHeight=1',
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
    
    # Clean up persisted variable files (if this belongs here, or separate config manager)
    # Leaving out variable cleanup for now to keep this minimal, or move it later.
    return True
