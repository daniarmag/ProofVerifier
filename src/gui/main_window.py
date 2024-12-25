from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QMainWindow, QAction, QMessageBox, QApplication, QTabWidget, QHBoxLayout, QInputDialog, QFileDialog
from PyQt5.QtCore import pyqtSlot, QMetaObject, Qt, Q_ARG, QSize
from PyQt5.QtGui import QIcon
from utils import common
from api.proof_worker import ProofWorker
from gui.user_guide_window import UserGuideWindow
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pathlib import Path
from datetime import datetime
import qdarkstyle
import re
import time
import os

class ProofVerificationGUI(QMainWindow):
    """
   Initializes the ProofVerificationGUI.
   Currently defaulted to dark-mode.
   """
    def __init__(self, api):
        super().__init__()
        self.status_label = self.iteration_label = self.latest_result_display = self.latest_proof_display = self.latest_tab = self.tabs =\
            self.statement_input = self.dark_mode_action = self.result_display = self.proof_display = self.central_widget = None
        self.verify_button = self.play_button = self.stop_button = self.pause_button = self.user_guide_window = None
        self.api = api
        self.iteration_count = 0
        self.status = "Inactive"
        self.verdict = "Not Set"
        self.is_paused = False
        self.init_ui()
        self.dark_mode_action.setChecked(True)
        ProofVerificationGUI.toggle_dark_mode(True)
        self.api.progress_update.connect(self.update_progress)
        self.api.proof_result.connect(self.display_result)
        self.api.update_status.connect(self.update_status)


    def init_ui(self):
        """
        Initializes the user interface of the proof verification GUI.
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_layout = QVBoxLayout(self.central_widget)
        self.create_menu_bar()

        # Statement Input Section
        top_row_layout = QHBoxLayout()
        top_row_layout.addWidget(QLabel("Mathematical Statement:"))
        button_layout = QHBoxLayout()
        self.verify_button = QPushButton()
        self.verify_button.setIcon(QIcon("img/verify.png"))
        self.verify_button.setIconSize(QSize(24, 24))
        self.verify_button.setFixedSize(36, 36)
        self.verify_button.setToolTip("Start Verification Process")
        self.verify_button.clicked.connect(self.on_verify)
        self.play_button = QPushButton()
        self.play_button.setEnabled(False)
        self.play_button.setIcon(QIcon("img/resume.png"))
        self.play_button.setIconSize(QSize(24, 24))
        self.play_button.setFixedSize(36, 36)
        self.play_button.setToolTip("Resume Verification Process")
        self.play_button.clicked.connect(self.on_play)
        self.pause_button = QPushButton()
        self.pause_button.setEnabled(False)
        self.pause_button.setIcon(QIcon("img/pause.png"))
        self.pause_button.setIconSize(QSize(24, 24))
        self.pause_button.setFixedSize(36, 36)
        self.pause_button.setToolTip("Pause Verification Process")
        self.pause_button.clicked.connect(self.on_pause)
        self.stop_button = QPushButton()
        self.stop_button.setEnabled(False)
        self.stop_button.setIcon(QIcon("img/stop.png"))
        self.stop_button.setIconSize(QSize(24, 24))
        self.stop_button.setFixedSize(36, 36)
        self.stop_button.setToolTip("Stop Verification Process")
        self.stop_button.clicked.connect(self.on_stop)
        button_layout.addWidget(self.verify_button)
        button_layout.addWidget(self.pause_button)
        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.stop_button)
        top_row_layout.addLayout(button_layout)
        main_layout.addLayout(top_row_layout)

        # Mathematical statement screen
        self.statement_input = QTextEdit()
        self.statement_input.setPlaceholderText("Enter the mathematical statement here...")
        main_layout.addWidget(self.statement_input)


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
        main_layout.addWidget(self.tabs)

        # Iteration Info
        iteration_info_layout = QHBoxLayout()
        self.iteration_label = QLabel(f"Iteration: {self.iteration_count}")
        self.status_label = QLabel(f"Status: {self.status}")
        iteration_info_layout.addWidget(self.iteration_label)
        iteration_info_layout.addStretch()
        iteration_info_layout.addWidget(self.status_label)
        main_layout.addLayout(iteration_info_layout)

        self.setWindowTitle("Proof Verifier")
        self.setGeometry(100, 100, 600, 500)
        self.showMaximized()

    def create_menu_bar(self):
        """
        Creates the menu bar with options for dark mode and displaying version information.
        """
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("File")
        save_pdf_action = QAction("Save to PDF", self)
        save_pdf_action.triggered.connect(self.save_to_pdf)
        file_menu.addAction(save_pdf_action)

        # View Menu
        view_menu = menu_bar.addMenu("View")
        self.dark_mode_action = QAction("Enable Dark Mode", self)
        self.dark_mode_action.setCheckable(True)
        self.dark_mode_action.triggered.connect(self.toggle_dark_mode)
        view_menu.addAction(self.dark_mode_action)

        # Configuration Menu
        config_menu = menu_bar.addMenu("Config")
        iterations_action = QAction("Set Iterations Limit", self)
        iterations_action.triggered.connect(self.configure_iterations_limit)
        config_menu.addAction(iterations_action)

        # Help Menu
        help_menu = menu_bar.addMenu("Help")
        user_help_action = QAction("User Help", self)
        user_help_action.triggered.connect(self.open_user_guide)
        help_menu.addAction(user_help_action)

        about_submenu = help_menu.addMenu("About")
        version_action = QAction(f"Version: {common.get_version()}", self)
        version_action.triggered.connect(self.show_version)
        about_submenu.addAction(version_action)

    def configure_iterations_limit(self):
        """
        Opens a dialog for the user to set the number of iterations limit dynamically.
        """
        # Create the input dialog
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Set Iterations Limit")
        dialog.setLabelText("Enter the maximum number of iterations:")
        dialog.setIntValue(common.get_iterations_limit())
        dialog.setIntRange(1, 1000)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        if dialog.exec_() == QInputDialog.Accepted:
            new_limit = dialog.intValue()
            common.set_iterations_limit(new_limit)
            QMessageBox.information(self, "Iterations Limit Updated", f"The iterations limit has been updated to {new_limit}.")

    def open_user_guide(self):
        """
        Opens the User Guide window with an embedded PDF viewer.
        """
        pdf_path = os.path.join("files", "user_guide.pdf")
        if not os.path.exists(pdf_path):
            QMessageBox.critical(self, "Error", f"User guide not found at: {pdf_path}")
            return
        self.user_guide_window = UserGuideWindow(pdf_path)
        self.user_guide_window.show()

    # Todo: Fix save_to_pdf
    # Todo: Disable verification submitting if math statement window is empty
    def save_to_pdf(self):
        """
        Saves the content to a PDF file. Adds a summary page and separates tabs with clear formatting.
        """
        if self.tabs.count() < 2 or self.status not in ["Inactive", "Stopped"]:
            QMessageBox.warning(self, "Save to PDF",
                                "Cannot save to PDF. Ensure the process is complete and there are tabs available.")
            return
        downloads_path = str(Path.home() / "Downloads")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = os.path.join(downloads_path, f"proof_verification_{timestamp}.pdf")
        if file_name:
            try:
                pdf = canvas.Canvas(file_name, pagesize=letter)
                pdf.setFont("Helvetica", 10)

                pdf.drawString(50, 770, "Proof Verification Summary")
                pdf.line(50, 765, 550, 765)
                pdf.drawString(50, 740, "Mathematical Statement:")
                statement = self.statement_input.toPlainText().strip()
                pdf.drawString(70, 725, statement if statement else "N/A")
                pdf.drawString(50, 700, f"Total Iterations: {self.iteration_count}")
                pdf.drawString(50, 660, f"Result: {self.verdict}")
                pdf.showPage()

                for i in range(self.tabs.count()):
                    tab_name = self.tabs.tabText(i)
                    tab = self.tabs.widget(i)
                    pdf.setFont("Helvetica-Bold", 12)
                    pdf.drawString(50, 770, tab_name)
                    pdf.setFont("Helvetica", 10)
                    pdf.line(50, 765, 550, 765)
                    y_position = 740

                    for child in tab.children():
                        if isinstance(child, QLabel):
                            section_header = child.text()
                            pdf.setFont("Helvetica-Bold", 12)
                            pdf.drawString(50, y_position, section_header)
                            y_position -= 20
                            pdf.setFont("Helvetica", 10)

                        if isinstance(child, QTextEdit):
                            content = child.toPlainText()
                            text_lines = content.split("\n")
                            for line in text_lines:
                                if y_position < 50:  # Add a new page if content exceeds page height
                                    pdf.showPage()
                                    pdf.setFont("Helvetica-Bold", 12)
                                    pdf.drawString(50, 770, f"Tab {i + 1}: {tab_name}")
                                    pdf.setFont("Helvetica", 10)
                                    y_position = 740

                                pdf.drawString(50, y_position, line)
                                y_position -= 15

                    # Separator between tabs
                    if i != self.tabs.count() - 1:  # Add separator only if not the last tab
                        pdf.showPage()

                pdf.save()
                QMessageBox.information(self, "Save to PDF", f"The content has been successfully saved to PDF!\nSave location: {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Save to PDF", f"An error occurred: {e}")

    @pyqtSlot(str)
    def update_progress(self, message: str):
        """
        Updates the progress of the proof generation and verification process.
        :param message: updates iteration number or the result display.
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
        color = {
            "Paused": "#87CEEB",
            "Pausing": "#87CEEB",
            "Stopped": "#FF6347",
            "Stopping": "#FF6347",
            "Active": "#32CD32",
            "Inactive": "#D3D3D3",
        }.get(status, "#D3D3D3")
        self.status_label.setStyleSheet(f"color: {color};")
        self.update_button_states()

    def on_verify(self):
        """
        Handles the click event for the verify button.
        Retrieves the mathematical statement from the input field and triggers
        the proof generation and verification process using the provided API.
        """
        self.initiateProof()
        statement = self.statement_input.toPlainText()
        self.api.generate_and_verify_proof(statement)

    def initiateProof(self):
        self.iteration_count = 0
        self.update_status("Active")
        self.iteration_label.setText(f"Iteration: {self.iteration_count}")

        # Clear the proof and result display areas
        self.latest_proof_display.clear()
        self.latest_result_display.clear()

        # Avoid clearing the tabs unnecessarily
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)

    def on_play(self):
        self.update_status("Active")
        self.update_button_states()
        self.api.resume_proof()

    def on_pause(self):
        self.update_status("Pausing")
        self.update_button_states()
        self.api.pause_proof()

    def on_stop(self):
        self.update_status("Stopping")
        self.update_button_states()
        self.api.stop_proof()

    def update_button_states(self):
        self.verify_button.setEnabled(self.status in ["Inactive", "Stopped"])
        self.play_button.setEnabled(self.status == "Paused")
        self.pause_button.setEnabled(self.status == "Active")
        self.stop_button.setEnabled(self.status in ["Active", "Paused"])

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

        if self.status == "Stopped":
            self.end_proof_verification("Stopped")
            return

        if "iteration limit" in feedback.lower():
            tab_name = f"Iteration {self.iteration_count}"
            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == tab_name:
                    self.tabs.removeTab(i)
                    break
            self.add_iteration_tab(tab_name, proof, result, feedback)
            self.end_proof_verification(status="Inactive", failed=True)
            return

        if not is_valid and self.iteration_count < common.get_iterations_limit():
            self.iteration_count += 1
            self.iteration_label.setText(f"Iteration {self.iteration_count}")
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

    def end_proof_verification(self, status = "Inactive", failed = False):
        """
        Stops further verification and shows a success message.
        """

        self.status = status
        self.status_label.setText(f"Status: {self.status}")
        if failed:
            msg = "Reached the iteration limit without finding a valid proof."
            QMessageBox.critical(self, "Proof Failed", f"Proof Verification Failed!\n{msg}")
            self.verdict = msg
            return
        if status == "Stopped":
            msg = "Proof Verification process has been stopped!"
            QMessageBox.warning(self, "Proof Stopped", msg)
            self.verdict = f"No valid proof found. {msg}"
            return
        else:
            msg = "A valid proof has been found!"
            QMessageBox.information(self, "Proof Verified", msg)
            self.verdict = msg
            return

    @staticmethod
    def toggle_dark_mode(state):
        """
        Toggles the dark mode theme for the application.
        """
        app = QApplication.instance()
        if state:
            app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        else:
            app.setStyleSheet("")

    def show_version(self):
        """
        Displays the version information in a message box.
        """
        QMessageBox.information(self, "Version", f"Proof Verification System\nVersion: {common.get_version()}")
