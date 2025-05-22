# Created By Sir_Cornealious 

import requests
import time
import os
import sys
import itertools
import subprocess
import urllib.parse
import ipaddress
import re

def validate_url_or_ip(input_str):
    # Validate URL
    try:
        result = urllib.parse.urlparse(input_str)
        if result.scheme in ('http', 'https') and result.netloc:
            return input_str
    except ValueError:
        pass
    
    # Validate IP (IPv4/IPv6)
    try:
        ipaddress.ip_address(input_str)
        return f"http://{input_str}/"
    except ValueError:
        pass
    
    print("[ERROR] Invalid URL or IP. Please enter a valid URL (e.g., https://example.com) or IP (e.g., 192.168.1.1)")
    return None

def validate_email(email):
    # Basic email validation
    if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return email
    print("[ERROR] Invalid email format. Please enter a valid email (e.g., yourname@icloud.com)")
    return None

def get_user_input():
    # Prompt for URL/IP
    while True:
        url = input("Enter the URL or IP to check (e.g., https://example.com or 192.168.1.1): ").strip()
        validated_url = validate_url_or_ip(url)
        if validated_url:
            break
    
    # Prompt for email
    while True:
        email = input("Enter your Apple ID email for notifications (e.g., yourname@icloud.com): ").strip()
        validated_email = validate_email(email)
        if validated_email:
            break
    
    # Prompt for proxy
    proxy = input("Enter a SOCKS5 proxy (address:port, e.g., us1234.nordvpn.com:1080) or press Enter to skip: ").strip()
    proxies = None
    if proxy:
        username = input("Enter proxy username (or press Enter to skip): ").strip()
        password = input("Enter proxy password (or press Enter to skip): ").strip()
        proxy_url = f"socks5://{proxy}"
        if username and password:
            proxy_url = f"socks5://{username}:{password}@{proxy}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url
        }
        print(f"[INFO] Configured proxy: {proxy_url}")
    else:
        print("[INFO] No proxy configured")
    
    # Prompt for interval
    interval = input("Enter check interval in seconds (default 60): ").strip()
    try:
        check_interval = int(interval) if interval else 60
        if check_interval <= 0:
            raise ValueError
    except ValueError:
        print("[INFO] Invalid interval, using default: 60 seconds")
        check_interval = 60
    
    # Prompt for stop option
    stop = input("Stop after first success? (y/n, default n): ").strip().lower()
    stop_after_success = stop == 'y'
    print(f"[INFO] Stop after first success: {'Yes' if stop_after_success else 'No'}")
    
    # Display iCloud reminder
    print("""
Reminder: To receive notifications, enable Messages in iCloud on each device (Mac, iPhone, iPad) using the same Apple ID email.
On Mac: System Settings > Apple ID > iCloud > Messages > Enable.
On iPhone/iPad: Settings > [Your Name] > iCloud > Messages > Enable.
""")
    
    return validated_url, validated_email, proxies, check_interval, stop_after_success

def check_website(url, proxies=None):
    print(f"[INFO] Sending request to {url}")
    if proxies:
        print(f"[INFO] Using proxy: {proxies.get('https')}")
    else:
        print("[INFO] No proxy configured")
    
    start_time = time.time()
    try:
        response = requests.get(url, timeout=5, proxies=proxies)
        end_time = time.time()
        latency = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"[INFO] Received response: Status {response.status_code}, Latency {latency:.2f}ms")
        
        if response.status_code == 200:
            return True, "Website is UP"
        else:
            return False, f"Website returned status code: {response.status_code}"
    except requests.ConnectionError:
        print("[ERROR] Connection failed")
        return False, "Website is DOWN (connection failed)"
    except requests.Timeout:
        print("[ERROR] Request timed out")
        return False, "Website timed out"
    except requests.RequestException as e:
        print(f"[ERROR] Request error: {e}")
        return False, f"Error checking website: {e}"

def play_alarm():
    print("[INFO] Playing alarm sound")
    os.system("afplay /System/Library/Sounds/Glass.aiff")
    # For custom sound, update path, e.g.:
    # os.system("afplay /path/to/your/alarm.mp3")

def send_notification(recipient_email, message):
    print(f"[INFO] Preparing notification: '{message}' to {recipient_email}")
    try:
        # AppleScript to send a message via Messages app
        applescript = f'''
        tell application "Messages"
            activate
            set targetService to first service whose service type is iMessage
            set targetBuddy to buddy "{recipient_email}" of targetService
            send "{message}" to targetBuddy
        end tell
        '''
        print("[INFO] Executing AppleScript for Messages")
        # Run AppleScript via subprocess
        process = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True)
        if process.returncode == 0:
            print("[INFO] AppleScript executed successfully")
            return True, "Notification sent"
        else:
            print(f"[ERROR] AppleScript failed: {process.stderr}")
            return False, f"Failed to send notification: {process.stderr}"
    except Exception as e:
        print(f"[ERROR] Notification error: {e}")
        return False, f"Failed to send notification: {e}"

def show_status_indicator():
    # Spinning cursor: | / - \
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    sys.stdout.write('\rChecking website... ' + next(spinner))
    sys.stdout.flush()

def clear_line():
    # Clear the current line in the terminal
    sys.stdout.write('\r\033[K')
    sys.stdout.flush()

def monitor_website(url, recipient_email, proxies=None, check_interval=60, stop_after_success=False):
    while True:
        # Show status indicator while checking
        show_status_indicator()
        
        # Check website with proxies
        is_up, message = check_website(url, proxies=proxies)
        
        # Clear the status indicator
        clear_line()
        
        # Print the result (overwrites the line)
        result = f"{time.ctime()}: {message}"
        print(result, end='', flush=True)
        
        if is_up:
            print(" - Playing alarm...", end='', flush=True)
            play_alarm()
            notification_body = f"Website is UP: {url}"
            success, notification_message = send_notification(recipient_email, notification_body)
            print(f" {notification_message}")
            if stop_after_success:
                print("[INFO] Stopping after first success")
                break
        else:
            print(" - Continuing to monitor...")
        
        # Wait for the next check, updating spinner periodically
        for _ in range(check_interval):
            show_status_indicator()
            time.sleep(1)
        clear_line()

if __name__ == "__main__":
    # Get user inputs
    url, recipient_email, proxies, check_interval, stop_after_success = get_user_input()
    # Check every specified interval
    monitor_website(url, recipient_email, proxies=proxies, check_interval=check_interval, stop_after_success=stop_after_success)