# Desk Controller

A FastAPI-based application to control a standing desk via Bluetooth Low Energy (BLE).

## Deployment (Raspberry Pi)

### 1. Install System Dependencies

Run the following commands on your Raspberry Pi:

```bash
sudo apt-get update
sudo apt-get install -y bluez dbus libdbus-1-dev libglib2.0-dev
```

### 2. Install Project Dependencies

If you haven't installed `uv`, do so first:
```bash
curl -fsSL https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
```

Then install the project:
```bash
uv sync
```

### 3. Configuration (.env)

Create a `.env` file and add your desk's MAC address:
```bash
echo "DESK_MAC_ADDRESS=XX:XX:XX:XX:XX:XX" > .env
```

### 4. Running the Application

To run the application manually:
```bash
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

### 5. Running in the Background (Recommended)

To keep the application running after closing your terminal, use the provided `systemd` service:

1.  Edit `desk-controller.service` to match your Pi's username and file path.
2.  Copy it to system settings:
    ```bash
    sudo cp desk-controller.service /etc/systemd/system/
    ```
3.  Start and enable it:
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable --now desk-controller
    ```

## Network Access

Access the frontend from any device on your home network at:
`http://<raspberry-pi-ip>:8000`
