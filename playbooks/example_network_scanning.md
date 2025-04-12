# Network Security Scanning Commands

A collection of common network security scanning commands using tools like Nmap, Nikto, and OpenVAS. Set variables like `$TargetIP`, `$PortRange`, and `$ScanIntensity` in the CommandWave UI before executing commands.

## Basic Network Scanning

### Basic Nmap Scan
```bash
nmap $TargetIP
```

### Network Range Scan
```bash
nmap -sn $TargetNetwork/24
```

### Full Port Scan
```bash
nmap -p $PortRange -sV $TargetIP
```

## Advanced Scanning

### Intense Scan with OS Detection
```bash
nmap -T$ScanIntensity -A $TargetIP
```

### Service Version Detection
```bash
nmap -sV --version-intensity 9 $TargetIP
```

### Vulnerability Scanning
```bash
nmap --script vuln $TargetIP
```

## Web Application Scanning

### Nikto Web Scan
```bash
nikto -h $TargetIP
```

### Directory Brute Force
```bash
gobuster dir -u http://$TargetIP -w $Wordlist
```

## Best Practices

- Always obtain proper authorization before scanning targets
- Start with less intrusive scans before running intensive ones
- Document your findings and share with appropriate stakeholders
- Consider network impact when running scans during business hours
