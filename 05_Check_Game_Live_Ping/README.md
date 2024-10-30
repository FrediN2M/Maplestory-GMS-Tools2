# Server Ping Monitor

## Overview

The **Server Ping Monitor** is a Python application that allows users to monitor the ping times of multiple servers. It provides real-time updates on server status, including the lowest, average, and failed pings. The application also detects ping spikes and tracks network interface changes, making it a valuable tool for network administrators and gamers alike.

## Features

- **Server Monitoring**: Continuously pings multiple servers and displays their current ping times.
- **Spike Detection**: Identifies and logs spikes in ping times (15% over average).
- **User Interface**: Built with Tkinter for a user-friendly GUI that displays ping statistics in a table format.
- **Logging**: Exports log data to a file for later analysis.
- **VPN Detection**: Automatically detects if a VPN is in use based on keywords in network interfaces.
- **Customizable**: Supports easy modification of monitored servers via a JSON configuration file.

## Installation

To run the Server Ping Monitor, ensure you have Python 3 installed on your machine. You will also need the following packages:

- `tkinter` (included with standard Python installations)
- `concurrent.futures` (included with standard Python installations)
- `psutil` (for network interface handling)
- `loguru` (for logging)

You can install `psutil` and `loguru` using pip:

```bash
pip install psutil loguru
```

## Usage

1. **Configuration**:
   - Create a file named `game_servers.json` in the same directory as the application. This file should contain a JSON object with server IPs and their names. For example:
   `json
   {
       "192.168.1.1": "Game Server 1",
       "192.168.1.2": "Game Server 2"
   }
   `
   - Create a `config.json` file with VPN keywords:
   `json
   {
       "vpn_keywords": ["vpn", "secure", "private"]
   }
   `

2. **Running the Application**:
   - Execute the script:
   `python server_ping_monitor.py`

3. **Using the GUI**:
   - Click the **Start** button to begin monitoring.
   - Click the **Stop** button to halt the monitoring process.
   - Use the **Export to Log** button to save the ping data to a log file.
   - Click **Information** for a brief description of the application’s features.

## Logging

The application logs activities and errors to a file named `App_Log_<date>.log`, which can be helpful for troubleshooting. It also provides a structured log export for the monitored servers.

## Conclusion

The Server Ping Monitor is an effective tool for keeping track of server performance and ensuring network reliability. Feel free to modify the code and configuration files to suit your needs.

## License

This project is open-source and available for modification. Please adhere to the MIT License for any distributions.
