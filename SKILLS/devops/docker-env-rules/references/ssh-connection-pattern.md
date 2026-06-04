# SSH Connection Pattern for Remote Servers

## Session: June 3, 2026 — hermes-demo (158.160.4.7)

### Key setup
- Private key stored at `/tmp/hermes-ssh/id_ed25519` (temporary location during session)
- User: `hermes`
- Server hostname: `hermes-demo`
- SSH flags: `-o StrictHostKeyChecking=no -i <key>`

### Common command patterns

**Test connectivity:**
```bash
ssh -i <key> -o StrictHostKeyChecking=no hermes@<ip> 'hostname'
```

**Run multi-command diagnostic:**
```bash
ssh -i <key> hermes@<ip> 'uname -a && cat /etc/os-release | head -5 && df -h / && free -h'
```

**Transfer files + execute:**
```bash
scp -i <key> local_file hermes@<ip>:~/target_dir/
ssh -i <key> hermes@<ip> 'cd ~/target_dir && bash script.sh'
```

### Important notes
- Keys stored in `/tmp/` are ephemeral — only survive the container session
- For persistent access, store keys in `/opt/data/.ssh/` (user-writable)
- Always use `StrictHostKeyChecking=no` on first connection to avoid interactive prompt
- Use `newgrp docker` after adding user to docker group (takes effect in new shell)
