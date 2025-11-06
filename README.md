# 📡 Mesh-BBS

**Mesh-BBS** is a Python-based Bulletin Board System (BBS) designed to run on a computer (like a Linux PC or Raspberry Pi) connected to a **Meshtastic** node.  
It acts as an automated service, routing commands received over the mesh (like reading messages or playing games) and responding to users.

The system uses **low-bandwidth, multi-packet text messages** to deliver a full, interactive, menu-driven experience.

---

## ✨ Features

- **Menu-Driven Navigation** — Single-letter commands (`B`, `R`, `P`, `M`, `G`, `X`) make system navigation simple and intuitive.  
- **Persistent Message Board** — Users can post and read messages across multiple categories (`General`, `News`, `Tech`, etc.).  
- **Consistent Navigation** — Standardized menu exits (`M` for Main, `B` for Board) ensure a seamless experience.  
- **Chunking Logic** — Automatically splits long replies (like message bodies or game states) into **Meshtastic-safe packets**, and handles multi-part posts.  
- **Games Center** — Includes fun, turn-based games like **Blackjack**.

---

## ⚙️ Installation & Setup

### 1. Prerequisites

You must have **Python 3.9+** and **Git** installed on your system.

---

### 2. Project Setup

Clone or navigate to your project folder:

```bash
cd ~/mesh-bbs
```

---

### 3. Create a Python Virtual Environment

Running this script inside a virtual environment (`venv`) isolates dependencies (like `meshtastic`, `pyserial`, etc.) from system-wide packages.

Create the environment:

```bash
python3 -m venv .venv
```

---

### 4. Activate the Virtual Environment

Activate it **every time** before running or installing dependencies:

```bash
source .venv/bin/activate
```

Your prompt should now look like this:

```bash
(.venv) pi@raspberrypi:~$
```

---

### 5. Install Dependencies

With the virtual environment active, install the required packages:

```bash
pip install -r requirements.txt
```

---

### 6. Run the BBS (Manual Start)

Make sure your **Meshtastic device** is connected via USB and powered on, then run:

```bash
python3 auto_responder.py
```

To enable verbose debug output (for troubleshooting):

```bash
python3 auto_responder.py --debug
```

---

## 🔄 Optional: Run Automatically at Boot

If deploying on a **headless device** (like a Raspberry Pi without monitor/keyboard), use `systemd` to automatically start the script on boot.

---

### 1. Create the Service File

Open the service configuration file using `nano`:

```bash
sudo nano /etc/systemd/system/meshbbs.service
```

Paste the following **exact content** (make sure paths and usernames match your setup):

```ini
[Unit]
Description=Meshtastic BBS Auto Responder
After=network.target

[Service]
# IMPORTANT: This path assumes the project is cloned into the home directory of the 'pi' user.
WorkingDirectory=/home/pi/mesh-bbs
# IMPORTANT: The user executing the script should be the 'pi' user.
User=pi
Group=pi
# Full path to the Python executable INSIDE your virtual environment.
ExecStart=/home/pi/mesh-bbs/.venv/bin/python3 auto_responder.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Save and close with:
```
CTRL + O, Enter, CTRL + X
```

---

### 2. Enable and Start the Service

Reload systemd and enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable meshbbs.service
sudo systemctl start meshbbs.service
```

---

### 3. Check Service Status

Verify the service is running:

```bash
sudo systemctl status meshbbs.service
```

You should see something like:

```
Active: active (running)
```

---

## 📝 License

This project is licensed under the **MIT License**.  
See the [LICENSE](LICENSE) file for details.

