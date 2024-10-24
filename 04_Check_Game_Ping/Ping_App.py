import json
import socket
import time
import concurrent.futures
import os
import psutil  # Requires installation: pip install psutil


# Function to check the default active network interface or VPN
def get_default_network_interface():
    # Get the default network interface based on active connections
    addrs = psutil.net_if_addrs()
    active_connections = psutil.net_if_stats()

    for interface, stats in active_connections.items():
        if stats.isup:  # Check if the interface is up
            for keyword in vpn_keywords:  # Check if the interface name contains any VPN keyword
                if keyword.lower() in interface.lower():
                    return interface  # VPN detected
            return interface
    return "unknown_interface"


# Function to check if the server is reachable on the specified port
def ping_server(ip, port=8585, timeout=1):
    total_time = 0
    successful_pings = 0
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

    return ip, avg_ping


# Ping all servers and get results
def ping_all_servers(servers):
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
        futures = []
        for ip, server_name in servers.items():
            if "Login" in server_name:
                port = 8484
            elif server_name in ["AH", "CS"]:
                port = 8786
            else:
                port = 8585

            futures.append(executor.submit(ping_server, ip, port))

        try:
            for future in concurrent.futures.as_completed(futures):
                ip, avg_ping = future.result()
                server_name = servers[ip]
                results.append((server_name, avg_ping))
        except KeyboardInterrupt:
            print("\nPinging interrupted by user.")
            executor.shutdown(wait=False)
            return results

    return results


# Update the log data with the latest pings, calculate averages, and track minimum ping
def update_log_data(log_data, server_name, avg_ping):
    # If the server name is not already in log_data, initialize its structure
    if server_name not in log_data:
        log_data[server_name] = {
            f"{server_name}_previous_pings": [],
            f"{server_name}_avg": 0,
            f"{server_name}_min": float('inf')  # Set initial min value to a very high number
        }

    # Update previous pings
    if avg_ping != "N/A":
        log_data[server_name][f"{server_name}_previous_pings"].append(avg_ping)
        # Recalculate the average
        total_pings = log_data[server_name][f"{server_name}_previous_pings"]
        log_data[server_name][f"{server_name}_avg"] = round(sum(total_pings) / len(total_pings))

        # Update the minimum ping if the current one is lower
        log_data[server_name][f"{server_name}_min"] = min(log_data[server_name][f"{server_name}_min"], avg_ping)


# Custom sorting function for the server names
def sort_servers(results):
    def server_sort_key(result):
        server_name = result[0]
        if server_name.startswith("CH"):
            return (0, int(server_name.split()[1]))  # Sort CH servers first
        elif server_name == "AH":
            return (1, 0)  # AH next
        elif server_name == "CS":
            return (2, 0)  # CS last
        else:
            return (3, server_name)  # Sort others alphabetically

    return sorted(results, key=server_sort_key)


# Save results to the appropriate log_data_<network_interface>.json file
def save_results_to_log(results, network_interface):
    log_file = f'log_data_{network_interface}.json'

    # Check if the log file exists, create it if it doesn't
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f:
            json.dump({}, f)  # Create an empty JSON object

    # Load existing log data
    with open(log_file, 'r') as f:
        log_data = json.load(f)

    # Update log data with the current results
    for server_name, avg_ping in results:
        update_log_data(log_data, server_name, avg_ping)

    # Save the updated log data back to the file
    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=4)


# Print comparison between current and previous average pings
def print_comparison(log_data, server_name, avg_ping):
    # Ensure that the server exists in log_data, otherwise initialize it
    if server_name not in log_data:
        log_data[server_name] = {
            f"{server_name}_previous_pings": [],
            f"{server_name}_avg": 0,
            f"{server_name}_min": "N/A"
        }

    recorded_min = log_data[server_name][f"{server_name}_min"]

    # Comparison logic with a check for the previous average being 0 (no previous pings)
    if avg_ping == "N/A":
        print(f"Server: {server_name}, Avg Ping: {avg_ping}")
    elif avg_ping > recorded_min:
        print(f"Server: {server_name}, Avg Ping: {avg_ping} ms, higher than minimum recorded ping ({recorded_min} ms)")
    elif avg_ping < recorded_min:
        print(f"Server: {server_name}, Avg Ping: {avg_ping} ms, lower than minimum recorded ping ({recorded_min} ms)")
    else:
        print(f"Server: {server_name}, Avg Ping: {avg_ping} ms, equal to minimum recorded ping ({recorded_min} ms)")


def load_configuration_files():
    # Load the config.json to get VPN keywords
    with open('config.json', 'r') as f:
        config = json.load(f)

    vpn_keywords = config.get('vpn_keywords', ['vpn'])  # Default to ['vpn'] if not found

    # Load the IPs and server names from game_servers.json
    with open('game_servers.json', 'r') as f:
        servers = json.load(f)

    return vpn_keywords, servers


if __name__ == "__main__":
    try:
        # Load Config and Servers
        vpn_keywords, servers = load_configuration_files()

        # Get the default active network interface or VPN
        network_interface = get_default_network_interface()
        print(f"Using network interface: {network_interface}")

        results = ping_all_servers(servers)
        sorted_results = sort_servers(results)

        # Load existing log data (create if necessary)
        log_file = f'log_data_{network_interface}.json'
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump({}, f)  # Create an empty JSON object

        with open(log_file, 'r') as f:
            log_data = json.load(f)

        # Print and compare results
        for server_name, avg_ping in sorted_results:
            print_comparison(log_data, server_name, avg_ping)

        # Save results to log_data_<network_interface>.json
        save_results_to_log(sorted_results, network_interface)

    except KeyboardInterrupt:
        print("\nGracefully exiting...")
