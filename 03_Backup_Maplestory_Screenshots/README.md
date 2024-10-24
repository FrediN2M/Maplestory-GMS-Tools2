# File Backup Script

## Overview

This Python script moves JPEG files that start with "Maple" from a specified game directory to a destination directory. It is designed to work with game clients such as Steam and Nexon, allowing for configurable source paths through a JSON configuration file. The script also logs the moving process and any errors encountered.

## Features

* Moves .jpg files starting with "Maple" from the selected game client directory to a specified destination.
* Handles filename collisions by appending a counter to the new filename.
* Logs details about moved files, including their sizes and total moved file statistics.
* Reads configuration settings from a config.json file.

## Requirements

- Python 3.x
- The following Python packages are required:
- `loguru` (for logging purposes)

You can install `loguru` by running:

```bash
pip install loguru
```

## Configuration

Before running the script, you must create a config.json file. An example configuration file config.json-example is provided in the repository. To use it:

Copy config.json-example to a new file named config.json:

* bash:

      cp config.json-example config.json
    

Edit the config.json file with your desired settings:

    {
      "destination_path": "",
      "use_steam": 1,
      "use_nexon": 0,
      "steam_game_path": "C:\\SteamLibrary\\steamapps\\common\\MapleStory",
      "nexon_game_path": "C:\\maplestory\\appdata"
    }

* destination_path: The directory where the files will be moved. This should be a valid path.
* use_steam: Set to 1 to use the Steam game path, or 0 otherwise, cannot be used with nexon.
* use_nexon: Set to 1 to use the Nexon game path, or 0 otherwise, cannot be used with steam.
* steam_game_path: The path to the directory containing the Steam game files.
* nexon_game_path: The path to the directory containing the Nexon game files.

## Usage

Ensure you have Python and the necessary dependencies installed.

Modify the config.json file to set your desired paths and flags.

Run the script from the command line:

    python script_name.py
Replace script_name.py with the actual name of your script file.

## Logging

The script creates a log file named App_Log_{time}.log in the same directory as the script. This log file contains information about the files moved, errors encountered, and statistics about the operation.

## Error Handling

If the script encounters an issue (e.g., missing configuration file or file access error), it will log an error message to the log file.

## License

This script is open-source. You can modify and distribute it as you see fit.
## Contributing

If you would like to contribute to this project, feel free to submit issues or pull requests.