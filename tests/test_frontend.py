"""
Tests for frontend JavaScript functionality using pytest and selenium
"""
import os
import time
import pytest
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Import subprocess testing module for JavaScript unit tests
import subprocess
import tempfile

# Fixtures for frontend testing
@pytest.fixture
def chrome_options():
    """Configure Chrome options for headless testing."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return options

@pytest.fixture
def selenium_browser(chrome_options):
    """Create a headless Chrome browser for UI testing."""
    try:
        browser = webdriver.Chrome(options=chrome_options)
        browser.set_window_size(1280, 1024)
        yield browser
    finally:
        browser.quit()

@pytest.fixture
def js_unit_test_file():
    """Create a temporary file for JavaScript unit testing."""
    fd, path = tempfile.mkstemp(suffix='.js')
    with os.fdopen(fd, 'w') as f:
        f.write("""
// JavaScript unit test using Node.js and Jest-like assertions
const fs = require('fs');
const path = require('path');

// Basic assertion functions
function expect(value) {
    return {
        toBe: function(expected) {
            if (value !== expected) {
                throw new Error(`Expected ${expected} but got ${value}`);
            }
            return true;
        },
        toContain: function(expected) {
            if (!value.includes(expected)) {
                throw new Error(`Expected "${value}" to contain "${expected}"`);
            }
            return true;
        },
        toEqual: function(expected) {
            if (JSON.stringify(value) !== JSON.stringify(expected)) {
                throw new Error(`Expected ${JSON.stringify(expected)} but got ${JSON.stringify(value)}`);
            }
            return true;
        }
    };
}

// Load the script.js file content
let scriptPath = process.argv[2];
if (!scriptPath) {
    console.error('Script path not provided');
    process.exit(1);
}

const scriptContent = fs.readFileSync(scriptPath, 'utf8');

// Create a mock DOM environment
global.document = {
    querySelectorAll: function() { return []; },
    querySelector: function() { return null; },
    getElementById: function() { return null; },
    createElement: function() { 
        return {
            classList: { add: function() {} },
            appendChild: function() {},
            setAttribute: function() {}
        }; 
    },
    body: { appendChild: function() {} },
    addEventListener: function() {}
};

global.window = {
    state: {
        terminals: {},
        activeTerminal: null
    },
    addEventListener: function() {}
};

// Extract and test the substituteVariables function
try {
    // Extract the substituteVariables function using regex
    const functionMatch = scriptContent.match(/function\\s+substituteVariables\\s*\\(([^)]*)\\)\\s*{([^}]*)}/s);
    
    if (!functionMatch) {
        throw new Error('Could not find substituteVariables function in script.js');
    }
    
    const functionBody = functionMatch[2];
    const functionArgs = functionMatch[1].split(',').map(arg => arg.trim());
    
    // Create the function from extracted code
    global.substituteVariables = new Function(...functionArgs, functionBody);
    
    // Run the tests
    console.log('Running substituteVariables tests...');
    
    // Test 1: Basic variable substitution
    const testInput1 = 'echo "Hello, $TestVar"';
    const testVars1 = { TestVar: 'World' };
    const result1 = substituteVariables(testInput1, testVars1);
    expect(result1).toBe('echo "Hello, World"');
    console.log('✓ Test 1 passed');
    
    // Test 2: Multiple variables
    const testInput2 = 'curl http://$TargetIP:$Port/api';
    const testVars2 = { TargetIP: '192.168.1.1', Port: '8080' };
    const result2 = substituteVariables(testInput2, testVars2);
    expect(result2).toBe('curl http://192.168.1.1:8080/api');
    console.log('✓ Test 2 passed');
    
    // Test 3: Undefined variables should remain as is
    const testInput3 = 'echo "$Var1 and $Var2"';
    const testVars3 = { Var1: 'Hello' };
    const result3 = substituteVariables(testInput3, testVars3);
    expect(result3).toBe('echo "Hello and $Var2"');
    console.log('✓ Test 3 passed');
    
    // Test 4: Empty input
    const testInput4 = '';
    const testVars4 = { TestVar: 'Test' };
    const result4 = substituteVariables(testInput4, testVars4);
    expect(result4).toBe('');
    console.log('✓ Test 4 passed');
    
    // Test 5: Special characters in variables
    const testInput5 = 'grep "$Pattern" file';
    const testVars5 = { Pattern: 'special*[chars]?+' };
    const result5 = substituteVariables(testInput5, testVars5);
    expect(result5).toBe('grep "special*[chars]?+" file');
    console.log('✓ Test 5 passed');
    
    console.log('All tests passed!');
    process.exit(0);
} catch (error) {
    console.error('Test failed:', error.message);
    process.exit(1);
}
        """)
    return path

# Unit tests for JavaScript functions
def test_substitute_variables(js_unit_test_file):
    """Test the substituteVariables function in the JavaScript code."""
    # Find the static directory to locate script.js
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    
    # Run Node.js test
    try:
        result = subprocess.run(
            ['node', js_unit_test_file, os.path.join(static_dir, 'js', 'script.js')],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        assert "✓ Test" in result.stdout
        assert "Error" not in result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Test failed: {e.stderr}")
        raise

# Integration tests for the frontend
def test_playbook_rendering(client, app, selenium_browser, monkeypatch):
    """Test the rendering of a playbook in the frontend."""
    
    # Mock data for testing
    test_playbook_content = """# Test Playbook

## Commands

```bash
echo "Hello, $TestVar"
```

## Description
This is a test playbook.
"""

    def test_playbook_page():
        """Set up a test route and page for playbook rendering"""
        
        # Mock the playbook retrieval
        def mock_get_playbook(*args, **kwargs):
            class MockResponse:
                @property
                def status_code(self):
                    return 200
                
                @property
                def data(self):
                    return json.dumps({
                        'success': True,
                        'html': f"""<h1>Test Playbook</h1>
<h2>Commands</h2>
<pre><code class="language-bash">echo "Hello, $TestVar"
</code></pre>
<h2>Description</h2>
<p>This is a test playbook.</p>""",
                        'content': test_playbook_content
                    }).encode('utf-8')
            
            return MockResponse()
        
        # Apply mocks
        monkeypatch.setattr(client, 'get', mock_get_playbook)
        
        # Add test routes to the app
        @app.route('/test/playbook')
        def test_route():
            return """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Playbook Test</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    pre { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
                    code { font-family: monospace; }
                </style>
                <script>
                    // Test variables
                    const variables = {
                        TestVar: 'World'
                    };
                    
                    // Function to substitute variables
                    function substituteVariables(text, vars) {
                        let substituted = text;
                        for (const key in vars) {
                            const regex = new RegExp('\\$' + key, 'g');
                            substituted = substituted.replace(regex, vars[key]);
                        }
                        return substituted;
                    }
                    
                    // Function to load playbook
                    function loadPlaybook() {
                        fetch('/api/playbooks/test_playbook.md')
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    // Display the playbook
                                    document.getElementById('playbook-content').innerHTML = data.html;
                                    
                                    // Apply variable substitution to code blocks
                                    const codeBlocks = document.querySelectorAll('pre code');
                                    codeBlocks.forEach(code => {
                                        const original = code.textContent;
                                        code.textContent = substituteVariables(original, variables);
                                        code.setAttribute('data-original', original);
                                    });
                                }
                            });
                    }
                    
                    // Initialization
                    window.onload = function() {
                        loadPlaybook();
                    };
                </script>
            </head>
            <body>
                <h1>Playbook Test</h1>
                <div id="playbook-content">Loading...</div>
            </body>
            </html>
            """
    
    # Add the test route to the app
    test_playbook_page()
    
    # Start a server in a separate thread
    import threading
    server_thread = threading.Thread(target=app.run, kwargs={
        'host': '127.0.0.1',
        'port': 5001,
        'debug': False,
        'use_reloader': False
    })
    server_thread.daemon = True
    server_thread.start()
    
    # Give the server time to start
    time.sleep(2)
    
    try:
        # Navigate to the test page
        selenium_browser.get('http://127.0.0.1:5001/test/playbook')
        
        # Wait for the playbook content to load
        WebDriverWait(selenium_browser, 10).until(
            EC.presence_of_element_located((By.ID, "playbook-content"))
        )
        
        # Wait for the code block to be populated
        WebDriverWait(selenium_browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "code"))
        )
        
        # Check the content
        content = selenium_browser.find_element(By.ID, "playbook-content")
        assert "Test Playbook" in content.text
        
        # Check if variable substitution occurred in the code block
        code_block = selenium_browser.find_element(By.TAG_NAME, "code")
        assert "echo \"Hello, World\"" in code_block.text
        
    finally:
        # Ensure the app is stopped
        app.config['TESTING'] = False

def test_js_variable_substitution_with_dom(client, app, selenium_browser, monkeypatch):
    """Test the variable substitution in the actual DOM environment."""
    
    # Create a mapping of test cases to expected outcomes
    test_case = {
        'input': 'nmap -sV $TargetIP -p $Ports',
        'variables': {
            'TargetIP': '192.168.1.1',
            'Ports': '80,443'
        },
        'expected': 'nmap -sV 192.168.1.1 -p 80,443'
    }
    
    def test_vars_page():
        """Set up a test route and page for variable substitution testing"""
        @app.route('/test/vars')
        def test_vars_route():
            return f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Variable Substitution Test</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    pre {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; }}
                    code {{ font-family: monospace; }}
                </style>
                <script>
                    // Test variables
                    const variables = {json.dumps(test_case['variables'])};
                    
                    // Function to substitute variables
                    function substituteVariables(text, vars) {{
                        let substituted = text;
                        for (const key in vars) {{
                            const regex = new RegExp('\\\\$' + key, 'g');
                            substituted = substituted.replace(regex, vars[key]);
                        }}
                        return substituted;
                    }}
                    
                    window.onload = function() {{
                        // Get the code element
                        const codeElement = document.getElementById('test-code');
                        
                        // Store original text
                        const originalText = codeElement.textContent;
                        
                        // Apply substitution
                        const substituted = substituteVariables(originalText, variables);
                        
                        // Update the element
                        codeElement.textContent = substituted;
                        codeElement.setAttribute('data-original', originalText);
                        
                        // Show the result
                        document.getElementById('result').textContent = 
                            'Original: ' + originalText + '\\nSubstituted: ' + substituted;
                    }};
                </script>
            </head>
            <body>
                <h1>Variable Substitution Test</h1>
                <pre><code id="test-code">{test_case['input']}</code></pre>
                <pre id="result">Processing...</pre>
            </body>
            </html>
            """
    
    # Add the test page
    test_vars_page()
    
    # Start a server in a separate thread
    import threading
    server_thread = threading.Thread(target=app.run, kwargs={
        'host': '127.0.0.1',
        'port': 5002,
        'debug': False,
        'use_reloader': False
    })
    server_thread.daemon = True
    server_thread.start()
    
    # Give the server time to start
    time.sleep(2)
    
    try:
        # Navigate to the test page
        selenium_browser.get('http://127.0.0.1:5002/test/vars')
        
        # Wait for the result to be populated
        WebDriverWait(selenium_browser, 10).until(
            EC.text_to_be_present_in_element((By.ID, "result"), "Substituted:")
        )
        
        # Check the code element has the substituted content
        code_element = selenium_browser.find_element(By.ID, "test-code")
        assert test_case['expected'] in code_element.text
        
        # Check the result shows both original and substituted
        result_element = selenium_browser.find_element(By.ID, "result")
        assert f"Original: {test_case['input']}" in result_element.text
        assert f"Substituted: {test_case['expected']}" in result_element.text
        
    finally:
        # Ensure the app is stopped
        app.config['TESTING'] = False

def test_ui_interaction_loading_playbook(client, app, selenium_browser, monkeypatch):
    """Test the UI interactions for loading a playbook."""
    
    def mock_playbooks_list():
        """Mock the API response for listing playbooks"""
        class MockListResponse:
            @property
            def status_code(self):
                return 200
                
            @property
            def data(self):
                return json.dumps({
                    'success': True,
                    'playbooks': [
                        {'filename': 'test_playbook.md', 'description': 'Test Playbook'}
                    ]
                }).encode('utf-8')
        
        return MockListResponse()
    
    def mock_playbook_content():
        """Mock the API response for a playbook's content"""
        class MockContentResponse:
            @property
            def status_code(self):
                return 200
                
            @property
            def data(self):
                return json.dumps({
                    'success': True,
                    'html': """<h1>Test Playbook</h1>
<pre><code class="language-bash">echo "Hello, $Name"</code></pre>""",
                    'content': '# Test Playbook\n```bash\necho "Hello, $Name"\n```'
                }).encode('utf-8')
        
        return MockContentResponse()
    
    def test_ui_page():
        """Set up a test route and page for UI interaction testing"""
        
        # Setup route mocking
        original_get = client.get
        def mock_get(url, *args, **kwargs):
            if '/api/playbooks/list/all' in url:
                return mock_playbooks_list()
            elif '/api/playbooks/' in url:
                return mock_playbook_content()
            return original_get(url, *args, **kwargs)
        
        monkeypatch.setattr(client, 'get', mock_get)
        
        @app.route('/test/ui')
        def test_ui_route():
            return """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>UI Interaction Test</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    pre { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }
                    code { font-family: monospace; }
                    ul { list-style-type: none; padding: 0; }
                    li { margin-bottom: 10px; }
                    a { color: #0066cc; text-decoration: none; }
                    a:hover { text-decoration: underline; }
                </style>
                <script>
                    // Test variables
                    const variables = {
                        Name: 'World'
                    };
                    
                    // Function to substitute variables
                    function substituteVariables(text, vars) {
                        let substituted = text;
                        for (const key in vars) {
                            const regex = new RegExp('\\$' + key, 'g');
                            substituted = substituted.replace(regex, vars[key]);
                        }
                        return substituted;
                    }
                    
                    // Function to load playbook
                    function loadPlaybook(filename) {
                        fetch('/api/playbooks/' + filename)
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    // Update info
                                    document.getElementById('playbook-info').textContent = 'Loaded: ' + filename;
                                    
                                    // Display the playbook
                                    document.getElementById('playbooks').innerHTML = data.html;
                                    
                                    // Apply variable substitution to code blocks
                                    const codeBlocks = document.querySelectorAll('pre code');
                                    codeBlocks.forEach(code => {
                                        const original = code.textContent;
                                        const substituted = substituteVariables(original, variables);
                                        code.textContent = substituted;
                                        code.setAttribute('data-original', original);
                                    });
                                }
                            })
                            .catch(error => {
                                console.error('Error loading playbook:', error);
                            });
                    }
                    
                    // Initialize
                    window.onload = function() {
                        // Load playbooks list
                        fetch('/api/playbooks/list/all')
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    const list = document.getElementById('playbook-list');
                                    data.playbooks.forEach(playbook => {
                                        const item = document.createElement('li');
                                        const link = document.createElement('a');
                                        link.href = '#';
                                        link.textContent = playbook.filename;
                                        link.onclick = function(e) {
                                            e.preventDefault();
                                            loadPlaybook(playbook.filename);
                                        };
                                        item.appendChild(link);
                                        list.appendChild(item);
                                    });
                                }
                            })
                            .catch(error => {
                                console.error('Error loading playbooks list:', error);
                            });
                    };
                </script>
            </head>
            <body>
                <h1>UI Interaction Test</h1>
                <div>
                    <h2>Playbooks List</h2>
                    <ul id="playbook-list"></ul>
                </div>
                <div>
                    <h2>Current Playbook</h2>
                    <div id="playbook-info">No playbook loaded</div>
                    <div id="playbooks"></div>
                </div>
            </body>
            </html>
            """
    
    # Add the test route
    test_ui_page()
    
    # Start a server in a separate thread
    import threading
    server_thread = threading.Thread(target=app.run, kwargs={
        'host': '127.0.0.1',
        'port': 5003,
        'debug': False,
        'use_reloader': False
    })
    server_thread.daemon = True
    server_thread.start()
    
    # Give the server time to start
    time.sleep(2)
    
    try:
        # Navigate to the test page
        selenium_browser.get('http://127.0.0.1:5003/test/ui')
        
        # Wait for page to load
        WebDriverWait(selenium_browser, 10).until(
            EC.presence_of_element_located((By.ID, "playbook-list"))
        )
        
        # Wait for playbook list to be populated
        WebDriverWait(selenium_browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "li"))
        )
        
        # Click on the first playbook
        playbook_link = selenium_browser.find_element(By.TAG_NAME, "a")
        playbook_link.click()
        
        # Wait for playbook to load
        WebDriverWait(selenium_browser, 10).until(
            EC.text_to_be_present_in_element((By.ID, "playbook-info"), "Loaded: test_playbook.md")
        )
        
        # Check the loaded playbook
        playbooks_div = selenium_browser.find_element(By.ID, "playbooks")
        assert "Test Playbook" in playbooks_div.text
        
        # Check variable substitution
        code_element = selenium_browser.find_element(By.TAG_NAME, "code")
        assert "echo \"Hello, World\"" in code_element.text
        
    finally:
        # Ensure the app is stopped
        app.config['TESTING'] = False
