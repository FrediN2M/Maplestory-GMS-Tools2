import sys
import psutil
import time
import datetime
import subprocess
import json
from loguru import logger
from Notificator import telegram_message, webhook_message
from Utilities import get_registry_value


class MapleStoryLauncher:
    def __init__(self, config):
        self.config = config
        self.prev_ch = None
        self.seen_connections = {}
        self.ch_history = []
        self.start_time_var = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def start_steam_game(self, app_id):
        if self.is_game_running('MapleStory.exe'):
            logger.warning('MapleStory.exe is already running.')
            return
        command = f'"{self.config["steam_exe_path"]}" -applaunch {app_id}'
        subprocess.Popen(command)

    def start_nexon_game(self, app_id):
        if self.is_game_running('MapleStory.exe'):
            logger.warning('MapleStory.exe is already running.')
            return
        command = f'"{self.config["nexon_launcher_path"]}" nxl://launch/{app_id}'
        subprocess.Popen(command)

    def is_game_running(self, game_name):
        return any(p.name() == game_name for p in psutil.process_iter())

    def process_connected(self, local_port, ip_address):
        key_value = get_registry_value(self.config["key_path"], self.config["key_name"])
        current_datetime = datetime.datetime.now()
        cc_time = current_datetime.strftime("%H:%M:%S")
        char_name = key_value if key_value else 'Unknown'

        retry_attempts = 3
        while not key_value and retry_attempts > 0:
            time.sleep(3)  # Wait for 3 seconds before retrying
            key_value = get_registry_value(self.config["key_path"], self.config["key_name"])
            if key_value:
                char_name = key_value
                break
            retry_attempts -= 1

        # Ignore IP address if not found in the dictionary
        if ip_address not in self.config['ip_address_dict']:
            return  # Exit the function without logging anything

        # Proceed with logging if the IP is in the dictionary
        if ip_address in self.seen_connections:
            prev_local_port = self.seen_connections[ip_address]
            if prev_local_port != local_port and ip_address == self.prev_ch:
                msg_print = f"{cc_time} - RC - {self.config['ip_address_dict'][ip_address]} - {char_name}"
                logger.info(msg_print)
                self.ch_history.append(msg_print)
            elif ip_address != self.prev_ch:
                msg_print = f"{cc_time} - CC - {self.config['ip_address_dict'][ip_address]} - {char_name}"
                logger.info(msg_print)
                self.ch_history.append(msg_print)
        elif self.prev_ch is None:
            msg_print = f"{cc_time} - LC - {self.config['ip_address_dict'][ip_address]} - {char_name}"
            logger.info(msg_print)
            self.ch_history.append(msg_print)
        else:
            msg_print = f"{cc_time} - CC - {self.config['ip_address_dict'][ip_address]} - {char_name}"
            logger.info(msg_print)
            self.ch_history.append(msg_print)

        self.prev_ch = ip_address
        self.seen_connections[ip_address] = local_port

    def wait_for_enter_key(self):
        while True:
            user_input = input("Press Enter key to exit: ")
            if user_input == "":
                break

    def monitor_process(self, process_name, initial_wait=30):
        logger.info(f"Waiting for {initial_wait} seconds for {process_name} to start...")
        time.sleep(initial_wait)

        connection_found = False

        while True:
            try:
                # Check for the process
                procs = [proc for proc in psutil.process_iter(['pid', 'name', 'connections']) if proc.info['name'] == process_name]
                if procs:
                    connections = procs[0].connections()
                    new_connection_found = False

                    if connections:
                        for conn in connections:
                            if conn.status == psutil.CONN_ESTABLISHED:
                                connection_tuple = (conn.laddr.ip, conn.laddr.port)
                                if connection_tuple not in self.seen_connections:
                                    new_connection_found = True
                                    self.process_connected(conn.laddr.port, conn.raddr.ip)

                    if new_connection_found and not connection_found:
                        logger.info(f"Connections are established for {process_name}.")
                        connection_found = True

                    if not connections and connection_found:
                        logger.info(f"No established connections found for {process_name}.")
                        connection_found = False

                else:
                    logger.warning("Process not found anymore.")
                    # Send webhook messages
                    if self.config["use_telegram"] == 1:
                        telegram_message(self.config["telegram_api_url"], self.config["telegram_bot_token"], self.config["user_chat_id"], self.start_time_var, self.seen_connections, self.ch_history)
                    if self.config["use_webhook"] == 1:
                        logger.info("Sending webhook message...")
                        webhook_message(self.config["mUrl"], self.start_time_var, self.seen_connections, self.ch_history)
                        logger.info("Webhook message sent.")
                    time.sleep(3)
                    self.wait_for_enter_key()  # Ensure this is called after the webhook message
                    break

                time.sleep(5)  # Adjust sleep duration as needed

            except psutil.NoSuchProcess as e:
                logger.warning(f"Process no longer exists: {e}")
                self.wait_for_enter_key()
                break
            except Exception as e:
                logger.error("An error occurred: {}", e)
                self.wait_for_enter_key()
                break


def load_config():
    try:
        with open('config.json') as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading config: {e}")
        raise


if __name__ == '__main__':
    logger.add("App_Log_{time}.log", rotation="30 days", backtrace=True, enqueue=False, catch=True)

    # Load configuration
    config = load_config()

    # Load additional configuration for IP addresses
    with open('game_servers.json') as json_file:
        config["ip_address_dict"] = json.load(json_file)

    # Create a launcher instance
    launcher = MapleStoryLauncher(config)

    # Start the game based on the configuration
    if config["use_steam"] == 1:
        launcher.start_steam_game(config["steam_game_app_id"])
    elif config["use_nexon"] == 1:
        launcher.start_nexon_game(config["nexon_game_app_id"])
    else:
        logger.error("No launcher selected")
        sys.exit(1)

    # Start monitoring the process, for slow loading machines, you can add the initial_wait parameter and change it to higher time
    launcher.monitor_process('MapleStory.exe')
