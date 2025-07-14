#!/usr/bin/env python3

import os
import sys
import subprocess
import requests
import zipfile
import io
import argparse
import shutil

# List of required dependencies
REQUIRED_DEPS = ["git", "make", "gcc", "go", "unzip"]

def print_step(message):
    print(f"\n[+] {message}")

def run_cmd(command, check=True):
    """Run a shell command and optionally check for errors."""
    print(f"    ↳ Executing: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.stdout:
        print(f"        Output: {result.stdout.strip()}")
    if result.stderr:
        print(f"        Errors: {result.stderr.strip()}")
    if check and result.returncode != 0:
        print("[!] Command failed. Exiting.")
        sys.exit(1)
    return result

def check_dependencies():
    """Check for required dependencies and offer to install missing ones."""
    print_step("Checking for required dependencies...")
    missing = [dep for dep in REQUIRED_DEPS if shutil.which(dep) is None]

    if missing:
        print(f"[!] Missing dependencies: {', '.join(missing)}")
        choice = input("Do you want to install the missing dependencies? (Y/N): ").strip().lower()
        if choice == 'y':
            print_step("Installing missing dependencies...")
            run_cmd(f"sudo apt update && sudo apt install -y {' '.join(missing)}")
            print_step("Dependencies installed successfully.")
        else:
            print("[!] Cannot proceed without required dependencies. Exiting.")
            sys.exit(1)
    else:
        print("[✓] All dependencies are already installed.")

def download_latest_zip():
    """Download and extract the latest Evilginx2 release from GitHub."""
    print_step("Fetching latest Evilginx2 release info from GitHub...")
    api_url = "https://api.github.com/repos/kgretzky/evilginx2/releases/latest"
    response = requests.get(api_url)
    if response.status_code != 200:
        print("[!] Failed to fetch release info. Exiting.")
        sys.exit(1)

    data = response.json()
    asset = next((a for a in data.get("assets", []) if a["name"].endswith(".zip")), None)
    if not asset:
        print("[!] No ZIP file found in the latest release.")
        sys.exit(1)

    zip_url = asset["browser_download_url"]
    print(f"[+] Downloading ZIP from: {zip_url}")
    zip_data = requests.get(zip_url).content

    print_step("Extracting ZIP contents...")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        zf.extractall()
    print("[✓] Extraction complete.")

def try_run_evilginx():
    """Attempt to execute the evilginx binary from known locations."""
    print_step("Searching for 'evilginx' binary...")

    if os.path.isfile("./evilginx"):
        print("[+] Found './evilginx'")
        run_cmd("chmod +x ./evilginx")
        return subprocess.Popen(["sudo", "./evilginx"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    elif os.path.isdir("evilginx") and os.path.isfile("evilginx/evilginx"):
        print("[+] Found 'evilginx/evilginx', changing into directory...")
        os.chdir("evilginx")
        run_cmd("chmod +x ./evilginx")
        return subprocess.Popen(["sudo", "./evilginx"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    else:
        print("[!] Could not find the evilginx binary. Exiting.")
        sys.exit(1)

def configure_evilginx(proc, domain, ip):
    """Send configuration commands to evilginx via stdin."""
    print_step("Configuring Evilginx with provided domain and IP...")
    commands = [
        f"config domain {domain}",
        f"config ipv4 {ip}",
        "exit"
    ]

    for cmd in commands:
        print(f"    ↳ Sending: {cmd}")
        proc.stdin.write(cmd + "\n")
        proc.stdin.flush()

    stdout, stderr = proc.communicate()

    if stdout:
        print_step("Evilginx Output:")
        print(stdout.strip())
    if stderr:
        print_step("Evilginx Errors:")
        print(stderr.strip())

    print_step("Evilginx configuration complete.")

def main():
    parser = argparse.ArgumentParser(description="AutoGinx - Evilginx Setup Script")
    parser.add_argument("--domain", required=True, help="Domain name for Evilginx")
    parser.add_argument("--pubIP", required=True, help="Public IP address for Evilginx")
    args = parser.parse_args()

    print("\n=== AutoGinx Script Starting ===")

    # Step 1: Create evilginx directory
    if not os.path.exists("evilginx"):
        print_step("Creating 'evilginx' directory...")
        os.mkdir("evilginx")
    else:
        print_step("'evilginx' directory already exists.")
    os.chdir("evilginx")

    # Step 2: Download and unzip
    download_latest_zip()

    # Step 3: Check and install dependencies
    check_dependencies()

    # Step 4: Prompt to run evilginx
    run_choice = input("\nDo you want to run evilginx now? (Y/N): ").strip().lower()
    if run_choice != 'y':
        print_step("Reminder:")
        print("    - Make sure to check your DNS records.")
        print("    - Make sure your firewall is properly configured to accept traffic.")
        print("\nExiting without running evilginx.")
        sys.exit(0)

    # Step 5: Run evilginx and configure it
    proc = try_run_evilginx()
    configure_evilginx(proc, args.domain, args.pubIP)

    # Final notes
    print_step("Reminder:")
    print("    - Make sure to check your DNS records.")
    print("    - Make sure your firewall is properly configured to accept traffic.")
    print_step("AutoGinx Evilginx setup is complete.")

if __name__ == "__main__":
    main()
