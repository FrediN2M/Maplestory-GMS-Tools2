import tkinter as tk
import concurrent.futures
import json
import socket
import threading
import time
import psutil
from datetime import datetime
from queue import Queue
from tkinter import ttk, messagebox, filedialog
from loguru import logger


class PingApp:
    def __init__(self, master):
        logger.info("PingApp Started")
        self.master = master
        self.master.title("Server Ping Monitor")

        # Bind close event to a cleanup method
        self.master.protocol("WM_DELETE_WINDOW", self.on_close)

        self.servers = {}
        self.load_servers()

        self.running = False
        self.lowest_pings = {ip: None for ip in self.servers.keys()}
        self.average_pings = {ip: [] for ip in self.servers.keys()}
        self.total_pings = {ip: 0 for ip in self.servers.keys()}
        self.failed_pings = {ip: 0 for ip in self.servers.keys()}
        self.spiked_pings = {ip: 0 for ip in self.servers.keys()}
        self.succeeded_pings = {ip: 0 for ip in self.servers.keys()}
        self.ping_queue = Queue()
        self.elapsed_time = 0.0
        self.ping_thread = None
        self.last_five_pings = {ip: [] for ip in self.servers.keys()}  # Track last five pings
        self.spike_threshold_percentage = 0.15  # 15% for spike detection
        # Initialize last spike time tracker for each IP
        self.last_spike_time = {}
        # Initialize previous spikes tracker for each IP
        self.previous_spikes = {}
        # Initialize spike detection state
        self.spike_detected = {}  # This will hold the spike detection status for each server
        self.spike_display_time = {}

        # Setup UI
        self.create_widgets()

        # VPN detection keywords
        self.vpn_keywords = self.load_vpn_keywords()

        # Update network interface
        self.current_interface = None
        self.update_network_interface()

    def on_close(self):
        """Gracefully shut down by calling stop_pinging and waiting for thread to finish."""
        self.stop_pinging()
        self.check_thread_closed()  # Use a separate method to check if the thread has finished
        logger.info("PingApp Closed")

    def create_widgets(self):
        # Buttons
        button_frame = tk.Frame(self.master)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(button_frame, text="Start", command=self.start_pinging)
        self.start_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = tk.Button(button_frame, text="Stop", command=self.stop_pinging, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

        tk.Button(button_frame, text="Export to Log", command=self.export_log).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Information", command=self.show_information).pack(side=tk.LEFT, padx=5)

        # Network interface display
        self.network_interface_label = tk.Label(self.master, text="Current Network Interface: ")
        self.network_interface_label.pack(pady=5)

        # Timer display
        self.timer_label = tk.Label(self.master, text="Elapsed Time: 00:00:00.0")
        self.timer_label.pack(pady=5)

        # Table setup with Scrollbar
        self.tree_frame = tk.Frame(self.master)
        self.tree_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Define table columns
        self.tree = ttk.Treeview(
            self.tree_frame, columns=("Server", "Ping", "Lowest Ping", "Average Ping", "Total Pings", "Succeeded Pings", "Failed Pings", "Spiked Pings", "Spike Ping"), show='headings'
        )
        self.tree.heading("Server", text="Server")
        self.tree.heading("Ping", text="Ping")
        self.tree.heading("Lowest Ping", text="Lowest Ping")
        self.tree.heading("Average Ping", text="Average Ping")
        self.tree.heading("Total Pings", text="Total Pings")
        self.tree.heading("Succeeded Pings", text="Succeeded Pings")
        self.tree.heading("Failed Pings", text="Failed Pings")
        self.tree.heading("Spiked Pings", text="Spiked Pings")
        self.tree.heading("Spike Ping", text="Spike Ping")  # New Spike Ping column

        # Set column widths
        self.tree.column("Server", width=100)
        self.tree.column("Ping", width=80)
        self.tree.column("Lowest Ping", width=80)
        self.tree.column("Average Ping", width=80)
        self.tree.column("Total Pings", width=80)
        self.tree.column("Succeeded Pings", width=110)
        self.tree.column("Failed Pings", width=80)
        self.tree.column("Spiked Pings", width=80)
        self.tree.column("Spike Ping", width=550)

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.tree_scroll.set)

        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Insert initial server data into the table
        for ip, name in self.servers.items():
            self.tree.insert("", "end", values=(name, "", "", "", "", "", "", ""))

    def load_servers(self):
        with open("game_servers.json") as f:
            self.servers = json.load(f)

    def load_vpn_keywords(self):
        with open("config.json") as f:
            config = json.load(f)
            return config.get("vpn_keywords", [])

    def update_network_interface(self):
        interface = self.get_default_network_interface()
        if interface != self.current_interface:
            self.current_interface = interface
            self.lowest_pings = {ip: None for ip in self.servers.keys()}
            self.total_pings = {ip: 0 for ip in self.servers.keys()}
            self.failed_pings = {ip: 0 for ip in self.servers.keys()}
            self.succeeded_pings = {ip: 0 for ip in self.servers.keys()}
            self.spiked_pings = {ip: 0 for ip in self.servers.keys()}
            self.last_five_pings = {ip: [] for ip in self.servers.keys()}  # Reset last five pings
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                self.tree.item(item, values=(values[0], values[1], "", "", "", "", "", ""))

        self.network_interface_label.config(text=f"Current Network Interface: {interface}")

    def get_default_network_interface(self):
        try:
            interfaces = psutil.net_if_addrs()
            active_vpn = None
            for interface in interfaces:
                if any(keyword.lower() in interface.lower() for keyword in self.vpn_keywords):
                    stats = psutil.net_if_stats()[interface]
                    if stats.isup:
                        active_vpn = interface
            if active_vpn:
                logger.info(f"VPN Detected: {active_vpn}")
                return f"VPN Detected: {active_vpn}"
            for interface in interfaces:
                stats = psutil.net_if_stats()[interface]
                if stats.isup:
                    if interface != self.current_interface:
                        logger.info(f"No VPN detected, using {interface}")
                    return interface
            logger.warning("No Active Interface found")
            return "No active interface found"
        except Exception as e:
            logger.error("Error fetching interface: " + str(e))
            return "Error fetching interface: " + str(e)

    def start_pinging(self):
        if not self.running:
            logger.info("Starting to ping servers...")
            self.running = True
            self.update_network_interface()
            self.elapsed_time = 0.0
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.ping_queue.queue.clear()
            self.update_timer()
            self.ping_thread = threading.Thread(target=self.run_ping_thread)
            self.ping_thread.start()

    def stop_pinging(self):
        """Set running to False to allow the pinging thread to exit gracefully."""
        logger.info("Stopping ping process...")
        self.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def check_thread_closed(self):
        """Check if the pinging thread has closed, then destroy the window."""
        if self.ping_thread is not None and self.ping_thread.is_alive():
            # Keep checking every 100 milliseconds until the thread stops
            logger.warning("Ping process still running, attempting to close it.")
            self.master.after(100, self.check_thread_closed)
        else:
            # Once the thread is confirmed closed, destroy the window
            self.master.destroy()

    def update_timer(self):
        if self.running:
            self.elapsed_time += 0.1
            milliseconds = int((self.elapsed_time % 1) * 10)
            total_seconds = int(self.elapsed_time)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds}"
            self.timer_label.config(text=f"Elapsed Time: {formatted_time}")
            self.master.after(100, self.update_timer)

    def run_ping_thread(self):
        while self.running:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(self.ping_server, ip, name): ip for ip, name in self.servers.items()}
                for future in concurrent.futures.as_completed(futures):
                    ip = futures[future]
                    try:
                        ping_time = future.result()  # This could raise an exception
                        # Only add to queue if ping_time is valid (not None)
                        if ping_time is not None:
                            self.ping_queue.put((ip, ping_time))
                        else:
                            # logger.warning(f"Ping time for {self.servers[ip]} was None.")
                            self.failed_pings[ip] += 1
                    except Exception as e:
                        logger.error(f"Error pinging {self.servers[ip]}: {e}")
            time.sleep(1)
            self.master.after(0, self.process_queue)

    def process_queue(self):
        while not self.ping_queue.empty():
            ip, ping_time = self.ping_queue.get()
            self.total_pings[ip] += 1
            if ping_time == float('inf'):
                self.failed_pings[ip] += 1
            else:
                self.succeeded_pings[ip] += 1
                if self.lowest_pings[ip] is None or ping_time < self.lowest_pings[ip]:
                    self.lowest_pings[ip] = ping_time
                self.average_pings[ip].append(ping_time)
                self.last_five_pings[ip].append(ping_time)  # Track last five pings
                if len(self.last_five_pings[ip]) > 5:
                    self.last_five_pings[ip].pop(0)  # Keep only the last five pings
            self.update_tree(ip, ping_time)

    def ping_server(self, ip, name):
        port = self.get_port(name)
        start_time = time.time()
        try:
            with socket.create_connection((ip, port), timeout=2):
                ping_time = (time.time() - start_time) * 1000
                return int(ping_time)  # The time taken for the ping in milliseconds
        except Exception as e:
            logger.error(f"Failed to ping server: {self.servers[ip]}. Error: {e}")
            return None  # Return None or a specific error code to signify failure

    def get_port(self, name):
        if "Login" in name:
            return 8484
        elif "AH" in name or "CS" in name:
            return 8786
        else:
            return 8585

    def update_tree(self, ip, ping_time):
        current_time = time.time()
        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values[0] == self.servers[ip]:
                average_ping = sum(self.average_pings[ip]) // len(self.average_pings[ip]) if self.average_pings[ip] else 0
                # Determine spike message
                spike_ping = self.detect_ping_spike(ip, current_time)
                if spike_ping == "No Spike":
                    spike_ping = ""  # Reset spike message if no spike is detected
                self.tree.item(item, values=(
                    values[0], f"{ping_time}ms", self.lowest_pings[ip] if self.lowest_pings[ip] is not None else "",
                    average_ping, self.total_pings[ip], self.succeeded_pings[ip],
                    self.failed_pings[ip], self.spiked_pings[ip], spike_ping
                ))

    def detect_ping_spike(self, ip, current_time):
        # Initialize last spike time and spike detected flag if not set for this IP
        if ip not in self.last_spike_time:
            self.last_spike_time[ip] = 0
        if ip not in self.spike_detected:
            self.spike_detected[ip] = False
            self.spike_display_time[ip] = 0  # Track when the last spike message should be cleared

        # Check if there are enough pings to calculate spikes
        if len(self.last_five_pings[ip]) < 5:
            return "Insufficient Data"

        # Calculate average and lowest recent pings
        recent_pings = self.last_five_pings[ip]
        average_recent = sum(recent_pings) / len(recent_pings)
        lowest_recent = min(recent_pings)

        # Detect spikes
        spikes = [
            ping for ping in recent_pings
            if ping > average_recent * (1 + self.spike_threshold_percentage)
        ]

        # Update only if there’s a spike and 10 seconds have passed or if a new spike is higher than the previous
        if spikes:
            highest_spike = max(spikes)
            if (current_time - self.last_spike_time[ip] >= 10) or highest_spike > self.get_previous_spike(ip):
                self.last_spike_time[ip] = current_time
                self.store_previous_spike(ip, highest_spike)
                self.spike_detected[ip] = True  # Set spike detected flag
                self.spike_display_time[ip] = current_time + 10  # Set time to clear spike message
                spike_details = f"{self.servers[ip]} - Spike Detected - {highest_spike}ms, passed threshold by 15% over Lowest Ping({lowest_recent}ms) and Average Ping({average_recent:.2f}ms) - 10s"
                self.spiked_pings[ip] += 1
                logger.warning(spike_details[:-6])
                return spike_details

        # If a spike has been detected previously, keep the message until 10 seconds have passed
        if self.spike_detected[ip] and (current_time < self.spike_display_time[ip]):
            remaining_time = int(self.spike_display_time[ip] - current_time)
            return f"{self.servers[ip]} - Last Spike: {self.get_previous_spike(ip)}ms - {remaining_time}s"

        # Reset the detected flag if the spike display time has passed
        self.spike_detected[ip] = False
        return "No Spike"

    # Helper functions to get and store the previous spike
    def get_previous_spike(self, ip):
        return self.previous_spikes.get(ip, 0)

    def store_previous_spike(self, ip, spike):
        self.previous_spikes[ip] = spike

    def export_log(self):
        # Get the current date for filename suggestion
        current_date = datetime.now().strftime("%Y-%m-%d")
        suggested_filename = f"log_data_{current_date}.log"

        # Open the save file dialog and suggest the filename
        file_path = filedialog.asksaveasfilename(
            defaultextension=".log",
            filetypes=[("Log files", "*.log"), ("Text files", "*.txt")],
            initialfile=suggested_filename,
            title="Save Log File"
        )

        # Only proceed if the user selected a file path
        if file_path:
            # Format the log data as text for readability
            log_data = []
            for ip, name in self.servers.items():
                log_data.append(f"Server: {name}")
                log_data.append(f"  Lowest Ping: {self.lowest_pings[ip]} ms")
                average_ping = (
                    int(sum(self.average_pings[ip]) / len(self.average_pings[ip]))
                    if self.average_pings[ip] else None
                )
                log_data.append(f"  Average Ping: {average_ping} ms" if average_ping is not None else "  Average Ping: N/A")
                log_data.append(f"  Total Pings: {self.total_pings[ip]}")
                if self.succeeded_pings[ip] > 0:
                    log_data.append(f"  Succeeded Pings: {self.succeeded_pings[ip]}")
                if self.failed_pings[ip] > 0:
                    log_data.append(f"  Failed Pings: {self.failed_pings[ip]}")
                    log_data.append("   For more information, please check the app log file")
                if self.spiked_pings[ip] > 0:
                    log_data.append(f"  Spiked Pings: {self.spiked_pings[ip]}")
                    log_data.append("   For more information, please check the app log file")

                log_data.append("")  # Blank line for separation

            # Write the log data to the specified file
            with open(file_path, "w") as f:
                f.write("\n".join(log_data))

    def show_information(self):
        info_text = "This app monitors server ping times and tracks failed and successful pings, also displays ping spikes which are considered 15% over average."
        messagebox.showinfo("Information", info_text)


if __name__ == "__main__":
    logger.add("App_Log_{time}.log", rotation="30 days", backtrace=True, enqueue=False, catch=True)
    root = tk.Tk()
    app = PingApp(root)
    root.mainloop()
