import sys
from utils import common
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from api.proof_verification_api import ProofVerificationAPI
from gui.main_window import ProofVerificationGUI

if __name__ == '__main__':
    """
    Activate the system
    """
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(common.resource_path('img/logo.png')))
    api = ProofVerificationAPI()
    gui = ProofVerificationGUI(api)
    gui.show()
    sys.exit(app.exec_())
