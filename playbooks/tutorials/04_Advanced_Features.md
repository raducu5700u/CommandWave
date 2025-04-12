# CommandWave: Advanced Features

This tutorial covers the more advanced capabilities of CommandWave to help you maximize your productivity.

## Terminal Management

### Managing Multiple Terminals

CommandWave allows you to create and manage multiple terminal sessions simultaneously:

```bash
# No command needed - use the interface to:
# 1. Create terminals with the '+' button
# 2. Switch between them by clicking on tabs
# 3. Rename terminals by right-clicking on a tab
```

### Terminal History

Each terminal maintains its own command history:

```bash
# Press Up Arrow to cycle through previous commands
# Or view history with:
history
```

## Advanced Playbook Features

### Notes Integration

CommandWave provides both global notes and tab-specific notes:

```bash
# No command needed - click "Global Notes" or "Tab Notes" buttons
# Notes are markdown-compatible
```

### Playbook Search

Quickly find commands across all your playbooks:

```bash
# No command needed - use the search box at the top
# Try searching for keywords from your playbooks
```

## Customization Options

### Variable Management

Create complex workflows with custom variables:

```bash
# Define multiple related variables for a workflow
# Example variables for a deployment scenario:
# TARGET_SERVER
# DEPLOY_PATH
# APP_NAME
# VERSION

# Then use them together
ssh $USER@$TARGET_SERVER "mkdir -p $DEPLOY_PATH/$APP_NAME-$VERSION"
```

### Tmux Integration

CommandWave uses tmux under the hood, allowing advanced terminal multiplexing:

```bash
# Split current pane vertically
tmux split-window -v

# Split current pane horizontally
tmux split-window -h

# Navigate between panes
# Ctrl+b arrow-key
```

## Workflow Integration

### Git Workflow Example

```bash
# Clone a repository
git clone $REPO_URL

# Create a new branch
git checkout -b feature/$FEATURE_NAME

# After making changes
git add .
git commit -m "Added $FEATURE_NAME functionality"
git push origin feature/$FEATURE_NAME
```

### Continuous Integration Example

```bash
# Run tests before deployment
cd $PROJECT_DIR
npm test

# If tests pass, deploy
if [ $? -eq 0 ]; then
  npm run deploy
else
  echo "Tests failed, deployment aborted"
fi
```

## Security Features

### Secure Terminal Sessions

```bash
# CommandWave terminal sessions are isolated
# Each terminal has its own environment
```

### Secure Variable Handling

```bash
# For sensitive variables, you can use:
read -s PASSWORD
echo "Password stored securely (not displayed)"
```

## Power User Tips

### Keyboard Shortcuts

CommandWave supports various keyboard shortcuts:

```bash
# Common terminal shortcuts:
# Ctrl+C - Interrupt/cancel current command
# Ctrl+L - Clear screen
# Ctrl+R - Search command history
```

### Command Chaining

Combine multiple commands for efficient workflows:

```bash
# Execute a command only if previous one succeeds
mkdir -p $PROJECT_DIR && cd $PROJECT_DIR && npm init -y

# Execute a command only if previous one fails
ping -c 1 $SERVER || echo "Server unreachable"

# Chain commands regardless of success/failure
git pull; npm install; npm start
```

## Troubleshooting

If you encounter issues with CommandWave:

```bash
# Check if tmux is running
pgrep tmux

# Verify ttyd processes
ps aux | grep ttyd

# Check available ports
netstat -tuln | grep 7681
```
