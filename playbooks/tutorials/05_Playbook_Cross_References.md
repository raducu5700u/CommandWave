# Playbook Cross-References

## Overview

CommandWave now allows you to create direct references between playbooks, making it easy to build an interconnected knowledge base. This tutorial explains how to use the new cross-referencing feature to create links between related playbooks.

## Creating Playbook References

To create a link to another playbook, use the special `playbook:` prefix in your markdown links.

### Syntax

```markdown
[Link Text](playbook:playbook_filename.md)
```

For example:
```markdown
See the [Network Setup](playbook:network_setup.md) playbook for more details.
```

When rendered, this creates a special styled button-like link that visually indicates it leads to another playbook.

## Example Usage

Here are some examples of how you might use playbook cross-references:

### Creating a Master Index

```markdown
# Security Tools Collection

## Reconnaissance
- [Port Scanner](playbook:port_scanner.md)
- [DNS Enumeration](playbook:dns_enum.md)
- [Network Mapping](playbook:network_map.md)

## Exploitation
- [SQL Injection](playbook:sql_injection.md)
- [XSS Attacks](playbook:xss_attacks.md)

## Post-Exploitation
- [Privilege Escalation](playbook:priv_esc.md)
- [Data Exfiltration](playbook:data_exfil.md)
```

### Adding References Within Documentation

```markdown
# Kerberos Authentication

## Prerequisites
Before attempting Kerberos authentication, ensure you have:
1. Domain controller information (see [Active Directory Setup](playbook:ad_setup.md))
2. Valid domain credentials 
3. Properly configured DNS (see [DNS Configuration](playbook:dns_config.md))
```

## Benefits of Playbook Cross-References

1. **Improved Organization**: Create logical connections between related content
2. **Better Navigation**: Quickly jump between relevant playbooks
3. **Modular Documentation**: Split complex processes into smaller, focused playbooks
4. **Visual Distinction**: Cross-references are styled differently from regular links

## How It Works

When you click a playbook reference link, CommandWave will:

1. Search for the referenced playbook
2. Load the playbook's content
3. Display it in the interface
4. Maintain the original playbook in view (if multiple playbooks are open)

## Advanced Use: Building Knowledge Trees

You can use cross-references to create hierarchical structures:

```markdown
# Project Documentation

## Overview
This is the root document for the project. Navigate to specific sections:

- [Development Setup](playbook:dev_setup.md)
- [API Documentation](playbook:api_docs.md)
- [Deployment Procedures](playbook:deployment.md)
- [Troubleshooting Guide](playbook:troubleshooting.md)
```

Each of these playbooks can then contain more specific cross-references, creating a tree-like structure of documentation.

## Style Differences by Theme

The appearance of playbook references changes based on your selected theme:

- **Cyberpunk Dark**: Cyan/blue glow effect with neon styling
- **Neon Light**: Modern blue styling with subtle shadow effects
- **Witch Hazel**: Purple accent color with the theme's signature style

## Try It Yourself

Use the editor to create a new playbook that references other playbooks, or modify existing playbooks to add cross-references. This will help you build a more interconnected and navigable collection of documentation.

```bash
# This is just a demo command - it doesn't create references directly
echo "Creating playbook cross-references helps organize your documentation!"
```
