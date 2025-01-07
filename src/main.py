import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from api.proof_verification_api import ProofVerificationAPI
from gui.main_window import ProofVerificationGUI
from dotenv import load_dotenv

if __name__ == '__main__':
    """
    Activate the system
    """
    load_dotenv()
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('img/logo.png'))
    api = ProofVerificationAPI()
    gui = ProofVerificationGUI(api)
    gui.show()
    sys.exit(app.exec_())
