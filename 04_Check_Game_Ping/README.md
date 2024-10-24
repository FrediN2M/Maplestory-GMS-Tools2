# Ping Check Script for Maplestory Game Servers

## Overview

This script allows you to ping multiple game servers, calculate average ping values, and store the results in JSON log files. 
It also provides additional functionality, such as detecting VPN connections and using the active network or VPN interface to determine which log file to store the data in.

* Important Note: This does not replace ExitLag or similar apps, it might help in a similar way to them by changing the default routing your pc uses to reach game servers. ISPs default routing is usually not optimized for gaming, also ISPs might throttle and use some QoS on all traffic, but VPN should prevent them from doing so. 

## Features

- Pings each game server multiple times to determine an average ping.
- Detects whether the computer is connected through a VPN or a regular network interface.
- Uses the detected network or VPN interface to store log data in corresponding JSON files.
- Compares current average ping with previously recorded minimum and provides feedback on whether the current ping is higher, lower, or equal.
- Saves all historical ping results for each server in a JSON file for analysis.

## Requirements

- Python 3.x
- The following Python packages are required:
  - `psutil` (for detecting network interfaces)

You can install `psutil` by running:

```bash
pip install psutil
```

## Configuration
**config.json**

The config.json file must include the following fields:

* vpn_keywords: A list of keywords to detect active VPN connections. For example:


    {
      "vpn_keywords": ["protonvpn", "openvpn", "vpn", "tunnel"]
    }

This list will be used to check for active VPN connections when determining the network interface.

**game_servers.json**

This file contains a mapping of IP addresses to server names. Example:

    {
      "192.168.1.1": "CH 01",
      "192.168.1.2": "CH 02",
      "192.168.1.3": "Login 1"
    }

## Log Files

Ping results are saved in `log_data_<network_interface>.json` or `log_data_<vpn_interface>.json` files, depending on the active connection.

## Usage

Ensure you have the necessary files (config.json, game_servers.json) and psutil installed.

Run the script:

    python Ping_App.py

The script will:

    Detect whether you're connected via a regular network interface or a VPN.
    Ping all servers listed in game_servers.json.
    Save results in the appropriate log file (log_data_<network_interface>.json or log_data_<vpn_interface>.json).
    Display a comparison between the current and minimum recorded pings for each server.

## Example Output


    Using network interface: Ethernet
    Server: CH 01, Avg Ping: 85 ms, higher than minimum recorded ping (78 ms)
    Server: Login 1, Avg Ping: 120 ms, lower than minimum recorded ping (130 ms)

## Error Handling

If psutil is not installed, the script will exit with the following message:

    psutil is not installed. Please install it using 'pip install psutil'.

Make sure to install the required package to proceed.

## License

This script is open-source. You can modify and distribute it as you see fit.
## Contributing

If you would like to contribute to this project, feel free to submit issues or pull requests.