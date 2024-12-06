import subprocess

def run_command(cmd: str, output: bool = False) -> tuple[bool, any]:
    try:
        if not output:
            p = subprocess.run([cmd], shell=True, capture_output=False, stdout=subprocess.DEVNULL)
        else:
            p = subprocess.run([cmd], shell=True, text=True, capture_output=True)
        return True, str(p.stdout)
    except subprocess.CalledProcessError as e:
        return False, e
