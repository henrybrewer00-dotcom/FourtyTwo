# Oracle Cloud Always Free Setup (True 24/7 Hosting)

## Why Oracle Cloud?
- ✅ **FREE FOREVER** (Oracle's permanent commitment)
- ✅ **Never sleeps** (true always-on VPS)
- ✅ **No 30-second wait** (instant access)
- ✅ **4 ARM CPUs, 24GB RAM** (insanely powerful)
- ✅ **Global access** (choose US region)

## Step-by-Step Setup (30 minutes)

### 1. Create Oracle Cloud Account

1. Go to https://www.oracle.com/cloud/free/
2. Click "Start for free"
3. Fill in details (requires credit card for verification, NEVER charged)
4. Verify email
5. Log in to console

### 2. Create a VM Instance

1. **Navigate:** Menu → Compute → Instances
2. Click **"Create Instance"**

3. **Configure:**
   - Name: `game42-server`
   - Placement: Keep default
   - Image: **Ubuntu 22.04** (click "Change Image" if needed)
   - Shape: Click "Change Shape"
     - Select **"Ampere"** (ARM processor)
     - Choose **VM.Standard.A1.Flex**
     - OCPUs: **2** (can use up to 4 for free!)
     - Memory: **12 GB** (can use up to 24 GB for free!)
   - Networking: Keep default (creates VCN automatically)
   - **IMPORTANT:** Download SSH keys or paste your public key
   - Click **"Create"**

4. **Wait 2-3 minutes** for VM to start

5. **Get Public IP:**
   - Copy the "Public IP address" (e.g., `123.45.67.89`)

### 3. Configure Firewall (Allow Traffic)

**In Oracle Cloud Console:**

1. Go to your Instance details
2. Click on the VCN (Virtual Cloud Network) name
3. Click "Security Lists" → "Default Security List"
4. Click "Add Ingress Rules"
5. **Add this rule:**
   - Source CIDR: `0.0.0.0/0`
   - Destination Port: `8080`
   - Description: `Game 42 Server`
6. Click "Add Ingress Rules"

**On the VM itself (after SSH):**
```bash
sudo ufw allow 8080
sudo ufw allow OpenSSH
sudo ufw enable
```

### 4. SSH into Your Server

From your computer:
```bash
ssh ubuntu@YOUR_PUBLIC_IP
```

(If using downloaded SSH key):
```bash
ssh -i path/to/private-key ubuntu@YOUR_PUBLIC_IP
```

### 5. Install Dependencies

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and Git
sudo apt install python3 python3-pip git -y

# Clone your repository
cd ~
git clone https://github.com/henrybrewer00-dotcom/FourtyTwo.git
cd FourtyTwo

# Install Python packages
pip3 install -r requirements.txt
```

### 6. Set Up as System Service (Auto-Start)

```bash
# Copy service file to systemd
sudo cp game42.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable game42

# Start service now
sudo systemctl start game42

# Check status
sudo systemctl status game42
```

You should see "active (running)" in green!

### 7. Test Your Server

Open browser and go to:
```
http://YOUR_PUBLIC_IP:8080
```

You should see your game! 🎉

### 8. Optional: Set Up Domain Name

**Using Cloudflare (Free):**

1. Buy a domain (or use existing)
2. Add to Cloudflare (free tier)
3. Add DNS A record:
   - Name: `@` (or `game42`)
   - Type: `A`
   - Content: `YOUR_PUBLIC_IP`
   - TTL: Auto
   - Proxy status: ☁️ Proxied (for free DDoS protection)

4. Access your game at: `https://yourdomain.com` 🚀

---

## Useful Commands

**View logs:**
```bash
sudo journalctl -u game42 -f
```

**Restart service:**
```bash
sudo systemctl restart game42
```

**Stop service:**
```bash
sudo systemctl stop game42
```

**Update code:**
```bash
cd ~/FourtyTwo
git pull
sudo systemctl restart game42
```

---

## Firewall Rules Summary

**Oracle Cloud Console:**
- Ingress: Port 8080 from 0.0.0.0/0

**VM Firewall (ufw):**
```bash
sudo ufw allow 8080
sudo ufw allow OpenSSH
```

---

## Performance

**Your free VM can handle:**
- 100+ concurrent players
- Thousands of games per day
- Multiple simultaneous games

**Monitoring:**
```bash
# CPU usage
htop

# Memory usage
free -h

# Disk usage
df -h
```

---

## Cost

**$0 FOREVER**

Oracle's Always Free tier includes:
- 4 ARM CPUs (you can use 2-4)
- 24 GB RAM (you can use 12-24)
- 200 GB storage
- Generous network bandwidth

**This is permanent.** Oracle won't charge you as long as you stay within Always Free limits.

---

## Troubleshooting

**Service won't start:**
```bash
# Check logs
sudo journalctl -u game42 -n 50

# Check if port is in use
sudo lsof -i :8080

# Try running manually
cd ~/FourtyTwo
python3 app.py
```

**Can't access from browser:**
- Check Oracle Cloud firewall rules (Ingress on port 8080)
- Check VM firewall: `sudo ufw status`
- Check service is running: `sudo systemctl status game42`
- Try: `curl localhost:8080` from SSH (should work)

**Database errors:**
```bash
cd ~/FourtyTwo
python3 init_db.py
sudo systemctl restart game42
```

---

## Security Recommendations

1. **Update regularly:**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Monitor logs:**
   ```bash
   sudo journalctl -u game42 -f
   ```

3. **Backup database:**
   ```bash
   cp game.db game.db.backup
   ```

---

## Result

✅ **24/7 uptime** - Never sleeps
✅ **Instant access** - No wait time
✅ **Free forever** - Oracle commitment
✅ **Global access** - Works worldwide
✅ **Your own VPS** - Full control

Perfect for serious game hosting! 🎲
