import subprocess
import os

VERSION = "1.2.5"
ITERATIONS_LIMIT = 50

def run_command(cmd: str, output: bool = False) -> tuple[int, any]:
    agda_bin_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Agda", "bin")
    os.environ['PATH'] = agda_bin_dir + os.pathsep + os.environ['PATH']
    try:
        if not output:
            p = subprocess.run(cmd, shell=True, capture_output=False, stdout=subprocess.DEVNULL)
        else:
            p = subprocess.run(cmd, shell=True, text=True, capture_output=True)
        return int(p.returncode) , str(p.stdout)
    except subprocess.CalledProcessError as e:
        return -1, e

def get_version():
    return VERSION

def get_iterations_limit():
    return ITERATIONS_LIMIT

def set_iterations_limit(limit):
    global ITERATIONS_LIMIT
    ITERATIONS_LIMIT = limit
