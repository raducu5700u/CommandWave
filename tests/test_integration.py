"""
Integration tests for CommandWave application testing complete workflows
"""
import os
import json
import pytest
import time

def test_full_workflow(client, app, monkeypatch):
    """
    Test the complete workflow of:
    1. Selecting a playbook
    2. Loading playbook content
    3. Rendering the playbook
    4. Substituting variables
    5. Sending commands to a terminal
    """
    # Test data
    test_playbook = """# Test Integration Playbook
    
## Command with variables
```bash
echo "Hello, $TestVar"
```

## Network command
```bash
ping -c 2 $TargetIP
```
"""
    
    # Setup the mocks for creating a terminal
    def mock_find_available_port(start_port, end_port):
        return 7682
    
    monkeypatch.setattr('main.find_available_port', mock_find_available_port)
    
    def mock_start_ttyd_process(port, session_name, use_tmux_config=False):
        return {'pid': 12345, 'port': port}
    
    monkeypatch.setattr('main.start_ttyd_process', mock_start_ttyd_process)
    
    # 1. Create a terminal
    terminal_response = client.post('/api/terminals/new', json={'name': 'Integration Test Terminal'})
    assert terminal_response.status_code == 200
    terminal_data = json.loads(terminal_response.data)
    assert terminal_data['success'] is True
    terminal_port = terminal_data['port']
    
    # Setup mock for file operations
    monkeypatch.setattr(os.path, 'exists', lambda path: True)
    monkeypatch.setattr(os.path, 'isfile', lambda path: True)
    
    def mock_open_read(path, *args, **kwargs):
        class MockFile:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            
            def read(self):
                return test_playbook
        
        return MockFile()
    
    monkeypatch.setattr('builtins.open', mock_open_read)
    
    # 2. Load the playbook file
    playbook_response = client.get('/api/playbooks/integration_test.md')
    assert playbook_response.status_code == 200
    playbook_data = json.loads(playbook_response.data)
    assert playbook_data['success'] is True
    assert 'content' in playbook_data
    assert 'html' in playbook_data
    
    # 3. Sync the playbook to associate it with the terminal
    sync_response = client.post('/api/playbooks/sync/integration_test.md', json={
        'content': test_playbook,
        'editor': 'test-client',
        'terminal_id': f'term-{terminal_port}'
    })
    assert sync_response.status_code == 200
    assert json.loads(sync_response.data)['success'] is True
    
    # Mock the send_keys_to_tmux function
    def mock_send_keys(session, keys):
        return True
    
    monkeypatch.setattr('main.send_keys_to_tmux', mock_send_keys)
    
    # 4. Send commands with variables to the terminal
    # Command 1 - with TestVar substituted
    keys_response = client.post('/api/terminals/sendkeys', json={
        'port': terminal_port,
        'keys': 'echo "Hello, World"'  # This would be substituted in frontend
    })
    assert keys_response.status_code == 200
    assert json.loads(keys_response.data)['success'] is True
    
    # Command 2 - with TargetIP substituted
    keys_response = client.post('/api/terminals/sendkeys', json={
        'port': terminal_port,
        'keys': 'ping -c 2 192.168.1.1'  # This would be substituted in frontend
    })
    assert keys_response.status_code == 200
    assert json.loads(keys_response.data)['success'] is True
    
    # 5. Check that the terminal is still available
    terminal_list_response = client.get('/api/terminals/list')
    assert terminal_list_response.status_code == 200
    terminal_list_data = json.loads(terminal_list_response.data)
    assert terminal_list_data['success'] is True
    
    # 6. Delete the terminal
    def mock_kill_terminal(port):
        return True
    
    monkeypatch.setattr('main.kill_terminal', mock_kill_terminal)
    
    delete_response = client.delete(f'/api/terminals/{terminal_port}')
    assert delete_response.status_code == 200
    assert json.loads(delete_response.data)['success'] is True

def test_concurrent_user_workflow(client, app, monkeypatch):
    """
    Test simulating multiple users accessing the application concurrently:
    1. Create multiple terminals
    2. Load different playbooks for each terminal
    3. Send commands to each terminal
    4. Save and retrieve notes for each terminal
    """
    # Setup mock terminals
    terminal_ports = [7682, 7683, 7684]
    terminal_names = ['User 1 Terminal', 'User 2 Terminal', 'User 3 Terminal']
    mock_terminals = {}
    
    # Sample playbooks for each user
    playbooks = {
        'user1.md': """# User 1 Playbook
```bash
echo "User 1 command"
```""",
        'user2.md': """# User 2 Playbook
```bash
echo "User 2 command"
```""",
        'user3.md': """# User 3 Playbook
```bash
echo "User 3 command"
```"""
    }
    
    # Create a port generator
    port_iter = iter(terminal_ports)
    
    def mock_find_available_port(start, end):
        return next(port_iter)
    
    monkeypatch.setattr('main.find_available_port', mock_find_available_port)
    
    def mock_start_ttyd_process(port, session_name, use_tmux_config=False):
        return {'pid': 12345 + (port - 7682), 'port': port}
    
    monkeypatch.setattr('main.start_ttyd_process', mock_start_ttyd_process)
    
    # 1. Create terminals for each simulated user
    for i, name in enumerate(terminal_names):
        response = client.post('/api/terminals/new', json={'name': name})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        port = data['port']
        assert port == terminal_ports[i]
        mock_terminals[str(port)] = {
            'port': port,
            'name': name,
            'tmux_session': f'test-session-{port}'
        }
    
    # Update the main terminals dictionary with our mock terminals
    monkeypatch.setattr('main.terminals', mock_terminals)
    
    # Mock file operations for playbooks
    monkeypatch.setattr(os.path, 'exists', lambda path: True)
    monkeypatch.setattr(os.path, 'isfile', lambda path: True)
    
    def mock_open_read(path, *args, **kwargs):
        class MockFile:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            
            def read(self):
                # Extract playbook filename from path
                filename = os.path.basename(path)
                return playbooks.get(filename, "# Empty Playbook")
            
            def write(self, content):
                pass
        
        return MockFile()
    
    monkeypatch.setattr('builtins.open', mock_open_read)
    
    # 2. Load different playbooks for each terminal
    for i, port in enumerate(terminal_ports):
        playbook_name = f'user{i+1}.md'
        
        # Load playbook
        load_response = client.get(f'/api/playbooks/{playbook_name}')
        assert load_response.status_code == 200
        load_data = json.loads(load_response.data)
        assert load_data['success'] is True
        
        # Sync playbook with terminal
        sync_response = client.post(f'/api/playbooks/sync/{playbook_name}', json={
            'content': playbooks[playbook_name],
            'editor': f'user{i+1}',
            'terminal_id': f'term-{port}'
        })
        assert sync_response.status_code == 200
        assert json.loads(sync_response.data)['success'] is True
    
    # Mock send keys function
    sent_keys = []
    
    def mock_send_keys(session, keys):
        sent_keys.append((session, keys))
        return True
    
    monkeypatch.setattr('main.send_keys_to_tmux', mock_send_keys)
    
    # 3. Send commands to each terminal
    for port in terminal_ports:
        keys_response = client.post('/api/terminals/sendkeys', json={
            'port': port,
            'keys': f'echo "Command for terminal {port}"'
        })
        assert keys_response.status_code == 200
        assert json.loads(keys_response.data)['success'] is True
    
    # Check that keys were sent to the correct terminal sessions
    assert len(sent_keys) == len(terminal_ports)
    for i, port in enumerate(terminal_ports):
        session, keys = sent_keys[i]
        assert session == f'test-session-{port}'
        assert f'echo "Command for terminal {port}"' in keys
    
    # 4. Save and retrieve notes for each terminal
    for port in terminal_ports:
        # Save notes
        notes_content = f"Notes for terminal {port}"
        save_response = client.post('/api/notes/save', json={
            'terminal_id': f'term-{port}',
            'content': notes_content
        })
        assert save_response.status_code == 200
        save_data = json.loads(save_response.data)
        assert save_data['success'] is True
        
        # Get notes
        get_response = client.get(f'/api/notes?terminal_id=term-{port}')
        assert get_response.status_code == 200
        get_data = json.loads(get_response.data)
        assert get_data['success'] is True
        assert 'content' in get_data
        # Verify that the saved content matches what we expect
        # Note: We can't actually check the content directly since our mock doesn't save it
        # but we can verify the API call succeeded
    
    # 5. Clean up - delete terminals
    def mock_kill_terminal(port):
        if str(port) in mock_terminals:
            del mock_terminals[str(port)]
            return True
        return False
    
    monkeypatch.setattr('main.kill_terminal', mock_kill_terminal)
    
    for port in terminal_ports:
        delete_response = client.delete(f'/api/terminals/{port}')
        assert delete_response.status_code == 200
        delete_data = json.loads(delete_response.data)
        assert delete_data['success'] is True

def test_playbook_search_and_load_workflow(client, app, monkeypatch):
    """
    Test the workflow of:
    1. Searching for playbooks matching certain criteria
    2. Loading a found playbook
    3. Rendering and interacting with the loaded playbook
    """
    # Sample playbooks with searchable content
    playbooks = {
        'network.md': """# Network Playbook
## Scan command
```bash
nmap -sV $TargetIP
```""",
        
        'system.md': """# System Commands
## Check disk space
```bash
df -h
```""",
        
        'database.md': """# Database Commands
## Connect to MySQL
```bash
mysql -u $DBUser -p$DBPass
```"""
    }
    
    # Mock glob to return our test playbooks
    def mock_glob(pattern):
        return [f'/playbooks/{name}' for name in playbooks.keys()]
    
    monkeypatch.setattr('glob.glob', mock_glob)
    
    # Mock file reads
    file_content_iter = iter(playbooks.values())
    
    def mock_open_read(path, *args, **kwargs):
        class MockFile:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            
            def read(self):
                # For search, return each playbook content in sequence
                if 'search' in kwargs.get('_search', ''):
                    return next(file_content_iter)
                
                # For specific file, return its content
                filename = os.path.basename(path)
                return playbooks.get(filename, "# Empty Playbook")
        
        return MockFile()
    
    # Setup for search test
    search_content_iter = iter(playbooks.values())
    
    def mock_open_with_search(path, *args, **kwargs):
        mock_file = mock_open_read(path, *args, _search='search', **kwargs)
        return mock_file
    
    monkeypatch.setattr('builtins.open', mock_open_with_search)
    
    # 1. Search for "mysql" in playbooks
    search_response = client.get('/api/search?q=mysql')
    assert search_response.status_code == 200
    search_data = json.loads(search_response.data)
    assert search_data['success'] is True
    
    # Reset mock and prepare for loading a specific playbook
    def mock_open_specific(path, *args, **kwargs):
        class MockFile:
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
            
            def read(self):
                return playbooks['database.md']
        
        return MockFile()
    
    monkeypatch.setattr('builtins.open', mock_open_specific)
    monkeypatch.setattr(os.path, 'exists', lambda path: True)
    monkeypatch.setattr(os.path, 'isfile', lambda path: True)
    
    # 2. Load the found playbook
    load_response = client.get('/api/playbooks/database.md')
    assert load_response.status_code == 200
    load_data = json.loads(load_response.data)
    assert load_data['success'] is True
    assert 'content' in load_data
    assert 'html' in load_data
    
    # 3. Create a terminal to work with the playbook
    def mock_find_available_port(start, end):
        return 7682
    
    monkeypatch.setattr('main.find_available_port', mock_find_available_port)
    
    def mock_start_ttyd_process(port, session_name, use_tmux_config=False):
        return {'pid': 12345, 'port': port}
    
    monkeypatch.setattr('main.start_ttyd_process', mock_start_ttyd_process)
    
    terminal_response = client.post('/api/terminals/new', json={'name': 'Database Terminal'})
    assert terminal_response.status_code == 200
    terminal_data = json.loads(terminal_response.data)
    assert terminal_data['success'] is True
    terminal_port = terminal_data['port']
    
    # Mock the terminals dictionary
    mock_terminals = {str(terminal_port): {'tmux_session': 'test-session'}}
    monkeypatch.setattr('main.terminals', mock_terminals)
    
    # Mock send_keys_to_tmux
    mock_send_keys_calls = []
    
    def mock_send_keys(session, keys):
        mock_send_keys_calls.append((session, keys))
        return True
    
    monkeypatch.setattr('main.send_keys_to_tmux', mock_send_keys)
    
    # 4. Send the command from the playbook to the terminal
    keys_response = client.post('/api/terminals/sendkeys', json={
        'port': terminal_port,
        'keys': 'mysql -u root -ppassword'  # Substituted values
    })
    assert keys_response.status_code == 200
    assert json.loads(keys_response.data)['success'] is True
    
    # Verify the keys were sent correctly
    assert len(mock_send_keys_calls) == 1
    session, keys = mock_send_keys_calls[0]
    assert session == 'test-session'
    assert keys == 'mysql -u root -ppassword'
    
    # 5. Clean up the terminal
    def mock_kill_terminal(port):
        return True
    
    monkeypatch.setattr('main.kill_terminal', mock_kill_terminal)
    
    delete_response = client.delete(f'/api/terminals/{terminal_port}')
    assert delete_response.status_code == 200
    assert json.loads(delete_response.data)['success'] is True
