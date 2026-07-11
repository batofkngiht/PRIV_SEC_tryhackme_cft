# 🎯 Willow Tree CTF - TryHackMe

![Platform](https://img.shields.io/badge/Platform-TryHackMe-blue)
![Difficulty](https://img.shields.io/badge/Difficulty-Medium-yellow)
![Category](https://img.shields.io/badge/Category-Privilege%20Escalation-orange)

---

## 📋 Table of Contents
- [Overview](#overview)
- [Tools Used](#tools-used)
- [Reconnaissance](#reconnaissance)
- [Enumeration](#enumeration)
- [Initial Access](#initial-access)
- [Privilege Escalation](#privilege-escalation)
- [Flags](#flags)
- [Lessons Learned](#lessons-learned)

---

## 🔍 Overview
**Room:** Willow Tree  
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** Privilege Escalation, Cryptography

**Brief Description:**  
This CTF involved scanning for open ports, finding an exposed NFS share, decrypting RSA keys, cracking an SSH private key, escalating privileges via sudo misconfiguration, and extracting hidden data using steghide.

---

## 🛠️ Tools Used
| Tool | Purpose |
|------|---------|
| Nmap | Port scanning and service enumeration |
| Gobuster | Directory/file brute forcing (if used) |
| CyberChef | RSA decryption and hex decoding |
| showmount | NFS share enumeration |
| mount | Mounting NFS shares |
| Python | Custom RSA decryption script |
| ssh2john | Converting SSH key to John format |
| John the Ripper | Cracking SSH key passphrase |
| SSH | Remote access to target |
| Steghide | Extracting hidden data from images |

---

## 🔍 Reconnaissance

### Nmap Scan
**Command:**
```bash
nmap -sV 10.48.178.179
