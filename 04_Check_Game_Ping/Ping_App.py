import json
import socket
import time
import concurrent.futures
import os
import psutil  # Requires installation: pip install psutil
from loguru import logger


# Function to check the default active network interface or VPN
def get_default_network_interface():
    try:
        # Get the active connections
        active_connections = psutil.net_if_stats()

        for interface, stats in active_connections.items():
            if stats.isup:  # Check if the interface is up
                for keyword in vpn_keywords:  # Check if the interface name contains any VPN keyword
                    if keyword.lower() in interface.lower():
                        return interface  # VPN detected
                return interface  # Non-VPN active interface
        return "unknown_interface"

    except (psutil.Error, Exception) as e:
        # Handle psutil-specific errors or other potential exceptions
        logger.error(f"Error occurred while fetching network interface: {e}")
        return "error_fetching_interface"


# Function to check if the server is reachable on the specified port
def ping_server(ip, port=8585, timeout=1):
    total_time = 0
    successful_pings = 0

    try:
        for _ in range(10):  # Perform 10 connection attempts
            start_time = time.time()
            try:
                with socket.create_connection((ip, port), timeout) as sock:
                    pass  # Connection successful
                total_time += (time.time() - start_time)
                successful_pings += 1
            except (socket.timeout, socket.error):
                continue  # Ignore failed connection attempts

        if successful_pings > 0:
            avg_ping = round((total_time / successful_pings) * 1000)  # Convert to ms and round to int
        else:
            avg_ping = "N/A"  # No successful pings

    except Exception as e:
        # Catch any other unforeseen errors
        logger.error(f"Error occurred while pinging {ip}:{port} - {e}")
        return ip, "error"

    return ip, avg_ping


# Ping all servers and get results
def ping_all_servers(servers):
    results = []

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
            futures = []
            for ip, server_name in servers.items():
                try:
                    # Determine port based on server name
                    if "Login" in server_name:
                        port = 8484
                    elif server_name in ["AH", "CS"]:
                        port = 8786
                    else:
                        port = 8585

                    futures.append(executor.submit(ping_server, ip, port))
                except Exception as e:
                    logger.error(f"Error while submitting ping task for server {server_name} ({ip}): {e}")
                    results.append((server_name, "error"))

            try:
                for future in concurrent.futures.as_completed(futures):
                    try:
                        ip, avg_ping = future.result()
                        server_name = servers[ip]
                        results.append((server_name, avg_ping))
                    except Exception as e:
                        # Catch any exception that occurs during ping_server
                        logger.error(f"Error occurred while pinging server {server_name} ({ip}): {e}")
                        results.append((servers[ip], "error"))
            except KeyboardInterrupt:
                logger.info("\nPinging interrupted by user.")
                executor.shutdown(wait=False)
                return results

    except Exception as e:
        logger.error(f"Error occurred during thread pool execution: {e}")
        return []

    return results


# Update the log data with the latest pings, calculate averages, and track minimum ping
def update_log_data(log_data, server_name, avg_ping):
    try:
        # If the server name is not already in log_data, initialize its structure
        if server_name not in log_data:
            log_data[server_name] = {
                f"{server_name}_previous_pings": [],
                f"{server_name}_avg": 0,
                f"{server_name}_min": float('inf')  # Set initial min value to a very high number
            }

        # Only update if avg_ping is valid (not "N/A")
        if isinstance(avg_ping, (int, float)):
            # Update previous pings
            log_data[server_name][f"{server_name}_previous_pings"].append(avg_ping)

            # Recalculate the average
            total_pings = log_data[server_name][f"{server_name}_previous_pings"]
            log_data[server_name][f"{server_name}_avg"] = round(sum(total_pings) / len(total_pings))

            # Update the minimum ping if the current one is lower
            log_data[server_name][f"{server_name}_min"] = min(log_data[server_name][f"{server_name}_min"], avg_ping)
        else:
            logger.warning(f"Invalid ping value '{avg_ping}' for server {server_name}. Skipping update.")

    except Exception as e:
        logger.error(f"Error updating log data for server {server_name}: {e}")


# Custom sorting function for the server names
def sort_servers(results):
    def server_sort_key(result):
        server_name = result[0]
        try:
            if server_name.startswith("CH"):
                # Ensure we handle cases where 'CH' might not be followed by a number
                number_part = server_name.split()[1]
                return (0, int(number_part))  # Sort CH servers first by their number
            elif server_name == "AH":
                return (1, 0)  # AH next
            elif server_name == "CS":
                return (2, 0)  # CS next
            else:
                return (3, server_name)  # Sort others alphabetically
        except (IndexError, ValueError) as e:
            # Handle cases where the server name format is unexpected (e.g., "CH" without a number)
            logger.warning(f"Unexpected server name format '{server_name}': {e}")
            return (4, server_name)  # Sort these last

    return sorted(results, key=server_sort_key)


# Save results to the appropriate log_data_<network_interface>.json file
def save_results_to_log(results, network_interface):
    log_file = f'log_data_{network_interface}.json'

    try:
        # Check if the log file exists, create it if it doesn't
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump({}, f)  # Create an empty JSON object
                logger.info(f"Created new log file: {log_file}")

        # Load existing log data
        with open(log_file, 'r') as f:
            try:
                log_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error decoding JSON from {log_file}: {e}")
                log_data = {}  # Fallback to an empty log_data if the file is corrupted

        # Update log data with the current results
        for server_name, avg_ping in results:
            update_log_data(log_data, server_name, avg_ping)

        # Save the updated log data back to the file
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=4)
            # logger.info(f"Successfully updated log file: {log_file}")

    except IOError as e:
        logger.error(f"File operation failed for {log_file}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error occurred while saving results: {e}")


# Print comparison between current and previous average pings
def print_comparison(log_data, server_name, avg_ping):
    # Ensure that the server exists in log_data, otherwise initialize it
    if server_name not in log_data:
        log_data[server_name] = {
            f"{server_name}_previous_pings": [],
            f"{server_name}_avg": 0,
            f"{server_name}_min": float('inf')  # Set initial min to a high value for new entries
        }

    recorded_min = log_data[server_name][f"{server_name}_min"]

    # Ensure avg_ping is valid for comparison
    if avg_ping == "N/A":
        logger.info(f"Server: {server_name}, Avg Ping: {avg_ping}")
        return

    try:
        # Convert avg_ping and recorded_min to numeric values if they are not
        if isinstance(recorded_min, str):
            recorded_min = float('inf')  # Treat "N/A" or invalid values as a very high number

        if isinstance(avg_ping, (int, float)):
            # Comparison logic
            if avg_ping > recorded_min:
                logger.info(f"Server: {server_name}, Avg Ping: {avg_ping} ms, higher than minimum recorded ping ({recorded_min} ms)")
            elif avg_ping < recorded_min:
                logger.info(f"Server: {server_name}, Avg Ping: {avg_ping} ms, lower than minimum recorded ping ({recorded_min} ms)")
            else:
                logger.info(f"Server: {server_name}, Avg Ping: {avg_ping} ms, equal to minimum recorded ping ({recorded_min} ms)")
        else:
            logger.warning(f"Invalid avg_ping value '{avg_ping}' for server {server_name}")
    except Exception as e:
        logger.error(f"Error comparing pings for server {server_name}: {e}")


def load_configuration_files():
    try:
        # Load the config.json to get VPN keywords
        with open('config.json', 'r') as f:
            config = json.load(f)

        vpn_keywords = config.get('vpn_keywords', ['vpn'])  # Default to ['vpn'] if not found
        # logger.info(f"Loaded VPN keywords: {vpn_keywords}")

    except FileNotFoundError:
        logger.error("Configuration file 'config.json' not found. Using default VPN keywords ['vpn'].")
        vpn_keywords = ['vpn']  # Default value if the config file is missing
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from 'config.json': {e}")
        vpn_keywords = ['vpn']  # Default value in case of a decode error

    try:
        # Load the IPs and server names from game_servers.json
        with open('game_servers.json', 'r') as f:
            servers = json.load(f)
        # logger.info(f"Loaded game servers: {servers}")

    except FileNotFoundError:
        logger.error("Configuration file 'game_servers.json' not found. Returning empty server list.")
        servers = {}  # Return an empty dictionary if the file is missing
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from 'game_servers.json': {e}")
        servers = {}  # Return an empty dictionary in case of a decode error

    return vpn_keywords, servers


if __name__ == "__main__":
    logger.add("App_Log.log", rotation="30 days", backtrace=True, enqueue=False, catch=True)

    try:
        # Load Config and Servers
        vpn_keywords, servers = load_configuration_files()

        # Get the default active network interface or VPN
        network_interface = get_default_network_interface()
        logger.info(f"Using network interface: {network_interface}")

        # Ping all servers
        results = ping_all_servers(servers)
        sorted_results = sort_servers(results)

        # Load existing log data (create if necessary)
        log_file = f'log_data_{network_interface}.json'

        try:
            if not os.path.exists(log_file):
                with open(log_file, 'w') as f:
                    json.dump({}, f)  # Create an empty JSON object

            with open(log_file, 'r') as f:
                log_data = json.load(f)

        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading log data from {log_file}: {e}")
            log_data = {}  # Start with an empty log data structure

        # Print and compare results
        for server_name, avg_ping in sorted_results:
            print_comparison(log_data, server_name, avg_ping)

        # Save results to log_data_<network_interface>.json
        save_results_to_log(sorted_results, network_interface)

    except KeyboardInterrupt:
        logger.info("\nGracefully exiting...")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
