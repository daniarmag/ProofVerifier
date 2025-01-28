# ProofVerifier README

Welcome to the **ProofVerifier** tool! This document will guide you through the installation and setup process to ensure everything works seamlessly.

## Step 1: Install Agda

Agda is a dependently typed functional programming language and proof assistant. Follow these instructions to install it:

1. Visit the official Agda installation guide: [Agda Installation Instructions](https://agda.readthedocs.io/en/latest/getting-started/installation.html).
2. Follow the steps specific to your system:
   - Install GHC and Cabal (Cabal executable can usually be found in `C:\ghcup\bin\cabal.exe`).
   - Use `cabal install Agda` to install Agda (Agda executable can usually be found in `C:\cabal\bin\agda.exe`).
3. Verify the installation by running the following command in your terminal:
   ```bash
   cd <AGDA EXECUTABLE FOLDER HERE>
   agda --version
   ```
   You should see the version number if Agda is installed correctly.

---

## Step 2: Add Agda to the Windows Path

To ensure that Agda is accessible from anywhere on your system:

1. Open the **Start Menu** and search for Settings
2. Select **System**
3. In the **System** window, select **About**.
4. Under **About**, find and select `Advanced system settings`.
5. In the **System Properties** window, click the `Environment Variables` button.
6. Under **System Variables**, find and select the `Path` variable, then click Edit.
7. Click **New** and add the path to Agda's executable (e.g., `C:\cabal\bin\` where agda.exe is in the folder).
8. Click **OK** to save the changes.
9. Restart your terminal and verify Agda is in the path by typing:
   ```bash
   agda --version
   ```

---

## Step 3: Download ProofVerifier Executable

1. Download **ProofVerifier.exe** file from the following link: [ProofVerifier Executable](https://drive.google.com/drive/folders/1B8zW-dO9rcprNjXHAU0rktjUy5oluiBj?usp=drive_link).
2. Save the executable to a folder of your choice.

---

## Step 4: User Guide

For detailed instructions on how to use **ProofVerifier**, refer to the user guide provided here: [ProofVerifier User Guide](https://github.com/daniarmag/ProofVerifier/tree/main/files).

---

## Support

If you encounter any issues or have questions, please reach out:

- **Daniel Armaganian**: [daniarmag@gmail.com](mailto\:daniarmag@gmail.com)
- **Tzahi Bakal**: [Tzahi.Bakal@gmail.com](mailto\:Tzahi.Bakal@gmail.com)

---

Thank you for using ProofVerifier!

