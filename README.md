# Pi_Inverter

A comprehensive solar inverter monitoring and visualization system for Raspberry Pi 4 with Sense HAT display.

## 📋 Overview

Pi_Inverter is a real-time monitoring system designed to track and visualize solar power production and grid consumption from a Huawei SUN2000-6KTL-M1 inverter. The application provides live data visualization on the Raspberry Pi Sense HAT LED matrix with automatic day/night mode switching and network connectivity monitoring.

## ✨ Key Features

- **Real-time Solar Power Monitoring**: Tracks solar power production via Modbus TCP protocol
- **Grid Consumption Tracking**: Monitors power consumption from/to the electrical grid
- **Dual-Mode Operation**:
  - **Day Mode** (6:00 - 20:00): Real-time power monitoring with animated LED bar charts
  - **Night Mode** (20:00 - 6:00): Historical data visualization and daily energy production display
- **Visual LED Effects**: Advanced wave animations on Sense HAT 8x8 LED matrix
- **Data Logging**: Automatic CSV logging of power readings with daily cleanup
- **Network Watchdog**: Automatic system reboot on prolonged network disconnection
- **Systemd Service Integration**: Runs automatically on system boot
- **Non-invasive Architecture**: Modular design with separated concerns

## 🛠️ Hardware Requirements

- **Raspberry Pi 4 Model B** (Rev 1.5 or later)
  - 8GB RAM recommended
  - ARM 64-bit (aarch64) architecture
  - Running Linux 64-bit OS
- **Sense HAT** add-on board with:
  - 8x8 RGB LED matrix
  - Environmental sensors
- **Huawei SUN2000-6KTL-M1** solar inverter (or compatible)
- **Network connection** to inverter via Ethernet/WiFi

## 📦 Dependencies

### Python Packages
- `pymodbus` - Modbus TCP client for inverter communication
- `sense-hat` - Interface for Raspberry Pi Sense HAT
- `csv` - CSV file handling (built-in)
- `threading` - Multi-threaded operation (built-in)
- `datetime` - Date and time management (built-in)

### System Requirements
- Python 3.7+
- Root/sudo access for systemd service creation
- Network access to inverter IP address

## 🚀 Installation

1. **Clone the repository**:
   ```bash
   cd /home/pi/Python/script
   git clone <repository-url> Pi_Inverter
   cd Pi_Inverter
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install pymodbus sense-hat
   ```

4. **Configure inverter settings**:
   Edit `classi/inverter_monitor.py` to set your inverter IP:
   ```python
   self.INVERTER_IP = "192.168.1.11"  # Change to your inverter IP
   ```

5. **Run the application**:
   ```bash
   sudo python3 rbp4_8gb_inverter.py
   ```

## 📂 Project Structure

```
Pi_Inverter/
├── rbp4_8gb_inverter.py          # Main application entry point
├── README.md                       # This file
├── read.me                         # Additional documentation
├── NETWORK_WATCHDOG_README.md      # Network watchdog documentation
├── network_watchdog_config.json    # Network watchdog configuration
├── last_daily_energy.json          # Cached daily energy production
├── .gitignore                      # Git ignore rules
│
├── classi/                         # Application modules
│   ├── inverter_monitor.py        # Base inverter monitoring class
│   ├── daytime_monitor.py         # Daytime operation mode
│   ├── nighttime_monitor.py       # Nighttime operation mode
│   ├── led_controller.py          # Sense HAT LED matrix control
│   ├── csv_handler.py             # CSV data management
│   ├── apc_monitor.py             # Grid power consumption monitoring
│   ├── network_watchdog.py        # Network connectivity monitoring
│   └── service_manager.py         # Systemd service management
│
└── logs/                           # Data logging directory
    ├── power_log.csv              # Solar power production log
    └── power_cons_log.csv         # Grid consumption log
```

## 🔧 Configuration

### Inverter Settings
Located in `classi/inverter_monitor.py`:
- `INVERTER_IP`: IP address of the inverter (default: `192.168.1.11`)
- `MODBUS_PORT`: Modbus TCP port (default: `502`)
- `POLL_INTERVAL`: Data polling interval in seconds (default: `60`)
- `DAY_START_HOUR`: Start of daytime mode (default: `6`)
- `DAY_END_HOUR`: End of daytime mode (default: `20`)

### Modbus Registers
- `POWER_REGISTER = 32080`: Current power output (32-bit signed integer)
- `DAILY_YIELD_REGISTER = 32114`: Daily energy production (kWh)
- `GRID_POWER_REGISTER = 37113`: Grid power consumption/export

### Network Watchdog
Configure in `network_watchdog_config.json`:
```json
{
  "watchdog": {
    "enabled": true,
    "check_interval": 60,
    "max_failures": 10,
    "ping_timeout": 5,
    "enable_reboot": true,
    "hosts_to_check": ["8.8.8.8", "1.1.1.1"]
  }
}
```

## 📊 Data Logging

### CSV Files
Two CSV files are maintained in the `logs/` directory:

1. **power_log.csv**: Solar power production
   - Format: `YYYY_MM_DD_HH:MM, power_in_watts`
   - Updated every 60 seconds during daytime

2. **power_cons_log.csv**: Grid consumption
   - Format: `YYYY_MM_DD_HH:MM, power_in_kW`
   - Positive values = consuming from grid
   - Negative values = exporting to grid

### Data Retention
- Automatic cleanup runs daily at midnight
- Entries older than 1 year are removed
- Daily energy production cached in `last_daily_energy.json`

## 🎨 LED Display Modes

### Daytime Mode (6:00 - 20:00)
- **Left 4 columns**: Solar power production bar chart
  - Green color indicates good production
  - Yellow/Orange for medium levels
  - Red for low production
  - Animated wave effect based on power level
  
- **Right 4 columns**: Grid consumption bar chart
  - Blue color for power consumption from grid
  - Red color for power export to grid
  - Wave animation proportional to consumption level

- **Text Display**: Alternating messages showing:
  - `Sol: X.X kW` - Current solar production
  - `Rete: X.X kW` - Current grid consumption/export

### Nighttime Mode (20:00 - 6:00)
- **8-column Bar Chart**: Historical power production for the day
  - Each column represents a time period
  - Color gradient from blue (low) to red/green (high)
  
- **Text Display**: Daily energy production
  - `Daily power: X.XX kWh`
  - Updates at predefined hours (20:00, 21:00, 22:00)

## 🔄 Systemd Service

The application automatically creates a systemd service when run as root:

**Service file**: `/etc/systemd/system/rbp4_8gb_inverter.service`

### Service Management Commands
```bash
# Start the service
sudo systemctl start rbp4_8gb_inverter.service

# Stop the service
sudo systemctl stop rbp4_8gb_inverter.service

# Restart the service
sudo systemctl restart rbp4_8gb_inverter.service

# Enable on boot
sudo systemctl enable rbp4_8gb_inverter.service

# Check status
sudo systemctl status rbp4_8gb_inverter.service

# View logs
sudo journalctl -u rbp4_8gb_inverter.service -f
```

## 🌐 Network Watchdog

The integrated network watchdog monitors connectivity and automatically reboots the system if the network is down for an extended period.

### How It Works
1. Checks network connectivity every 60 seconds (configurable)
2. Pings multiple hosts:
   - Local gateway (router)
   - Google DNS (8.8.8.8)
   - Cloudflare DNS (1.1.1.1)
3. If **all** hosts are unreachable → counts as a failure
4. After 10 consecutive failures (≈10 minutes) → system reboot
5. If network recovers → failure counter resets

See `NETWORK_WATCHDOG_README.md` for detailed configuration.

## 🧩 Module Descriptions

### `inverter_monitor.py`
Base class providing:
- Modbus TCP client configuration
- Inverter communication methods
- Register decoding (32-bit signed integers)
- Daily energy tracking
- Retry logic with automatic reconnection

### `daytime_monitor.py`
Handles daytime operation:
- Queries solar power every 60 seconds
- Reads grid consumption from APC monitor
- Logs data to CSV files
- Calculates relative power levels
- Updates dual LED bar charts with wave animations

### `nighttime_monitor.py`
Handles nighttime operation:
- Displays historical power chart
- Shows daily energy production
- Updates cached daily values at specific hours
- Alternates between graph and text display

### `led_controller.py`
Manages Sense HAT LED matrix:
- Advanced wave animation effects
- Dual bar chart visualization
- Color gradient calculations
- Dynamic brightness based on power levels
- Message scrolling with configurable speed

### `csv_handler.py`
CSV file operations:
- Reading and parsing CSV data
- Appending new records
- Daily cleanup (removes entries > 1 year old)
- Calculating bar chart values from historical data
- Error handling with user feedback

### `apc_monitor.py`
Grid power monitoring:
- Reads grid consumption via Modbus register 37113
- Decodes 32-bit signed values
- Returns power in kW
- Retry logic for reliability

### `network_watchdog.py`
Network connectivity monitoring:
- Threaded background operation
- Multi-host ping checks
- Configurable thresholds
- Automatic system reboot
- Detailed logging

### `service_manager.py`
Systemd integration:
- Creates service file automatically
- Configures proper paths and permissions
- Enables auto-start on boot
- Manages service lifecycle

## 📈 Performance

- **CPU Usage**: ~2-5% on Raspberry Pi 4 (8GB)
- **Memory**: ~50-80 MB
- **Network**: Minimal bandwidth (periodic Modbus queries)
- **Storage**: CSV files grow ~1 MB per month (auto-cleanup enabled)

## 🐛 Troubleshooting

### Common Issues

**1. Inverter connection failed**
- Verify inverter IP address in configuration
- Check network connectivity: `ping 192.168.1.11`
- Ensure Modbus TCP is enabled on inverter
- Check firewall rules

**2. Sense HAT not responding**
- Verify Sense HAT is properly connected
- Check I2C is enabled: `sudo raspi-config` → Interface Options → I2C
- Test with: `python3 -c "from sense_hat import SenseHat; s = SenseHat(); s.show_message('OK')"`

**3. CSV files not updating**
- Check file permissions: `ls -la logs/`
- Verify disk space: `df -h`
- Check logs for errors: `sudo journalctl -u rbp4_8gb_inverter.service`

**4. Service not starting on boot**
- Enable service: `sudo systemctl enable rbp4_8gb_inverter.service`
- Check service status: `sudo systemctl status rbp4_8gb_inverter.service`
- View service logs: `journalctl -xe`

**5. Network watchdog causing unexpected reboots**
- Increase `max_failures` in `network_watchdog_config.json`
- Increase `check_interval` for less frequent checks
- Disable temporarily: Set `"enabled": false` in config

## 🔐 Security Considerations

- Application requires root access for:
  - Systemd service file creation
  - System reboot capability (network watchdog)
  - Sense HAT hardware access
- Modbus TCP communication is **unencrypted**
- Recommended to run on isolated network segment
- No external internet exposure required (except for network watchdog ping tests)

## 📝 License

[Specify your license here]

## 👤 Author

[Your name/organization]

## 🙏 Acknowledgments

- Huawei for inverter Modbus documentation
- Raspberry Pi Foundation for Sense HAT libraries
- PyModbus project for Modbus TCP implementation

## 📞 Support

For issues, questions, or contributions, please [specify contact method or issue tracker].

---

**Last Updated**: November 2025  
**Version**: 1.0  
**Compatible with**: Raspberry Pi 4 Model B, Sense HAT, Huawei SUN2000 series inverters
