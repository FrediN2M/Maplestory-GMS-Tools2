# Maplestory GMS Character Channel Monitor
A python script that can help a gamer log his channel changes of his in-game character during his gameplay.

## Table of Contents
- [Installation](#installation)
- [Additional-Configuration](#Additional-Configuration)
- [Usage](#usage)
- [Features](#features)

## Installation
1. Clone the repository locally.
2. Modify the config.json file:
* use_telegram - Optional - Enable sending messages via telegram bot to user(must configure "telegram_bot_token" and "user_chat_id")
* use_webhook - Optional - Enable sending messages via webhook, most common way to send a message(must configure "mUrl" with webhook link.)
* use_steam - 1 or 0, use steam client to open maplestory, cannot be used with nexon launcher.
* use_nexon - 1 or 0, use nexon launcher to open maplestory, cannot be used with steam client.
* steam_exe_path - path to steam client exe file
* nexon_exe_path - path to nexon launcher exe file
3. Modify the game_servers.json file with IPs for each channel.


## Additional-Configuration
1. For slow loading machines, you can add more time to the default loading timer of 30 seconds.
2. Modify Monitor.py and change the following command to add a time parameter, recommended up to 90 seconds
* launcher.monitor_process('MapleStory.exe', 90)

## Usage
1. Open Command/Terminal in the path of the code
2. Type "python Monitor.py" and press enter


## Features
1. Log changes of user channel changes to log file.
2. Send history of channel changes via webhook or telegram.
3. TBD - tkinter UI.

## License
This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
