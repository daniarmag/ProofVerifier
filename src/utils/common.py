import subprocess
import os

# Constants
VERSION = "1.2.5"
ITERATIONS_LIMIT = 50

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
    agda_bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Agda", "bin")
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
