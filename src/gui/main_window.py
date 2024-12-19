from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QMainWindow, QAction, QMessageBox, QApplication, QTabWidget, QHBoxLayout
from PyQt5.QtCore import pyqtSlot, QMetaObject, Qt, Q_ARG
from utils.constants import VERSION
from api.proof_worker import ProofWorker
import qdarkstyle
import re
import time



class ProofVerificationGUI(QMainWindow):
    """
   Initializes the ProofVerificationGUI.
   Currently defaulted to dark-mode.
   """
    def __init__(self, api):
        super().__init__()
        self.status_label = self.iteration_label = self.latest_result_display = self.latest_proof_display = self.latest_tab = self.tabs =\
            self.statement_input = self.dark_mode_action = self.result_display = self.proof_display = self.verify_button = self.central_widget = None
        self.api = api
        self.iteration_count = 0
        self.status = "Inactive"
        self.init_ui()
        self.dark_mode_action.setChecked(True)
        self.toggle_dark_mode(True)
        self.api.progress_update.connect(self.update_progress)
        self.api.proof_result.connect(self.display_result)
        self.api.update_status.connect(self.update_status)


    def init_ui(self):
        """
        Initializes the user interface of the proof verification GUI.
        """
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

        # Proof Display and Iterations Section
        self.tabs = QTabWidget()
        self.latest_tab = QWidget()
        latest_tab_layout = QVBoxLayout()
        self.latest_proof_display = QTextEdit()
        self.latest_proof_display.setReadOnly(True)
        latest_tab_layout.addWidget(QLabel("Latest Proof:"))
        latest_tab_layout.addWidget(self.latest_proof_display)
        self.latest_result_display = QTextEdit()
        self.latest_result_display.setReadOnly(True)
        latest_tab_layout.addWidget(QLabel("Latest Verification Result:"))
        latest_tab_layout.addWidget(self.latest_result_display)
        self.latest_tab.setLayout(latest_tab_layout)
        self.tabs.addTab(self.latest_tab, "Latest Iteration")
        layout.addWidget(self.tabs)

        # Iteration Info
        iteration_info_layout = QHBoxLayout()
        self.iteration_label = QLabel(f"Iteration: {self.iteration_count}")
        self.status_label = QLabel(f"Status: {self.status}")
        iteration_info_layout.addWidget(self.iteration_label)
        iteration_info_layout.addWidget(self.status_label)
        layout.addLayout(iteration_info_layout)

        self.setWindowTitle("Proof Verifier")
        self.setGeometry(100, 100, 600, 500)
        self.showMaximized()

    def create_menu_bar(self):
        """
        Creates the menu bar with options for dark mode and displaying version information.
        """
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

    @pyqtSlot(str)
    def update_progress(self, message: str):
        """
        Updates the progress of the proof generation and verification process.
        """
        if "Iteration" in message:
            match = re.search(r"Iteration (\d+):", message)
            if match:
                self.iteration_count = int(match.group(1))
                self.iteration_label.setText(f"Iteration: {self.iteration_count}")
        if message:
            time.sleep(0.1)
            QMetaObject.invokeMethod(
                self.latest_result_display,
                "append",
                Qt.QueuedConnection,
                Q_ARG(str, message)
            )

    def update_status(self, status):
        """
        Updates the status label based on the signal from the worker.
        """
        self.status = status
        self.status_label.setText(f"Status: {self.status}")

    def on_verify(self):
        """
        Handles the click event for the verify button.
        Retrieves the mathematical statement from the input field and triggers
        the proof generation and verification process using the provided API.
        """
        self.iteration_count = 0
        self.update_status("Active")
        self.iteration_label.setText(f"Iteration: {self.iteration_count}")

        # Clear the proof and result display areas
        self.latest_proof_display.clear()
        self.latest_result_display.clear()

        # Avoid clearing the tabs unnecessarily
        if self.tabs.count() > 1:
            self.tabs.removeTab(1)

        statement = self.statement_input.toPlainText()
        self.api.generate_and_verify_proof(statement)

    @pyqtSlot(bool, str, str)
    def display_result(self, is_valid, proof, feedback):
        """
        Displays the verification result and generated proof in the respective fields.
        """
        self.latest_proof_display.setPlainText(proof.strip())
        result = "Proof is valid." if is_valid else "Proof is invalid."
        self.latest_result_display.setPlainText(f"{result}\n\nFeedback:\n{feedback}")

        if self.iteration_count == 0:
            self.iteration_count = 1
            self.iteration_label.setText("Iteration: 1")
            self.add_iteration_tab("Iteration 1", proof, result, feedback)
            if is_valid:
                self.end_proof_verification()
            return
        if self.iteration_count > 0:
            self.iteration_count += 1
            tab_name = f"Iteration {self.iteration_count}"
            existing_tabs = [self.tabs.tabText(i) for i in range(self.tabs.count())]
            if tab_name not in existing_tabs:
                self.add_iteration_tab(tab_name, proof, result, feedback)
        if is_valid:
            self.end_proof_verification()

    def add_iteration_tab(self, tab_name, proof, result, feedback):
        """
        Adds a new tab for the current iteration with proof and feedback.
        """
        iteration_tab = QWidget()
        tab_layout = QVBoxLayout()

        proof_display = QTextEdit()
        proof_display.setPlainText(proof.strip())
        proof_display.setReadOnly(True)

        result_display = QTextEdit()
        result_display.setPlainText(f"{result}\n\nFeedback:\n{feedback}")
        result_display.setReadOnly(True)

        tab_layout.addWidget(QLabel("Proof:"))
        tab_layout.addWidget(proof_display)
        tab_layout.addWidget(QLabel("Verification Result:"))
        tab_layout.addWidget(result_display)

        iteration_tab.setLayout(tab_layout)
        self.tabs.addTab(iteration_tab, tab_name)

    def end_proof_verification(self):
        """
        Stops further verification and shows a success message.
        """
        self.status = "Inactive"
        self.status_label.setText(f"Status: {self.status}")
        QMessageBox.information(self, "Proof Verified", "A valid proof has been found!")

    def toggle_dark_mode(self, state):
        """
        Toggles the dark mode theme for the application.
        """
        app = QApplication.instance()  # Get the existing QApplication instance
        if state:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        else:
            app.setStyleSheet("")

    def show_version(self):
        """
        Displays the version information in a message box.
        """
        QMessageBox.information(self, "Version", f"Proof Verification System\nVersion: {VERSION}")
