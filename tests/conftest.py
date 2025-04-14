"""
CommandWave pytest fixtures and configuration
"""
import os
import sys
import pytest
import tempfile
import shutil
from flask import Flask

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main  # Import the main module from parent directory

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a temporary directory for test data
    test_instance_path = tempfile.mkdtemp()
    test_notes_dir = os.path.join(test_instance_path, 'notes_data')
    test_playbooks_dir = os.path.join(test_instance_path, 'playbooks')
    
    # Create necessary directories
    os.makedirs(test_notes_dir, exist_ok=True)
    os.makedirs(test_playbooks_dir, exist_ok=True)
    
    # Copy test playbooks to the test directory
    test_data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    if os.path.exists(test_data_dir):
        for filename in os.listdir(test_data_dir):
            if filename.endswith('.md'):
                src = os.path.join(test_data_dir, filename)
                dst = os.path.join(test_playbooks_dir, filename)
                shutil.copy2(src, dst)
    
    # Store original directories
    original_notes_dir = main.NOTES_DIR
    original_playbooks_dir = main.PLAYBOOKS_DIR
    
    # Override directories for testing
    main.NOTES_DIR = test_notes_dir
    main.PLAYBOOKS_DIR = test_playbooks_dir
    
    # Create a test Flask app with test configuration
    app = main.app
    app.config.update({
        'TESTING': True,
        'SERVER_NAME': None,  # Prevent SERVER_NAME issues
        'PREFERRED_URL_SCHEME': 'http'
    })
    
    # Mock the terminal processes functionality - use a simple dictionary
    # for testing instead of trying to mock complex functions
    main.terminals = {}  # Reset terminals dictionary
    main.playbooks = {}  # Reset playbooks dictionary
    
    with app.app_context():
        yield app
    
    # Restore original directories
    main.NOTES_DIR = original_notes_dir
    main.PLAYBOOKS_DIR = original_playbooks_dir
    
    # Clean up temporary test directory
    shutil.rmtree(test_instance_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner()

@pytest.fixture
def test_playbooks_dir():
    """Return the path to the test playbooks directory."""
    return os.path.join(os.path.dirname(__file__), 'test_data')

@pytest.fixture
def sample_playbook_content():
    """Return sample playbook markdown content for testing."""
    return """# Test Playbook
    
## Command Section 1
```bash
echo "Hello, $TestVar"
```

## Command Section 2
```bash
ping -c 4 $TargetIP
```
"""

@pytest.fixture
def sample_note_content():
    """Return sample note content for testing."""
    return "This is a test note with some content."

@pytest.fixture
def complex_playbook_content():
    """Return a more complex playbook for testing edge cases."""
    return """# Complex Test Playbook
    
## Command with nested variables
```bash
curl -X POST "http://$TargetIP:$Port/api/$Endpoint" -d '{"key": "$Value", "nested": "${NestedVar}"}'
```

## Command with special characters
```bash
grep -E "^[a-zA-Z0-9]+" $FileName | sed 's/$SearchPattern/$ReplacePattern/g'
```

## Empty command block
```bash

```

## Non-bash code block
```python
import os
print(f"Working with {os.environ.get('$EnvVar')}")
```
"""

@pytest.fixture
def large_playbook_content():
    """Return a large playbook content for testing performance."""
    sections = []
    for i in range(50):
        sections.append(f"""## Section {i}
```bash
echo "Command group {i}"
ls -la /tmp/folder_{i}
find /var/log -name "$Pattern_{i}" | grep "$Filter_{i}"
```
""")
    
    return "# Large Test Playbook\n\n" + "\n".join(sections)
