from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QMainWindow, QAction, QMessageBox,
                             QApplication, QTabWidget, QHBoxLayout, QInputDialog, QLineEdit, QFileDialog, QProgressDialog, QDialog)
from PyQt5.QtCore import pyqtSlot, QMetaObject, Qt, Q_ARG, QSize
from PyQt5.QtGui import QIcon, QTextDocument
from PyQt5.QtPrintSupport import QPrinter
from utils import common
from api.proof_worker import ProofWorker
from gui.user_guide_window import UserGuideWindow
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from pathlib import Path
from datetime import datetime
import qdarkstyle
import re
import time
import os
import logging
logging.basicConfig(
    filename=os.path.join(common.get_proof_verifier_directory(), 'ProofVerifier.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s')


class ProofVerificationGUI(QMainWindow):
    """
    Main GUI class for Proof Verification System.
    """
    def __init__(self, api):
        super().__init__()
        self.status_label = self.iteration_label = self.latest_result_display = self.latest_proof_display = self.latest_tab = self.tabs =\
            self.statement_input = self.dark_mode_action = self.result_display = self.proof_display = self.central_widget = None
        self.verify_button = self.resume_button = self.stop_button = self.pause_button = self.user_guide_window = None
        self.api = api
        self.iteration_count = 0
        self.status = "Inactive"
        self.verdict = "Not Set"
        self.temp_files = ['temp_proof.agda', 'temp_proof.agdai']
        self.is_paused = False
        self.init_ui()
        self.restore_configuration()
        self.connect_signals()


    def init_ui(self):
        """
        Initializes the user interface of the proof verification GUI.
        """
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Main Layout
        main_layout = QVBoxLayout(self.central_widget)
        self.create_menu_bar()
        main_layout.addLayout(self.create_top_row_section())
        main_layout.addWidget(self.create_input_section())
        main_layout.addWidget(self.create_tabs_section())
        main_layout.addLayout(self.create_status_section())

        self.setWindowTitle("Proof Verifier")
        self.setGeometry(100, 100, 600, 500)
        self.showMaximized()

    def restore_configuration(self):
        try:
            cache_data = common.load_cache_data()
            dark_mode = cache_data.get("dark_mode", True)
            self.dark_mode_action.setChecked(dark_mode)
            self.toggle_dark_mode(dark_mode)
            iterations_limit = cache_data.get("iterations_limit", common.get_iterations_limit())
            common.set_iterations_limit(iterations_limit)
            api_key = cache_data.get("api_key", "")
            logging.debug(f"restore_configuration: {api_key}")
            if api_key:
                common.set_api_key(api_key)
            else:
                if "OPENAI_API_KEY" in os.environ:
                    del os.environ["OPENAI_API_KEY"]
        except Exception as e:
            logging.debug(f"Error restoring configuration: {e}")

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
        set_api_action = QAction("Set API Key", self)
        set_api_action.triggered.connect(self.configure_api_key)
        config_menu.addAction(set_api_action)

        # Help Menu
        help_menu = menu_bar.addMenu("Help")
        user_help_action = QAction("User Help", self)
        user_help_action.triggered.connect(self.open_user_guide)
        help_menu.addAction(user_help_action)
        contact_action = QAction("Contact Us", self)
        contact_action.triggered.connect(self.show_contact_info)
        help_menu.addAction(contact_action)
        about_submenu = help_menu.addMenu("About")
        version_action = QAction(f"Version: {common.get_version()}", self)
        version_action.triggered.connect(self.show_version)
        about_submenu.addAction(version_action)

    def create_top_row_section(self):
        """Creates the create top row section layout."""
        top_row_layout = QHBoxLayout()

        buttons_layout = QHBoxLayout()
        self.verify_button = self.create_icon_button(common.resource_path("img/verify.png"), "Start Verification Process", self.on_verify)
        self.pause_button = self.create_icon_button(common.resource_path("img/pause.png"), "Pause Verification Process", self.on_pause)
        self.resume_button = self.create_icon_button(common.resource_path("img/resume.png"), "Resume Verification Process", self.on_resume)
        self.stop_button = self.create_icon_button(common.resource_path("img/stop.png"), "Stop Verification Process", self.on_stop)

        buttons_layout.addWidget(self.verify_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.resume_button)
        buttons_layout.addWidget(self.stop_button)

        top_row_layout.addWidget(QLabel("Mathematical Statement:"))
        top_row_layout.addLayout(buttons_layout)
        return top_row_layout

    def create_input_section(self):
        """Creates the input section layout."""
        self.statement_input = QTextEdit()
        self.statement_input.setPlaceholderText("Enter the mathematical statement here...")
        self.statement_input.textChanged.connect(self.on_statement_changed)
        return self.statement_input

    def create_tabs_section(self):
        """Creates the tabs section for displaying proofs and results."""
        self.tabs = QTabWidget()
        self.latest_tab = QWidget()
        latest_tab_layout = QVBoxLayout()

        self.latest_proof_display = QTextEdit()
        self.latest_proof_display.setReadOnly(True)
        self.latest_result_display = QTextEdit()
        self.latest_result_display.setReadOnly(True)

        latest_tab_layout.addWidget(QLabel("Latest Proof:"))
        latest_tab_layout.addWidget(self.latest_proof_display)
        latest_tab_layout.addWidget(QLabel("Latest Verification Result:"))
        latest_tab_layout.addWidget(self.latest_result_display)

        self.latest_tab.setLayout(latest_tab_layout)
        self.tabs.addTab(self.latest_tab, "Latest Iteration")
        return self.tabs

    def create_status_section(self):
        """Creates the status section layout."""
        layout = QHBoxLayout()
        self.iteration_label = QLabel(f"Iteration: {self.iteration_count}")
        self.status_label = QLabel(f"Status: {self.status}")
        layout.addWidget(self.iteration_label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        return layout

    def create_icon_button(self, icon_path, tooltip, callback):
        """
        Helper to create a QPushButton with an icon.
        :param icon_path: path to the icon
        :param tooltip: tooltip for when user hovers the button
        :param callback: OnClick function
        :return:
        """
        button = QPushButton()
        button.setIcon(QIcon(icon_path))
        button.setEnabled(False)
        button.setIconSize(QSize(24, 24))
        button.setFixedSize(36, 36)
        button.setToolTip(tooltip)
        button.clicked.connect(callback)
        return button

    def connect_signals(self):
        """Connects API signals to the GUI methods."""
        self.api.progress_update.connect(self.update_progress)
        self.api.proof_result.connect(self.display_result)
        self.api.update_status.connect(self.update_status)

    def configure_setting(self, title, label, cache_key, default_value, is_number=False, min_value=None, max_value=None, env_var=None):
        """
        Generic method to configure a setting via a dialog, save it to the cache, and optionally update an environment variable.
        :param title: Title of the dialog window
        :param label: Label text for the input field
        :param cache_key: The key in the cache to update
        :param default_value: The default value if the cache does not contain the key
        :param is_number: Whether the input is numeric
        :param min_value: Minimum value for numeric inputs (optional)
        :param max_value: Maximum value for numeric inputs (optional)
        :param env_var: Name of the environment variable to update (optional)
        """
        if self.status in ["Active", "Paused"]:
            QMessageBox.warning(
                self,
                f"{title} Config",
                f"You cannot configure {title} while the verification process is active. "
                "Retry when the status of program is stopped or inactive."
            )
            return

        try:
            success = False
            cache_data = common.load_cache_data()
            new_value = cache_data.get(cache_key, default_value)
            dialog = QInputDialog(self)
            dialog.setWindowTitle(f"Set {title}")
            dialog.setLabelText(label)
            dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)
            if is_number:
                dialog.setIntRange(min_value, max_value)
                dialog.setIntValue(int(new_value))
                if dialog.exec_() == QInputDialog.Accepted:
                    new_value = dialog.intValue()
                    success = True
            else:
                dialog.setTextValue(new_value)
                if dialog.exec_() == QInputDialog.Accepted:
                    new_value = dialog.textValue().strip()
                    if not new_value:
                        QMessageBox.critical(self, "title", "OpenAI API key cannot be an empty string.")
                    success = bool(new_value)
            if not success:
                return
            cache_data[cache_key] = new_value
            common.save_cache_data(cache_data)
            if env_var:
                os.environ[env_var] = new_value
            QMessageBox.information(self, title, f"{title} updated successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while updating {title}: {e}")

    def configure_iterations_limit(self):
        """
        Opens a dialog for the user to set the number of iterations limit dynamically.
        """
        self.configure_setting(
            title="Iterations Limit",
            label="Enter the maximum number of iterations:",
            cache_key="iterations_limit",
            default_value=common.get_iterations_limit(),
            is_number=True,
            min_value=1,
            max_value=1000
        )

    def configure_api_key(self):
        """
        Opens a dialog for the user to input or update their API key.
        """
        self.configure_setting(
            title="API Key",
            label="Enter your API key:",
            cache_key="api_key",
            default_value="",
            is_number=False,
            env_var="OPENAI_API_KEY"
        )

    def show_contact_info(self):
        """
        Displays contact information in a dialog with selectable and copyable text.
        """
        contact_dialog = QDialog(self)
        contact_dialog.setWindowTitle("Contact Us")
        contact_dialog.setMinimumSize(400, 150)
        layout = QVBoxLayout(contact_dialog)
        contact_message = (
            "If you need assistance, please contact us:\n\n"
            "Daniel Armaganian:\n"
            "Email: daniarmag@gmail.com\n"
            "Tzahi Bakal:\n"
            "Email: tzahi.bakal@gmail.com\n\n"
            "We value your feedback and are here to help!"
        )
        text_area = QTextEdit(contact_dialog)
        text_area.setPlainText(contact_message)
        text_area.setReadOnly(True)
        text_area.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
        layout.addWidget(text_area)

        close_button = QPushButton("Close", contact_dialog)
        close_button.clicked.connect(contact_dialog.close)
        layout.addWidget(close_button)
        contact_dialog.setLayout(layout)
        contact_dialog.exec_()

    def open_user_guide(self):
        """
        Opens the User Guide window with an embedded PDF viewer.
        """
        pdf_path = common.resource_path(os.path.join("files", "Proof_Verifier_User_help.pdf"))
        if not os.path.exists(pdf_path):
            QMessageBox.critical(self, "Error", f"User guide not found at: {pdf_path}")
            return
        self.user_guide_window = UserGuideWindow(pdf_path)
        self.user_guide_window.show()

    def save_to_pdf(self):
        """
        Saves the content to a PDF file using QTextDocument and HTML rendering.
        Adds a summary page and separates tabs with clear formatting.
        """
        if self.tabs.count() < 2 or self.status not in ["Inactive", "Stopped"]:
            QMessageBox.warning(self, "Save to PDF", "Cannot save to PDF. Ensure the process is complete and there are tabs available.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = os.path.join(str(Path.home() / "Downloads"), f"proof_verification_{timestamp}.pdf")
        if file_name:
            try:
                # Progress dialog
                progress_dialog = QProgressDialog("Saving to PDF...", "Cancel", 0, 100, self)
                progress_dialog.setWindowTitle("Saving to PDF")
                progress_dialog.setWindowModality(Qt.WindowModal)
                progress_dialog.setMinimumDuration(0)
                progress_dialog.setValue(0)

                document = QTextDocument()
                html_content = '<html><head><meta charset="UTF-8"></head><body>'
                html_content += '<h1>Proof Verification Summary</h1>'
                html_content += '<hr>'
                html_content += '<h2>Mathematical Statement:</h2>'
                statement = self.statement_input.toPlainText().strip()
                html_content += f'<p>{statement if statement else "N/A"}</p>'
                html_content += f'<h2>Total Iterations:</h2><p>{self.iteration_count}</p>'
                html_content += f'<h2>Result:</h2><p>{self.verdict}</p>'
                total_steps = self.tabs.count() + 1
                progress_increment = 100 // total_steps
                progress = 0
                progress_dialog.setValue(progress)
                for i in range(self.tabs.count()):
                    tab_name = self.tabs.tabText(i)
                    tab = self.tabs.widget(i)
                    html_content += f'<h2>{tab_name}</h2>'
                    html_content += '<hr>'
                    for child in tab.children():
                        if isinstance(child, QLabel):
                            section_header = child.text()
                            html_content += f'<h3>{section_header}</h3>'
                        if isinstance(child, QTextEdit):
                            content = child.toPlainText().replace("\n", "<br>")
                            html_content += f'<p>{content}</p>'
                    html_content += '<hr>'
                    progress += progress_increment
                    progress_dialog.setValue(min(progress, 90))
                html_content += '</body></html>'
                document.setHtml(html_content)
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_name)
                document.print(printer)
                progress_dialog.setValue(100)
                progress_dialog.close()
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
            "Pausing...": "#87CEEB",
            "Stopped": "#FF6347",
            "Stopping...": "#FF6347",
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
        if "OPENAI_API_KEY" not in os.environ:
            QMessageBox.critical(self, "No OpenAI API Key", "Cannot start verification process before setting OpenAI API Key.")
            return
        self.initiateProof()
        statement = self.statement_input.toPlainText()
        self.api.generate_and_verify_proof(statement)

    def initiateProof(self):
        """
        Initiates all needed GUI elements.
        """
        self.iteration_count = 0
        self.update_status("Active")
        self.iteration_label.setText(f"Iteration: {self.iteration_count}")

        # Clear the proof and result display areas
        self.latest_proof_display.clear()
        self.latest_result_display.clear()

        # Avoid clearing the tabs unnecessarily
        while self.tabs.count() > 1:
            self.tabs.removeTab(1)

    def on_resume(self):
        """
        Handles resume button functionality
        """
        self.update_status("Active")
        self.update_button_states()
        self.api.resume_proof()

    def on_pause(self):
        """
        Handles pause button functionality
        """
        self.update_status("Pausing...")
        self.update_button_states()
        self.api.pause_proof()

    def on_stop(self):
        """
        Handles stop button functionality
        """
        self.update_status("Stopping...")
        self.update_button_states()
        self.api.stop_proof()

    def on_statement_changed(self):
        """
        Handler for when the statement input text changes.
        Enables/disables the verify button based on whether there is non-whitespace content.
        """
        text = self.statement_input.toPlainText().strip()
        should_enable = bool(text) and self.status in ["Inactive", "Stopped"]
        self.verify_button.setEnabled(should_enable)

    def update_button_states(self):
        """
        Handles the buttons based on the current GUI tool-status.
        """
        text = self.statement_input.toPlainText().strip()
        self.verify_button.setEnabled(bool(text) and self.status in ["Inactive", "Stopped"])
        self.resume_button.setEnabled(self.status == "Paused")
        self.pause_button.setEnabled(self.status == "Active")
        self.stop_button.setEnabled(self.status in ["Active", "Paused"])

    @pyqtSlot(bool, str, str)
    def display_result(self, is_valid, proof, feedback):
        """
        Displays the verification result and generated proof in the respective fields.
        :param is_valid: bool True = Valid | False = Invalid
        :param proof: proof to display
        :param feedback: feedback to display
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

        if is_valid:
            self.end_proof_verification()

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

    def add_iteration_tab(self, tab_name, proof, result, feedback):
        """
        Adds a new tab for the current iteration with proof and feedback.
        :param tab_name: name of the tab
        :param proof: the current proof (initial/refined)
        :param result: bool - Valid = True | Invalid = False
        :param feedback: Agda compiler feedback.
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
        :param status: stopped/inactive status.
        :param failed: parameter used for when the verification process reaches the iteration limit.
        :return:
        """
        self.status = status
        self.status_label.setText(f"Status: {self.status}")
        if failed:
            msg = "Proof Verification Failed!\nReached the iteration limit without finding a valid proof."
            QMessageBox.critical(self, "Proof Failed", msg)
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


    def closeEvent(self, event):
        """
        Override the close event to perform cleanup before closing the application.
        :param event: event
        """
        try:
            self.cleanup_temp_files()
            event.accept()
        except Exception:
            event.accept()
        finally:
            logging.debug("closeEvent: Good Bye.")

    def cleanup_temp_files(self) -> None:
        """
        Remove temporary files created during program execution.
        """
        for temp_file in self.temp_files:
            try:
                temp_file = os.path.join(os.path.abspath("."), temp_file)
                if os.path.exists(temp_file):
                    logging.debug("Cleaning up files before exit...")
                    os.remove(temp_file)
            except Exception:
                pass

    def toggle_dark_mode(self, enabled: bool) -> None:
        """
        Toggles the dark mode theme for the application.
        :param enabled: enabled or disabled (Bool)
        """
        app = QApplication.instance()
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5() if enabled else "")
        try:
            cache_data = common.load_cache_data()
            cache_data["dark_mode"] = enabled
            common.save_cache_data(cache_data)
        except Exception as e:
            logging.debug(e)

    def show_version(self) -> None:
        """
        Displays the version information in a message box.
        """
        QMessageBox.information(self, "Version", f"Proof Verification System\nVersion: {common.get_version()}")
