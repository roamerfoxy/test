# Desk Controller

A FastAPI-based application to control a standing desk via Bluetooth Low Energy (BLE).

## Deployment

### Docker (Recommended)

To deploy on a Raspberry Pi:

1.  Clone this repository.
2.  Set your desk's MAC address in `.env`:
    ```env
    DESK_MAC_ADDRESS=XX:XX:XX:XX:XX:XX
    ```
3.  Run with Docker Compose:
    ```bash
    docker compose up -d
    ```

The application will be available at `http://<raspberry-pi-ip>:8000`.

### Manual Deployment

1.  Install system dependencies:
    ```bash
    sudo apt-get update
    sudo apt-get install -y bluez dbus libdbus-1-dev libglib2.0-dev
    ```
2.  Install dependencies and run:
    ```bash
    uv sync
    uvicorn main:app --host 0.0.0.0 --port 8000
    ```

## Network Access

To access the frontend from another device on your home network, navigate to the Raspberry Pi's local IP address on port 8000. For example: `http://192.168.1.100:8000`.
