## ⚠️ When Do You Need These Manual Steps?

**You ONLY need these steps if:**
- The Ansible provisioning failed to set up SSH keys automatically (provisioning should now handle this automatically)
- You see errors during provisioning related to SSH key setup

**You DON'T need these steps if:**
- ✅ You paused VMs with `vagrant suspend` - everything persists, just use `vagrant resume`
- ✅ You halted VMs with `vagrant halt` - disk persists, just use `vagrant up` (no destroy)
- ✅ Ansible provisioning completed successfully (SSH keys are now set up automatically during provisioning)

**Note:** The Ansible playbook has been improved to automatically set up SSH keys with proper permissions and distribute them to target servers. If provisioning fails with SSH key errors, use these manual steps as a fallback.

---

## Manual SSH Key Setup (Fallback - Only if provisioning fails)

If Ansible provisioning failed to set up SSH keys properly, use these manual steps:

```bash
vagrant ssh backup-server-auto
```

Then run:
```bash
# Fix permissions on the private key
sudo chmod 600 /var/lib/jenkins/.ssh/id_ed25519
sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/id_ed25519

# Regenerate the public key to match
sudo -u jenkins ssh-keygen -y -f /var/lib/jenkins/.ssh/id_ed25519 > /tmp/id_ed25519.pub
sudo mv /tmp/id_ed25519.pub /var/lib/jenkins/.ssh/id_ed25519.pub
sudo chmod 644 /var/lib/jenkins/.ssh/id_ed25519.pub
sudo chown jenkins:jenkins /var/lib/jenkins/.ssh/id_ed25519.pub

# Get the public key
PUB_KEY=$(sudo cat /var/lib/jenkins/.ssh/id_ed25519.pub)
echo "Public key: $PUB_KEY"

# Add it to all target servers
for ip in 192.168.56.21 192.168.56.22 192.168.56.23; do
  sshpass -p "vagrant" ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null vagrant@$ip "mkdir -p ~/.ssh && echo '$PUB_KEY' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && sort -u ~/.ssh/authorized_keys -o ~/.ssh/authorized_keys"
done

# Verify permissions
ls -la /var/lib/jenkins/.ssh/

# Expected output:
# total 20
# drwxr-xr-x  2 jenkins jenkins 4096 Nov 20 16:25 .
# drwxr-xr-x 15 jenkins jenkins 4096 Nov 20 16:25 ..
# -rw-------  1 jenkins jenkins  400 Nov 20 16:21 id_ed25519
# -rw-r--r--  1 jenkins jenkins   89 Nov 20 16:25 id_ed25519.pub
# -rw-r--r--  1 jenkins jenkins  426 Nov 20 16:24 known_hosts
```

---

## Testing the CI/CD Pipeline

After setup (manual or automated), test the pipeline:
1. Make a code change (e.g., edit `ansible/roles/frontend_container/files/app/app.py`)
2. Commit and push: `git add . && git commit -m "Test CI/CD" && git push`
3. Wait up to 1 minute for Jenkins to detect changes (polling interval: `* * * * *`)
4. Check Jenkins: http://192.168.56.24:8080 (admin/admin)
5. Verify deployment: `curl http://192.168.56.20/` or open in browser

**For comprehensive testing guide, see TESTING_GUIDE.md** 