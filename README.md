# GPU Temperature Monitor 🌡️

A Python-based GPU temperature monitoring service that alerts you via Rocket.Chat webhook when GPU temperatures exceed specified thresholds.

## Features

- 🔍 **Real-time GPU monitoring** - Uses `nvidia-smi` to track GPU temperatures
- 🚨 **Threshold alerts** - Sends notifications when temperature exceeds configured limits
- 💬 **Rocket.Chat integration** - Delivers formatted alerts to your Rocket.Chat channels
- 🔄 **Auto-retry logic** - Handles network interruptions gracefully
- 📝 **Comprehensive logging** - Tracks all events in `service.log`
- 🌍 **Timezone support** - Timestamps in Asia/Tehran timezone (configurable)

## Prerequisites

- Python 3.10+
- NVIDIA GPU with `nvidia-smi` installed
- Rocket.Chat webhook URL
- Required Python packages:
  ```bash
  pip install requests pytz
  ```

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install requests pytz
   ```
3. Make the bash script executable:
   ```bash
   chmod +x script.sh
   ```

## Configuration

Edit the constants in `gpu_tmp.py`:

```python
WEBHOOK_URL = "<YOUR WEB_HOOK>"  # Your Rocket.Chat webhook URL
THRESHOLD = 70                    # Temperature threshold in °C
INTERVAL = "50s"                  # Retry interval (supports: ms, s, min, h)
RETRY = 10                        # Number of retry attempts
LOG_PATH = "service.log"          # Log file path
```

## Usage

Run the monitoring script:

```bash
python gpu_tmp.py
```

### Running as a Service

For continuous monitoring, set up as a systemd service:

1. Create `/etc/systemd/system/gpu-temp-monitor.service`:
   ```ini
   [Unit]
   Description=GPU Temperature Monitor
   After=network.target

   [Service]
   Type=oneshot
   WorkingDirectory=/home/amin/Desktop/temp_gpu
   ExecStart=/usr/bin/python3 /home/amin/Desktop/temp_gpu/gpu_tmp.py
   User=your-username
   Restart=on-failure

   [Install]
   WantedBy=multi-user.target
   ```

2. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable gpu-temp-monitor.service
   sudo systemctl start gpu-temp-monitor.service
   ```

## How It Works

1. **Temperature Check**: Executes `script.sh` which queries `nvidia-smi` for GPU temperatures
2. **Threshold Comparison**: Compares each GPU's temperature against `THRESHOLD`
3. **Alert Dispatch**: If threshold exceeded, sends formatted alert to Rocket.Chat
4. **Retry Logic**: On network failure, retries `RETRY` times with `INTERVAL` delay
5. **Logging**: All activities logged to `service.log`

## Alert Format

Alerts include:
- 🖥️ Server name
- 🎮 GPU model
- 🌡️ Current temperature
- ⏰ Timestamp

## File Structure

```
temp_gpu/
├── gpu_tmp.py       # Main Python script
├── script.sh        # Bash script to query nvidia-smi
├── service.log      # Runtime logs
├── app.log          # Application logs
└── README.md        # This file
```

## Troubleshooting

### nvidia-smi not found
Ensure NVIDIA drivers are installed:
```bash
nvidia-smi
```

### Webhook not working
- Verify your Rocket.Chat webhook URL is correct
- Check network connectivity to Rocket.Chat server

### Permission denied
Make sure `script.sh` is executable:
```bash
chmod +x script.sh
```

## License

Open source - feel free to modify and use as needed.

## Contributing

Contributions welcome! Feel free to submit issues or pull requests.
