import os
import subprocess
import requests
import argparse
import sys
import shutil

# Define colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Define branding
BRANDING = f"{CYAN}{BOLD}[BDupdater]{RESET} "

VERSION_FILE = "/var/tmp/discord_version"
BETTERDISCORD_URL = "https://github.com/BetterDiscord/Installer/releases/latest/download/BetterDiscord-Linux.AppImage"
COMMON_DISCORD_PATHS = [
    "/usr/lib/discord",
    "/opt/discord",
    "/usr/share/discord",
    os.path.expanduser("~/.local/share/Discord"),
    os.path.expanduser("~/snap/discord/current/Discord")
]

def print_info(message):
    print(f"{BRANDING}{BLUE}{message}{RESET}")

def print_success(message):
    print(f"{BRANDING}{GREEN}{message}{RESET}")

def print_warning(message):
    print(f"{BRANDING}{YELLOW}{message}{RESET}")

def print_error(message):
    print(f"{BRANDING}{RED}{message}{RESET}")

def is_installed(command):
    """ Check if a command is available in the system PATH """
    result = subprocess.run(['which', command], capture_output=True, text=True)
    return result.returncode == 0

def install_dependencies():
    """ Ask user if they want to install missing dependencies """
    print_warning("Some required tools are missing. We need to install them.")
    
    # Ask for user input
    answer = input("Do you want to install missing dependencies? (yes/no): ").strip().lower()
    if answer not in ['yes', 'y']:
        print_warning("Exiting. Please install the required tools manually.")
        sys.exit(1)
    
    # Install dependencies based on the system
    try:
        # Attempt to install using apt (Debian/Ubuntu-based systems)
        print_info("Updating package list...")
        subprocess.run(['sudo', 'apt-get', 'update'], check=True)
        print_info("Installing required packages...")
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'git', 'npm'], check=True)
        
        # Install pnpm via npm
        subprocess.run(['sudo', 'npm', 'install', '-g', 'pnpm'], check=True)
        
        print_success("Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print_error("Failed to install dependencies.")
        print_error("Output:", e.stdout)
        print_error("Errors:", e.stderr)
        sys.exit(1)

def find_discord_path():
    # Look for the discord executable in common paths
    for path in COMMON_DISCORD_PATHS:
        discord_executable = os.path.join(path, 'discord')
        if os.path.exists(discord_executable):
            return path
    
    # Search for `discord` executable in system PATH
    for path in os.getenv('PATH', '').split(os.pathsep):
        discord_executable = os.path.join(path, 'discord')
        if os.path.exists(discord_executable):
            return os.path.dirname(discord_executable)
    
    return None

def get_current_discord_version(discord_path):
    version_file = os.path.join(discord_path, 'version')
    if os.path.exists(version_file):
        with open(version_file, 'r') as file:
            return file.read().strip()
    return None
    
def get_previous_discord_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as file:
            return file.read().strip()
        
    return None

def update_previous_discord_version(version):
    if version is None:
        version = "unknown"
    try:
        with open(VERSION_FILE, 'w') as file:
            file.write(version)
    except IOError as e:
        print_error(f"Error writing version file: {e}")
        sys.exit(1)

def update_betterdiscord(inject_type):
    print_info("Updating BetterDiscord...")
    
    bd_dir = "/tmp/BetterDiscord"
    
    # Remove the existing directory if it exists
    if os.path.exists(bd_dir):
        print_info(f"Removing existing directory: {bd_dir}")
        shutil.rmtree(bd_dir)
    
    print_info("Cloning BetterDiscord repository...")
    clone_result = subprocess.run(['git', 'clone', 'https://github.com/BetterDiscord/BetterDiscord.git', bd_dir], capture_output=True, text=True)
    if clone_result.returncode != 0:
        print_error("Error cloning BetterDiscord repository.")
        print_error("Output:", clone_result.stdout)
        print_error("Errors:", clone_result.stderr)
        return
    
    os.chdir(bd_dir)
    
    print_info("Installing dependencies...")
    npm_install_result = subprocess.run(['npm', 'install', '-g', 'pnpm'], capture_output=True, text=True)
    if npm_install_result.returncode != 0:
        print_error("Error installing pnpm.")
        print_error("Output:", npm_install_result.stdout)
        print_error("Errors:", npm_install_result.stderr)
        return
    
    pnpm_install_result = subprocess.run(['pnpm', 'install'], capture_output=True, text=True)
    if pnpm_install_result.returncode != 0:
        print_error("Error installing dependencies with pnpm.")
        print_error("Output:", pnpm_install_result.stdout)
        print_error("Errors:", pnpm_install_result.stderr)
        return
    
    print_info("Building BetterDiscord...")
    pnpm_build_result = subprocess.run(['pnpm', 'build'], capture_output=True, text=True)
    if pnpm_build_result.returncode != 0:
        print_error("Error building BetterDiscord.")
        print_error("Output:", pnpm_build_result.stdout)
        print_error("Errors:", pnpm_build_result.stderr)
        return
    
    print_info(f"Injecting BetterDiscord for {inject_type}...")
    pnpm_inject_result = subprocess.run(['pnpm', 'inject', inject_type], capture_output=True, text=True)
    if pnpm_inject_result.returncode != 0:
        print_error("Error injecting BetterDiscord.")
        print_error("Output:", pnpm_inject_result.stdout)
        print_error("Errors:", pnpm_inject_result.stderr)
        return
    
    print_success("BetterDiscord installed successfully.")

    restart_discord()

def restart_discord():
    """ Restart Discord if it is currently running """
    print_info("Checking if Discord is running...")
    
    # Check if Discord is running
    result = subprocess.run(['pgrep', 'discord'], capture_output=True, text=True)
    if result.returncode == 0:
        print_info("Discord is running. Restarting...")
        try:
            # Kill Discord process
            subprocess.run(['pkill', 'discord'], check=True)
            # Wait a moment for Discord to close properly
            print_info("Waiting for Discord to close...")
            subprocess.run(['sleep', '5'], check=True)
        except subprocess.CalledProcessError as e:
            print_error("Error stopping Discord.")
            print_error("Output:", e.stdout)
            print_error("Errors:", e.stderr)
            return
        
    else:
        print_error("Discord is not running.")

    # Restart Discord
    discord_path = find_discord_path()
    if discord_path:
        discord_executable = os.path.join(discord_path, 'discord')
        print_info(f"Starting Discord from {discord_executable}...")
        subprocess.run([discord_executable])
    else:
        print_error("Could not find Discord executable to restart.")

def main():
    parser = argparse.ArgumentParser(description="BetterDiscord Updater")
    parser.add_argument('command', choices=['update'], help="Command to execute")
    parser.add_argument('--type', choices=['canary', 'ptb'], default='canary', help="Injection type (canary or ptb)")

    args = parser.parse_args()
    
    # Check for required tools
    missing_tools = []
    for tool in ['git', 'npm', 'pnpm']:
        if not is_installed(tool):
            missing_tools.append(tool)
    
    if missing_tools:
        print_warning("Missing tools detected:")
        for tool in missing_tools:
            print(f"- {tool}")
        install_dependencies()
    else:
        print_info("All required tools are already installed.")
    
    discord_path = find_discord_path()
    if not discord_path:
        print_warning("Discord installation not found.")
        return
    
    current_version = get_current_discord_version(discord_path)
    previous_version = get_previous_discord_version()
    
    if current_version != previous_version:
        print_info(f"New version detected: {current_version}. Updating BetterDiscord...")
        update_betterdiscord(args.type)
        update_previous_discord_version(current_version)
    else:
        print_success("No update required. BetterDiscord is up-to-date.")

if __name__ == "__main__":
    main()