"""
Author:Jui Hsin Wong
Assignment: #2
Description: Port Scanner — A tool that scans a target machine for open network ports
"""

# TODO: Import the required modules (Step ii)
# socket, threading, sqlite3, os, platform, datetime
import socket
import threading
import sqlite3
import os
import platform
import datetime


# TODO: Print Python version and OS name (Step iii)
print(f"Python version: {platform.python_version()}")
print(f"Operating System: {os.name}")


# TODO: Create the common_ports dictionary (Step iv)
# Dictionary mapping common port num to their service name
common_ports = {21:"FTP",22: "SSH",23: "Telnet",25: "SMTP",53: "DNS",80: "HTTP",110: "POP3",
                143: "IMAP",443: "HTTPS",3306: "MySQL",3389: "RDP",8080: "HTTP-Alt"}

# TODO: Create the NetworkTool parent class (Step v)
# - Constructor: takes target, stores as private self.__target
# - @property getter for target
# - @target.setter with empty string validation
# - Destructor: prints "NetworkTool instance destroyed"
class NetworkTool:
    def __init__(self,target):
        self.__target = target
    
# Q3: What is the benefit of using @property and @target.setter?
# TODO: Your 2-4 sentence answer here... (Part 2, Q3)
#The benefit of using @porperty lets you read an attribute like a normal variable, but secretly runs a method behind the scenes
#The benefit of using @target.setter, you can validate the value before saving it.

    @property
    def target(self):
        return self.__target
    
    @target.setter
    def target(self,value):
        if value == "":
            print("Error: Target cannot be empty")
        else:
            self.__target = value

    def __del__(self):
        print("NetworkTool instance destroyed")



# Q1: How does PortScanner reuse code from NetworkTool?
# TODO: Your 2-4 sentence answer here... (Part 2, Q1)
# PortScanner inherits from NetworkTool by defining it as class PortScanner(NetworkTool), This mean all methods and attributes from 
#NetworkTool are automatically available in PortScanner.

# TODO: Create the PortScanner child class that inherits from NetworkTool (Step vi)
# - Constructor: call super().__init__(target), initialize self.scan_results = [], self.lock = threading.Lock()
# - Destructor: print "PortScanner instance destroyed", call super().__del__()
class PortScanner (NetworkTool):
    def __init__(self,target):
        super().__init__(target)
        self.scan_results=[]
        self.lock = threading.Lock()
    
    def __del__(self):
        print("PortScanner instance destroyed")
        super().__del__()

# - scan_port(self, port):
#     - try-except with socket operations
#     - Create socket, set timeout, connect_ex
#     - Determine Open/Closed status
#     - Look up service name from common_ports (use "Unknown" if not found)
#     - Acquire lock, append (port, status, service_name) tuple, release lock
#     - Close socket in finally block
#     - Catch socket.error, print error message
    def scan_port(self, port):
#     Q4: What would happen without try-except here?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q4)
#     Without using try-except, if an error occurs Python will throw an unhandlled exception and crash the program.
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((self.target, port))
                if result == 0 :
                    status = "Open"
                else:
                    status = "Closed"
                service_name = common_ports.get(port, "Unknown")
                self.lock.acquire()
                self.scan_results.append((port, status, service_name))
                self.lock.release()
            except socket.error as e:
                print(f"Error scanning port {port}: {e}")
            finally:
                sock.close()

# - get_open_ports(self):
#     - Use list comprehension to return only "Open" results
    def get_open_ports(self):
        return[result for result in self.scan_results if result[1] == "Open"]

#     Q2: Why do we use threading instead of scanning one port at a time?
#     TODO: Your 2-4 sentence answer here... (Part 2, Q2)
#     Scanning one port at a time means the program must wait for each connection responce before moving on which is very slow.
#     With threading, multiple ports are scanned at the same time, so they don't block each other. 
#
# - scan_range(self, start_port, end_port):
#     - Create threads list
#     - Create Thread for each port targeting scan_port
#     - Start all threads (one loop)
#     - Join all threads (separate loop)
    def scan_range(self, start_port, end_port):
        threads = []
        for port in range(start_port, end_port+1):
            t = threading.Thread(target=self.scan_port, args=(port,))
            threads.append(t)

        for t in threads:
            t.start()
        for t in threads:
            t.join()

# TODO: Create save_results(target, results) function (Step vii)
# - Connect to scan_history.db
# - CREATE TABLE IF NOT EXISTS scans (id, target, port, status, service, scan_date)
# - INSERT each result with datetime.datetime.now()
# - Commit, close
# - Wrap in try-except for sqlite3.Error
def save_results(target, results):
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS scans(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   target TEXT,
                   port INTEGER,
                   status TEXT,
                   service TEXT,
                   scan_date TEXT
                   )""")
        for result in results:
            cursor.execute("INSERT INTO scans (target, port, status, service, scan_date) VALUES (?,?,?,?,?)",
                    (target, result[0], result[1], result[2], str(datetime.datetime.now())))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Error is {e}")


# TODO: Create load_past_scans() function (Step viii)
# - Connect to scan_history.db
# - SELECT all from scans
# - Print each row in readable format
# - Handle missing table/db: print "No past scans found."
# - Close connection
def load_past_scans():
    try:
        conn = sqlite3.connect("scan_history.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM scans")
        rows = cursor.fetchall()
        if not rows:
            print(f"No past scans found.")
        else:
            for row in rows:
                print(f"[{row[5]}] {row[1]} : Port {row[2]} ({row[4]}) - {row[3]}")
    except:
        print(f"No past scans found.")
    finally:
        conn.close()

# ============================================================
# MAIN PROGRAM
# ============================================================
if __name__ == "__main__":
    # TODO: Get user input with try-except (Step ix)
    # - Target IP (default "127.0.0.1" if empty)
    # - Start port (1-1024)
    # - End port (1-1024, >= start port)
    # - Catch ValueError: "Invalid input. Please enter a valid integer."
    # - Range check: "Port must be between 1 and 1024."
    target = input("Enter target IP: ") or "127.0.0.1"
    try:
        start_port = int(input("Enter start port number: Between 1-1024 : "))
        end_port = int(input("Enter end port number: Between 1-1024 and need to greater than start port : "))
        if start_port<1 or start_port >1024 or end_port<1 or end_port > 1024:
            print("Port must be between 1 and 1024.")
        elif end_port < start_port:
            print("End port must be >= start port.")
        else:
            scanner = PortScanner(target)
            print (f"Scanning {target} from port {start_port} to {end_port}...")
            scanner.scan_range(start_port,end_port)
            open_port = scanner.get_open_ports()
            print(f"--- Scan Results for {target} ---")
            for result in open_port:
                print (f"Port {result[0]}: {result[1]} ({result[2]})")
            print ("-------------------")
            print (f"Total open ports found {len(open_port)}")
            save_results(target, open_port)
            answer = input("Would you like to see past scan history? (yes/no)")
            if answer == "yes" or answer == "YES":
                load_past_scans()
            else:
                pass
    except ValueError:
        print("Invalid input. Please enter a valid integer.")
    
    # TODO: After valid input (Step x)
    # - Create PortScanner object
    # - Print "Scanning {target} from port {start} to {end}..."
    # - Call scan_range()
    # - Call get_open_ports() and print results
    # - Print total open ports found
    # - Call save_results()
    # - Ask "Would you like to see past scan history? (yes/no): "
    # - If "yes", call load_past_scans()
    
# Q5: New Feature Proposal
# TODO: Your 2-3 sentence description here... (Part 2, Q5)
# Diagram: See diagram_studentID.png in the repository root
