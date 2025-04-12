# CommandWave: Creating Custom Playbooks

This tutorial will guide you through the process of creating your own custom playbooks to organize and automate your command-line workflows.

## What are Playbooks?

Playbooks in CommandWave are Markdown files that contain organized collections of commands with explanatory text. They allow you to:

- Document complex command sequences
- Share knowledge with team members
- Execute commands directly from the documentation
- Use variables for flexible automation

## Playbook Structure

A well-structured playbook typically includes:

1. **Title and Description** - What the playbook does
2. **Sections** - Organized by task or topic (using ## headings)
3. **Command Blocks** - Executable code sections (using ```bash)
4. **Documentation** - Explanatory text between commands

## Creating a New Playbook

You can create playbooks in two ways:

### 1. Using the Create Playbook Button

```bash
# No command needed - use the interface:
# 1. Click the "Create Playbook" button in the main interface
# 2. Enter a name for your playbook
# 3. Start adding content in the editor
```

### 2. Uploading an Existing Markdown File

```bash
# No command needed - use the interface:
# 1. Click the "Upload Playbook" button
# 2. Select your Markdown file (.md)
```

## Markdown Basics for Playbooks

CommandWave playbooks use standard Markdown syntax:

```bash
# Create a simple example file to demonstrate markdown
cat > example.md << EOF
# Playbook Title

## Section 1
Normal text goes here

### Subsection
More detailed information

\`\`\`bash
# Your commands go here
echo "This is a command block"
\`\`\`
EOF

# View the file
cat example.md
```

## Code Block Best Practices

For command blocks to be most effective:

1. Use ```bash for proper syntax highlighting
2. Include comments to explain complex commands
3. Keep commands focused on single tasks
4. Use variables for values that might change

## Example: Creating a System Info Playbook

Let's create a simple system information playbook as practice:

```bash
# This would be in a Markdown file, not executed directly

# System Information Playbook

## Basic System Info

### System Overview
\`\`\`bash
uname -a
\`\`\`

### Disk Usage
\`\`\`bash
df -h
\`\`\`

### Memory Usage
\`\`\`bash
free -m
\`\`\`

## Process Management

### List Running Processes
\`\`\`bash
ps aux | grep \$PROCESS_NAME
\`\`\`

### Process Resource Usage
\`\`\`bash
top -n 1
\`\`\`
```

## Testing Your Playbook

After creating a playbook:

1. Test each command to ensure it works
2. Verify variable substitution is working
3. Check formatting and readability
4. Consider adding examples of expected output

## Sharing Playbooks

Playbooks can be easily shared with your team:

```bash
# Export your playbooks directory (not executed directly)
# zip -r commandwave_playbooks.zip /path/to/playbooks

# Import received playbooks via the Upload button
```

## Advanced Playbook Tips

- Create playbooks for specific workflows or projects
- Use consistent formatting and structure
- Include error handling and troubleshooting sections
- Document dependencies and prerequisites
