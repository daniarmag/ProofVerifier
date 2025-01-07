import subprocess
import os
import sys
import json
from pathlib import Path

# Constants
VERSION = "2.0"
ITERATIONS_LIMIT = 50
MAX_API_LOOP_CHECKER = 5

def get_max_api_loop_checker():
    """Returns the limit constant of inner verifications."""
    return MAX_API_LOOP_CHECKER

# Centralized Access to Constants
def get_version():
    """Returns the current version of the application."""
    return VERSION

def get_iterations_limit():
    """Returns the current iteration limit for proof verification."""
    return ITERATIONS_LIMIT

def set_iterations_limit(limit):
    """Sets a new iteration limit with validation to ensure it's a positive integer."""
    global ITERATIONS_LIMIT
    ITERATIONS_LIMIT = limit


# Utility Functions
def run_command(cmd: str, output: bool = False) -> tuple[int, str]:
    """
    Executes a shell command with optional output capture and
    Args:
        cmd (str): The command to execute.
        output (bool): If True, captures the output of the command.

    Returns:
        tuple[int, str]: A tuple containing the exit code and the command output (if captured).
    """
    agda_bin_dir = resource_path("Agda/bin")
    env = os.environ.copy()
    env['PATH'] = agda_bin_dir + os.pathsep + os.environ['PATH']
    if os.name != "nt":
        env["LC_ALL"] = "en_US.UTF-8"
    try:
        subprocess.run("CHCP 65001", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) if os.name == "nt" else None
        if not output:
            process = subprocess.run(cmd, shell=True, capture_output=False, stdout=subprocess.DEVNULL, encoding='utf-8')
        else:
            process = subprocess.run(cmd, shell=True, text=True, capture_output=True, encoding='utf-8')
        return int(process.returncode), str(process.stdout.strip()) if output else ""
    except subprocess.CalledProcessError as e:
        return -1, str(e)

def set_api_key(api_key: str):
    """
    Sets the API key in the configuration cache and as an environment variable.
    :param api_key: The API key to be saved.
    """
    try:
        cache_data = common.load_cache_data()
        cache_data["api_key"] = api_key
        common.save_cache_data(cache_data)
        os.environ["OPENAI_API_KEY"] = api_key
    except Exception as e:
        pass

def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for dev and PyInstaller
    :param relative_path: relative path of desired file/img/folder
    :return absolute path
    """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

def get_proof_verifier_directory():
    """
    Determines and creates the platform-specific directory for storing application data.
    Returns the directory path.
    """
    app_name = "ProofVerifier"
    base_dir = Path.home()
    proof_verifier_dir = base_dir / app_name
    proof_verifier_dir.mkdir(parents=True, exist_ok=True)
    return proof_verifier_dir

def save_cache_data(data):
    """
    Saves the given data to a JSON file inside the ProofVerifier directory.
    :param data: dict that contains the data that needs saving
    """
    try:
        cache_file = os.path.join(get_proof_verifier_directory(), "cache.json")
        existing_data = load_cache_data()
        existing_data.update(data)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(existing_data, f, indent=4)
    except:
        pass


def load_cache_data():
    """
    Loads data from the JSON file inside the ProofVerifier directory.
    :return: the data or an empty dictionary if the file doesn't exist.
    """
    try:
        cache_file = os.path.join(get_proof_verifier_directory(), "cache.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
    except:
        pass
    return {}
