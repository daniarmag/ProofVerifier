import subprocess
import os
import sys
import json
import logging
import tempfile
from pathlib import Path

# Constants
VERSION = "2.0"
ITERATIONS_LIMIT = 50
MAX_API_LOOP_CHECKER = 5

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

logging.basicConfig(
    filename=os.path.join(get_proof_verifier_directory(), 'ProofVerifier.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s')

def get_max_api_loop_checker():
    """Returns the limit constant of inner verifications."""
    return MAX_API_LOOP_CHECKER

# Centralized Access to Constants
def get_version():
    """Returns the current version of the application."""
    return VERSION

def get_iterations_limit():
    """Returns the current iteration limit for proof verification."""
    return load_cache_data().get("iterations_limit", ITERATIONS_LIMIT)

def set_iterations_limit(limit: int):
    """Sets a new iteration limit with validation to ensure it's a positive integer."""
    try:
        global ITERATIONS_LIMIT
        ITERATIONS_LIMIT = limit
        cache_data = load_cache_data()
        cache_data["iterations_limit"] = limit
        save_cache_data(cache_data)
        return True
    except Exception as e:
        logger.debug(f"set_iterations_limit error: {e}")
        return False

def setup_environment() -> dict:
    """
    Sets up the environment variables for the shell command.
    Returns:
        dict: A modified environment dictionary.
    """
    env = os.environ.copy()
    agda_bin_dir = os.path.join(os.path.abspath("."), "Agda", "bin")
    env['PATH'] = agda_bin_dir + os.pathsep + env.get('PATH', '')
    if os.name == "nt":
        env['PYTHONIOENCODING'] = 'utf-8'
        try:
            subprocess.run("CHCP 65001", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        except subprocess.CalledProcessError:
            logging.warning("Failed to set console code page to UTF-8")
    else:
        env["LC_ALL"] = "en_US.UTF-8"
    return env

def run_command(cmd: str, output: bool = False) -> tuple[int, str]:
    """
    Executes a shell command with optional output capture and
    Args:
        cmd (str): The command to execute.
        output (bool): If True, captures the output of the command.

    Returns:
        tuple[int, str]: A tuple containing the exit code and the command output (if captured).
    """
    feedback = ""
    env = setup_environment()
    try:
        logging.debug(f"Environment PATH: {env['PATH']}")
        if not output:
            process = subprocess.run(cmd, shell=True, capture_output=False, stdout=subprocess.DEVNULL, encoding='utf-8', env=env)
        else:
            process = subprocess.run(cmd, shell=True, text=True, capture_output=True, encoding='utf-8', env=env)
            feedback = process.stdout.strip() if process.stdout else f"Could not compile, exit code: {process.returncode}."
        logging.debug(f"Command completed. Stdout: {process.stdout is not None}, Stderr: {process.stderr is not None}")
        return int(process.returncode), feedback
    except Exception as e:
        logging.error(f"Unexpected Exception in run_command: {e}")
        return -1, str(e)

def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for dev and PyInstaller
    :param relative_path: relative path of desired file/img/folder
    :return absolute path
    """
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, relative_path)

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
    except Exception as e:
        logging.debug(f"save_cache_data:{e}")


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
    except Exception as e:
        logging.debug(f"load_cache_data:{e}")
    return {}
