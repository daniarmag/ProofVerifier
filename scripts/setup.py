import os
import subprocess
import sys

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


def install_agda():
    print("Installing Agda...")
    subprocess.run(["cabal", "update"], check=True)
    subprocess.run(["cabal", "install", "Agda"], check=True)


def install_dependencies():
    print("Installing dependencies...")
    if os.name == 'posix':
        subprocess.run(["sudo", "apt-get", "install", "-y", "zlib1g-dev", "libncurses5-dev", "git"], check=True)


def check_agda():
    try:
        subprocess.run(["agda", "--version"], check=True, stdout=subprocess.PIPE)
        print("Agda is already installed.")
        return True
    except FileNotFoundError:
        print("Agda is not installed.")
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

    if not check_agda():
        if os.name == 'posix':
            install_dependencies()
        install_haskell()
        install_agda()

    check_pyinstaller()
    spec_file = os.path.join(os.getcwd(), "files/ProofVerifier.spec")
    if not os.path.exists(spec_file):
        print(f"Error: Spec file '{spec_file}' not found.")
        sys.exit(1)
    build_application_with_spec(spec_file)

if __name__ == "__main__":
    main()
