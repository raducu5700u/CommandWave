# CommandWave

<div align="center">
  <img src="static/img/commandwave-logo.png" alt="CommandWave Logo" width="400">
  <p><em>A cyberpunk-themed web interface for managing terminal sessions alongside executable Markdown playbooks.</em></p>
  </div>

## Overview

CommandWave provides a streamlined, web-based environment for managing multiple terminal sessions powered by `tmux` and `ttyd`. It features a distinct cyberpunk/neon aesthetic and allows users to work with Markdown-based "playbooks" containing executable code blocks. Define variables, search through local playbooks, and execute commands directly into your active terminal session, enhancing command-line workflows.

![CommandWave Screenshot](static/img/screenshot.png) *(Ensure you have a `screenshot.png` in `static/img/`)*

## Features

* **Multi-Tab Terminal Management**: Create, name, switch between, and close multiple `tmux`-backed terminal sessions via `ttyd`.
* **Markdown Playbook Integration**:
    * Upload Markdown (`.md`) files as playbooks.
    * Create new playbooks directly within the application.
    * Playbooks are parsed to separate text blocks from code blocks.
* **Executable Code Blocks**: Execute shell command blocks from playbooks directly into the active terminal session.
* **Variable Substitution**: Define key-value pairs (e.g., `$TargetIP`, `$Port`) that are automatically substituted into code blocks before execution.
* **Playbook Search**: Quickly search across all loaded playbooks for specific commands or text.
* **Persistent Notes**:
    * A global notes panel for general information.
    * A separate notes panel for each terminal tab. Notes are saved automatically.
* **Cyberpunk UI**: A visually distinct interface inspired by neon and cyberpunk aesthetics, including a matching `tmux` theme option.
* **Custom tmux Theming**: Includes an optional, enhanced `tmux` configuration file (`commandwave_theme.tmux.conf`) for a cohesive visual experience.

## Requirements

* Python 3.6+
* Flask (and other libraries listed in `requirements.txt`)
* **`ttyd`**: A command-line tool for sharing terminals over the web.
    * *Installation*: Download binaries or build from source via the [official ttyd GitHub repository](https://github.com/tsl0922/ttyd).
* **`tmux`**: A terminal multiplexer.
    * *Installation*: Typically available via system package managers (e.g., `sudo apt install tmux`, `brew install tmux`).

## Installation

1.  **Install System Dependencies**: Ensure `ttyd` and `tmux` are installed and accessible in your system's PATH. Refer to their respective documentation for installation instructions.
2.  **Clone the Repository**:
    ```bash
    git clone [https://github.com/YOUR_USERNAME/CommandWave](https://github.com/YOUR_USERNAME/CommandWave) # Replace with your repo URL
    cd CommandWave
    ```
3.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Running CommandWave

1.  **Navigate to the Directory**:
    ```bash
    cd CommandWave
    ```
2.  **Start the Application**:
    ```bash
    python main.py 
    ```
3.  **Access the UI**: Open your web browser and go to `http://localhost:5000` (or the port specified if using the `--port` option).

### Command Line Options 

* `--port PORT`: Specify the port for the web server (default: 5000).
* `--use-default-tmux-config`: Apply the custom `commandwave_theme.tmux.conf` to the `tmux` sessions managed by CommandWave.

## Usage Guide

1.  **Terminals**:
    * The main terminal is available on launch.
    * Click the `+` button in the terminal tabs bar to create a new terminal session. You'll be prompted for a name.
    * Click on a tab to switch to that terminal.
    * Double-click a tab name (not the 'x') to rename it.
    * Click the `x` on a tab to close that terminal session.
2.  **Variables**:
    * Use the "Variables" section to define key-value pairs. Default variables like `targetIP`, `port`, etc., are provided.
    * Click "+ Add Variable" to create custom variables. Use camelCase names (e.g., `myVar`).
    * These variables will be substituted in playbook code blocks using the `$MyVar` format (PascalCase with a leading `$`) when you click "Execute".
3.  **Playbooks**:
    * Click "Upload Playbook" to load `.md` files.
    * Click "Create New Playbook" to author a new playbook within the app.
    * Playbooks appear in the section below the controls. Click the playbook title to expand/collapse its content.
    * Within code blocks (` ``` `), click:
        * **Copy**: Copies the code (with variables substituted) to the clipboard.
        * **Execute**: Sends the code (with variables substituted) to the *currently active* terminal tab for execution.
4.  **Search**:
    * Use the search bar to find lines within any loaded playbook's content.
    * Results show the filename, line number, and content. You can copy, execute, or import the full playbook directly from the search results.
5.  **Notes**:
    * Click "Global Notes" or "Tab Notes" in the header to toggle the respective side panels.
    * Content is saved automatically as you type.

## Contributing

Contributions are welcome! Please follow standard fork-and-pull-request workflows.

1.  Fork the repository.
2.  Create your feature branch (`git checkout -b feature/your-feature`).
3.  Commit your changes (`git commit -m 'Add some feature'`).
4.  Push to the branch (`git push origin feature/your-feature`).
5.  Open a Pull Request.

*(Optional: Add more specific contribution guidelines, e.g., code style, testing requirements)*

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

* Built using [Flask](https://flask.palletsprojects.com/), [ttyd](https://github.com/tsl0922/ttyd), and [tmux](https://github.com/tmux/tmux).
* Utilizes [Marked.js](https://marked.js.org/) for Markdown parsing and [Prism.js](https://prismjs.com/) for syntax highlighting.
* Cyberpunk UI inspiration drawn from various synthwave and neon aesthetics.