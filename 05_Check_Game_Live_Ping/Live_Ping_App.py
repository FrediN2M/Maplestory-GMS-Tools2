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


class PingApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Server Ping Monitor")

        self.servers = {}
        self.load_servers()

        self.running = False
        self.lowest_pings = {ip: None for ip in self.servers.keys()}
        self.average_pings = {ip: [] for ip in self.servers.keys()}  # Dictionary to hold lists of pings for each server
        self.ping_queue = Queue()
        self.elapsed_time = 0.0  # Store as float for precision
        self.ping_thread = None

        # Setup UI
        self.create_widgets()

        # VPN detection keywords
        self.vpn_keywords = self.load_vpn_keywords()

        # Update network interface
        self.current_interface = None  # To track the current interface
        self.update_network_interface()

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

        self.tree = ttk.Treeview(self.tree_frame, columns=("Server", "Ping", "Lowest Ping", "Average Ping"), show='headings')
        self.tree.heading("Server", text="Server")
        self.tree.heading("Ping", text="Ping")
        self.tree.heading("Lowest Ping", text="Lowest Ping")
        self.tree.heading("Average Ping", text="Average Ping")

        self.tree_scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=self.tree_scroll.set)

        self.tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Insert initial server data into the table
        for ip, name in self.servers.items():
            self.tree.insert("", "end", values=(name, "", ""))

    def load_servers(self):
        with open("game_servers.json") as f:
            self.servers = json.load(f)

    def load_vpn_keywords(self):
        with open("config.json") as f:
            config = json.load(f)
            return config.get("vpn_keywords", [])

    def update_network_interface(self):
        # Get the new interface
        interface = self.get_default_network_interface()

        # Check if the interface has changed
        if interface != self.current_interface:
            self.current_interface = interface
            self.lowest_pings = {ip: None for ip in self.servers.keys()}  # Reset only on change

            # Update the TreeView to clear the "Lowest Ping" column
            for item in self.tree.get_children():
                values = self.tree.item(item, 'values')
                self.tree.item(item, values=(values[0], values[1], ""))  # Clear the lowest ping column

        # Display the updated interface
        self.network_interface_label.config(text=f"Current Network Interface: {interface}")

    def get_default_network_interface(self):
        try:
            # Get the list of network interfaces
            interfaces = psutil.net_if_addrs()
            active_vpn = None

            # Check for active interfaces
            for interface in interfaces:
                if any(keyword.lower() in interface.lower() for keyword in self.vpn_keywords):
                    stats = psutil.net_if_stats()[interface]
                    if stats.isup:
                        active_vpn = interface  # Found an active VPN interface

            if active_vpn:
                return f"VPN Detected: {active_vpn}"

            # If no active VPN found, return the first active interface
            for interface in interfaces:
                stats = psutil.net_if_stats()[interface]
                if stats.isup:  # Check if the interface is up
                    return interface  # Return the first active non-VPN interface

            return "No active interface found"

        except Exception as e:
            return "Error fetching interface: " + str(e)

    def start_pinging(self):
        if not self.running:
            self.running = True
            # Recheck and update the network interface before starting the ping
            self.update_network_interface()
            self.elapsed_time = 0.0  # Reset elapsed time
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.ping_queue.queue.clear()  # Clear any previous ping results
            self.update_timer()  # Start updating the timer

            # Start the ping thread
            self.ping_thread = threading.Thread(target=self.run_ping_thread)
            self.ping_thread.start()

    def stop_pinging(self):
        self.running = False  # Set flag to stop the loop
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

    def update_timer(self):
        if self.running:
            self.elapsed_time += 0.1  # Increment by 100 ms
            milliseconds = int((self.elapsed_time % 1) * 10)  # Get first digit of milliseconds
            total_seconds = int(self.elapsed_time)
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Format time as HH:MM:SS.MS
            formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds}"
            self.timer_label.config(text=f"Elapsed Time: {formatted_time}")

            # Call update_timer again after 100 ms for smoother update
            self.master.after(100, self.update_timer)  # Update every 100 ms

    def run_ping_thread(self):
        while self.running:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(self.ping_server, ip, name): ip for ip, name in self.servers.items()}
                for future in concurrent.futures.as_completed(futures):
                    ip = futures[future]
                    try:
                        ping_time = future.result()
                        self.ping_queue.put((ip, ping_time))
                    except Exception as e:
                        print(f"Error pinging {ip}: {e}")

            # Wait for 1 second before the next round of pings
            time.sleep(1)

            # Process the queue after all pings are done
            self.master.after(0, self.process_queue)

    def process_queue(self):
        while not self.ping_queue.empty():
            ip, ping_time = self.ping_queue.get()
            # Update lowest ping if applicable
            if self.lowest_pings[ip] is None or ping_time < self.lowest_pings[ip]:
                self.lowest_pings[ip] = ping_time

            # Add the ping to the list for average calculation
            self.average_pings[ip].append(ping_time)
            self.update_tree(ip, ping_time)

    def ping_server(self, ip, name):
        port = self.get_port(name)
        start_time = time.time()
        try:
            with socket.create_connection((ip, port), timeout=2):
                ping_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        except (socket.timeout, socket.error):
            ping_time = float('inf')  # No response, simulate very high ping
        return int(ping_time)  # Return as integer (no decimal places)

    def get_port(self, name):
        if "Login" in name:
            return 8484
        elif "AH" in name or "CS" in name:
            return 8786
        else:
            return 8585

    def update_tree(self, ip, ping):
        # Calculate average ping for the server
        average_ping = int(sum(self.average_pings[ip]) / len(self.average_pings[ip])) if self.average_pings[ip] else 0

        for item in self.tree.get_children():
            values = self.tree.item(item, 'values')
            if values[0] == self.servers[ip]:
                lowest_ping = f"{self.lowest_pings[ip]} ms" if self.lowest_pings[ip] is not None and self.lowest_pings[ip] != float('inf') else ""
                average_ping_text = f"{average_ping} ms" if average_ping != float('inf') else "Timeout"
                self.tree.item(item, values=(values[0], f"{ping} ms" if ping != float('inf') else "Timeout", lowest_ping, average_ping_text))
                break

    def export_log(self):
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text Files", "*.txt")], initialfile="ping_log.txt")
        if filename:
            with open(filename, 'w') as f:
                f.write(f"Log Timestamp: {datetime.now()}\n")
                f.write(f"Network Interface: {self.network_interface_label.cget('text')}\n")
                f.write(f"Elapsed Time: {self.timer_label.cget('text')}\n")
                for ip, name in self.servers.items():
                    ping = self.tree.item(self.tree.get_children()[0], 'values')[1]
                    lowest_ping = self.lowest_pings[ip]
                    f.write(f"{name} - Current Ping: {ping} - Lowest Ping: {lowest_ping} ms\n")
            messagebox.showinfo("Export", "Log exported successfully.")

    def show_information(self):
        information_window = tk.Toplevel(self.master)
        information_window.title("Information")
        information_window.transient(self.master)
        information_window.grab_set()
        information_text = """Information:
        Click 'Start' to begin pinging the servers.
        Click 'Stop' to halt the pinging process.
        Optional - Click 'Export to Log' to save the current table to a log file.
        """
        label = tk.Label(information_window, text=information_text, padx=10, pady=10)
        label.pack()
        tk.Button(information_window, text="Close", command=information_window.destroy).pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = PingApp(root)
    root.mainloop()
