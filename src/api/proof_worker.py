from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from utils import common
import threading
import logging

class ProofWorker(QObject):
    """
    Worker class for running the proof generation and verification in a separate thread.
    """
    proof_result = pyqtSignal(bool, str, str)
    progress_update = pyqtSignal(str)
    status_update = pyqtSignal(str)

    def __init__(self, api, statement):
        super().__init__()
        self.api = api
        self.statement = statement
        self.refinements = 0
        self.paused = False
        self.stopped = False
        self.current_proof = None
        self.current_feedback = None

    def pause(self):
        """Pauses the worker's operation."""
        self.paused = True

    def stop(self):
        """Stops the worker's operation."""
        self.stopped = True

    def resume(self):
        """Resumes the worker's operation."""
        self.paused = False

    def run(self):
        """
        Main execution loop for generating and verifying proofs, with support for pause and stop states.
        """
        self.stopped = False
        self.paused = False

        # Initial Proof Generation
        self.current_proof = self.api.generate_proof_with_chatgpt(self.statement)
        is_valid, self.current_feedback, self.current_proof = self.api.verify_with_agda(self.current_proof)
        self.proof_result.emit(is_valid, self.current_proof, self.current_feedback)

        if is_valid:
            self.status_update.emit("Inactive")
            return

        while not is_valid:
            if self.stopped:
                self.handle_stop()
                return

            if self.refinements >= common.get_iterations_limit():
                self.handle_iteration_limit()
                return

            self.refinements += 1
            self.current_proof = self.api.refine_proof_with_chatgpt(self.statement, self.current_proof, self.current_feedback)

            # Refinement step
            is_valid, self.current_feedback, self.current_proof = self.api.verify_with_agda(self.current_proof)
            self.proof_result.emit(is_valid, self.current_proof, self.current_feedback)

            if is_valid:
                break

            if self.paused:
                self.handle_pause()

        if is_valid:
            self.proof_result.emit(True, self.api.clean_agda_code(self.current_proof), "Valid proof found.")
        self.status_update.emit("Inactive")

    def handle_stop(self):
        """Handles the stop state and emits relevant signals."""
        self.status_update.emit("Stopped")
        self.progress_update.emit(f"Iteration {self.refinements + 1}: Proof verification has been stopped.")
        self.proof_result.emit(False, self.current_proof, "Proof verification has been stopped.")

    def handle_iteration_limit(self):
        """Handles the case where the iteration limit is reached."""
        feedback = "Reached the iteration limit without finding a valid proof."
        self.proof_result.emit(False, self.api.clean_agda_code(self.current_proof), f"{self.current_feedback}\n\n{feedback}")
        self.status_update.emit("Inactive")

    def handle_pause(self):
        """Handles the pause state by idling the thread until resumed or stopped."""
        self.status_update.emit("Paused")
        self.progress_update.emit(f"Iteration {self.refinements + 1}: Proof verification is paused.")
        while self.paused and not self.stopped:
            QThread.msleep(100)
