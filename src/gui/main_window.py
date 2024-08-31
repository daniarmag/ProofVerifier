from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QMainWindow, QAction, QMessageBox, QApplication
from PyQt5.QtCore import pyqtSlot
import qdarkstyle
from utils.constants import VERSION



class ProofVerificationGUI(QMainWindow):
    def __init__(self, api):
        super().__init__()
        self.statement_input = self.dark_mode_action = self.result_display = self.proof_display = self.verify_button = self.central_widget = None
        self.api = api
        self.init_ui()
        self.dark_mode_action.setChecked(True)
        self.toggle_dark_mode(True)

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout(self.central_widget)
        self.create_menu_bar()
        # Statement Input Section
        layout.addWidget(QLabel("Mathematical Statement:"))
        self.statement_input = QTextEdit()
        self.statement_input.setPlaceholderText("Enter the mathematical statement here...")
        layout.addWidget(self.statement_input)
        self.verify_button = QPushButton("Generate and Verify Proof")
        self.verify_button.clicked.connect(self.on_verify)
        layout.addWidget(self.verify_button)
        # Proof Display Section
        layout.addWidget(QLabel("Generated Proof:"))
        self.proof_display = QTextEdit()
        self.proof_display.setReadOnly(True)
        layout.addWidget(self.proof_display)
        # Verification Result Section
        layout.addWidget(QLabel("Verification Result:"))
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)
        self.setWindowTitle("Proof Verification System")
        self.setGeometry(100, 100, 600, 500)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        # View Menu
        view_menu = menu_bar.addMenu("View")
        self.dark_mode_action = QAction("Enable Dark Mode", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)
        # About Menu
        about_menu = menu_bar.addMenu("About")
        version_action = QAction(f"Version: {VERSION}", self)
        version_action.triggered.connect(self.show_version)
        about_menu.addAction(version_action)

    def on_verify(self):
        statement = self.statement_input.toPlainText()
        self.api.generate_and_verify_proof(statement)

    @pyqtSlot(bool, str, str)
    def display_result(self, is_valid, proof, feedback):
        self.proof_display.setPlainText(f"The Proof:\n\n{proof}")
        result = "Proof is valid." if is_valid else "Proof is invalid."
        self.result_display.setPlainText(f"Verification Result:\n{result}\n\nFeedback:\n{feedback}")

    def toggle_dark_mode(self, state):
        app = QApplication.instance()  # Get the existing QApplication instance
        if state:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        else:
            app.setStyleSheet("")

    def show_version(self):
        QMessageBox.information(self, "Version", f"Proof Verification System\nVersion: {VERSION}")
