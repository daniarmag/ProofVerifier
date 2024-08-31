import sys
from PyQt5.QtWidgets import QApplication
from api.proof_verification_api import ProofVerificationAPI
from gui.main_window import ProofVerificationGUI

if __name__ == '__main__':
    """
    Activate the system
    """
    app = QApplication(sys.argv)
    api = ProofVerificationAPI()
    gui = ProofVerificationGUI(api)
    api.proof_result.connect(gui.display_result)
    gui.show()
    sys.exit(app.exec_())
