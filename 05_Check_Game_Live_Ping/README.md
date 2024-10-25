# Server Ping Monitor

`Server Ping Monitor` is a Tkinter-based GUI application for monitoring the ping times of multiple servers in real-time. This tool also supports VPN detection, allowing users to view the active network interface (VPN or standard) being used for the connection. Additional functionalities include exporting log files, updating in-app instructions, and dynamically updating the lowest ping observed per server.

## Features

- **Real-time Server Monitoring**: Track the ping times to multiple servers with live updates.
- **VPN Detection**: Identifies if the active network interface is a VPN connection based on keywords specified in `config.json`.
- **Lowest Ping Tracking**: Displays the lowest ping observed for each server since the last network interface change.
- **Export Log**: Export current data to a log file.
- **Elapsed Time Display**: Shows how long the ping monitoring has been active in `HH:MM:SS.MS` format.
- **Responsive Controls**: Enables/disables controls based on the pinging status.
- **Customizable Settings**: Load server configurations from `game_servers.json` and VPN keywords from `config.json`.

## Installation

1. Clone the repository or download the files to your local machine.
2. Install the required Python packages:

```bash
pip install -r requirements.txt
```


## Configuration

Server Configurations: Ensure that game_servers.json is in the same directory. This file should contain the server IPs and names in JSON format:

    {
        "192.168.1.1": "Server1",
        "192.168.1.2": "Server2"
    }

VPN Detection: Include config.json with a vpn_keywords key to specify VPN identifiers:

    {
        "vpn_keywords": ["ProtonVPN", "VPN"]
    }

## Usage

Run the script:


    python Live_Ping_App.py

* Start Monitoring: Click Start to begin pinging servers.
* Stop Monitoring: Click Stop to end the pinging process.
* Export Log: Save the current ping data to a log file by clicking Export to Log.
* Instructions: For help, click Instructions in the app.

## Interface

    Start/Stop Buttons: Begin or halt the pinging process.
    Elapsed Time Display: Shows the elapsed time since the start of pinging.
    Current Network Interface: Displays the current active interface, with VPN detection if a VPN is connected.
    Ping Table: Real-time updates of the ping and lowest ping values for each server.

## Dependencies

    Python 3.7 or higher
    Tkinter: Included in standard Python installations
    Additional Packages: Listed in requirements.txt

## License
This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## Contributing

If you would like to contribute to this project, feel free to submit issues or pull requests.