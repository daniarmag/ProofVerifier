import os
import subprocess
import sys
import winreg

def install_haskell():
    """Installs Haskell via GHCup."""
    print("Installing Haskell...")
    if os.name == 'nt':
        subprocess.run(
            [
                "powershell",
                "-Command",
                "Set-ExecutionPolicy Bypass -Scope Process -Force;"
                "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072;"
                "Invoke-WebRequest https://www.haskell.org/ghcup/sh/bootstrap-haskell.ps1 -UseBasicParsing | Invoke-Expression"
            ],
            check=True
        )
    else:
        subprocess.run(
            ["curl", "--proto", "=https", "--tlsv1.2", "-sSf", "https://get-ghcup.haskell.org"],
            check=True
        )
        subprocess.run(["sh"], check=True)

def install_agda(clone_dir):
    print("Installing Agda...")
    subprocess.run(["cabal", "update"], check=True)
    subprocess.run(["cabal", "install", "Agda", "--overwrite-policy=always"], check=True)
    agda_path = os.path.join("C:\\cabal\\bin", "agda.exe")
    if os.path.exists(agda_path):
        print(f"Agda found at {agda_path}.")
        copy_agda_to_repo(agda_path, repo_dir)

def install_dependencies():
    print("Installing dependencies...")
    if os.name == 'posix':
        subprocess.run(["sudo", "apt-get", "install", "-y", "zlib1g-dev", "libncurses5-dev", "git"], check=True)

def copy_agda_to_repo(agda_path, repo_dir):
    """Copies the Agda directory to the ProofVerifier repo."""
    destination = os.path.join(repo_dir, "agda_bin")
    if not os.path.exists(destination):
        print(f"Copying Agda from {agda_path} to {destination}...")
        shutil.copytree(agda_path, destination)
        print("Agda successfully copied.")
    else:
        print("Agda already exists in the repository. Skipping copy.")

def check_agda(repo_dir):
    """Checks if Agda is installed and accessible."""
    agda_path = os.path.join("C:\\cabal\\bin")
    if os.path.exists(os.path.join(agda_path, "agda.exe")):
        print(f"Agda found at {agda_path}.")
        copy_agda_to_repo(agda_path, repo_dir)
        return True
    else:
        print("Agda is not installed or not found in C:\\cabal\\bin.")
        return False


def check_pyinstaller():
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, stdout=subprocess.PIPE)
        print("PyInstaller is already installed.")
        return True
    except FileNotFoundError:
        print("PyInstaller is not installed. Installing now...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        return True


def check_git():
    try:
        subprocess.run(["git", "--version"], check=True, stdout=subprocess.PIPE)
        print("Git is already installed.")
        return True
    except FileNotFoundError:
        print("Git is not installed. Installing now...")
        if os.name == 'posix':
            subprocess.run(["sudo", "apt-get", "install", "-y", "git"], check=True)
        elif os.name == 'nt':
            print("Please install Git manually from https://git-scm.com/downloads.")
            sys.exit(1)


def clone_github_repo(repo_url, clone_dir):
    if not os.path.exists(clone_dir):
        print(f"Cloning GitHub repository from {repo_url}...")
        subprocess.run(["git", "clone", repo_url, clone_dir], check=True)
    else:
        print(f"Directory {clone_dir} already exists. Skipping clone.")


def build_application_with_spec(spec_file):
    print(f"Building application with spec file: {spec_file}...")
    subprocess.run(["pyinstaller", spec_file], check=True)


def main():
    check_git()
    repo_url = "https://github.com/daniarmag/ProofVerifier.git"
    clone_dir = "cloned_repo"

    clone_github_repo(repo_url, clone_dir)
    os.chdir(clone_dir)

    if not check_agda(clone_dir):
        if os.name == 'posix':
            install_dependencies()
        install_haskell()
        install_agda(clone_dir)

    check_pyinstaller()
    spec_file = os.path.join(os.getcwd(), "files/ProofVerifier.spec")
    if not os.path.exists(spec_file):
        print(f"Error: Spec file '{spec_file}' not found.")
        sys.exit(1)
    build_application_with_spec(spec_file)

if __name__ == "__main__":
    main()
