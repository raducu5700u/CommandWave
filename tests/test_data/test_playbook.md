# Test Playbook

This is a simple test playbook for testing the CommandWave application.

## Basic Commands

### Echo Test
```bash
echo "Hello, $TestVar"
```

### Network Test
```bash
ping -c 4 $TargetIP
```

## Variable Substitution Tests

### Multiple Variables
```bash
curl http://$TargetIP:$Port/api/endpoint
```

### Special Characters
```bash
grep -E "^[a-zA-Z0-9]+" $FileName | sed 's/$SearchPattern/$ReplacePattern/g'
```
