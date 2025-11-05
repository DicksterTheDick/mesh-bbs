📡 Meshtastic BBS Auto Responder

This is a Python-based Bulletin Board System (BBS) designed to run on a computer (like a Linux PC or Raspberry Pi) connected to a Meshtastic node. It acts as an automated service, routing commands received over the mesh (like reading messages or playing games) and responding to the user.

The system is designed to use low-bandwidth, multi-packet text messages to deliver a full, interactive, menu-driven experience.

✨ Features

Menu-Driven Navigation: Uses single-letter commands (B, R, P, M, G, X) to navigate the system.

Persistent Message Board: Users can post and read messages across several categorized topics (General, News, Tech, etc.).

Consistent Navigation: All major menu exits use dedicated commands (M for Main, B for Board) for a seamless user experience.

Chunking Logic: Automatically splits long replies (like full message bodies or game boards) into Meshtastic-safe packets (max ~190 chars) and handles multi-part posts from users.

Games Center: Includes simple, turn-based games like Blackjack and Minesweeper.

⚙️ Installation and Setup

1. Prerequisites

You must have Python 3.9 or higher and Git installed on your system.

2. Project Setup

Navigate to your project folder (~/mesh-bbs):

cd ~/mesh-bbs


3. Creating a Python Virtual Environment (venv)

It is highly recommended to run this script within a virtual environment (venv) to isolate its dependencies (meshtastic, pyserial, etc.) from your system's global Python packages.

To Create the Environment:

python3 -m venv .venv


4. Activating the Virtual Environment

You MUST activate this environment every time you want to run or install dependencies for the script.

source .venv/bin/activate


(Your command prompt should now show (.venv) at the beginning, e.g., (.venv) dickster@...)

5. Installing Dependencies

The requirements.txt file lists all necessary Python libraries.

With the virtual environment activated, install the required packages using pip:

pip install -r requirements.txt


6. Running the BBS (Manual Start)

Ensure your Meshtastic device is plugged in via USB and is powered on. Then, run the main script:

python3 auto_responder.py


To see verbose debug information (useful for troubleshooting connection issues), run:

python3 auto_responder.py --debug


🔄 Optional: Running the Script Automatically at Boot

If deploying on a headless device (like a Raspberry Pi) that won't have a monitor or keyboard, you can use a systemd service to ensure the script starts automatically after a reboot.

1. Create the Service File

Using nano, create a new service file:

sudo nano /etc/systemd/system/meshbbs.service


Paste the following content, making sure to replace the placeholder path and username with your actual absolute path and username (e.g., dickster):

[Unit]
Description=Meshtastic BBS Auto Responder
After=network.target

[Service]
# IMPORTANT: Replace /home/dickster/mesh-bbs with the absolute path to your project folder.
WorkingDirectory=/home/dickster/mesh-bbs
# IMPORTANT: Replace dickster with your actual Linux username.
User=dickster 
Group=dickster
# Full path to the Python executable INSIDE your virtual environment.
ExecStart=/home/dickster/mesh-bbs/.venv/bin/python3 auto_responder.py
Restart=always

[Install]
WantedBy=multi-user.target


Save and close the file (Ctrl+O, Enter, Ctrl+X).

2. Enable and Start the Service

Run the following commands to tell systemd about the new service and start it immediately:

# Reload the systemd manager configuration
sudo systemctl daemon-reload

# Enable the service to start automatically on boot
sudo systemctl enable meshbbs.service

# Start the service now
sudo systemctl start meshbbs.service


3. Check Status

To verify the script is running correctly:

sudo systemctl status meshbbs.service


(The status should show "active (running)")

📝 License

This project is licensed under the MIT License. See the LICENSE file for details.
