from PyQt5.QtCore import QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication
from utils import constants
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
        self.paused = True

    def stop(self):
        self.stopped = True

    def resume(self):
        self.paused = False

    def run(self):
        """
        Main execution method for generating and verifying proofs, handling pause and stop states.
        """
        self.stopped = False
        self.paused = False
        self.current_proof = self.api.generate_proof_with_chatgpt(self.statement)
        is_valid, self.current_feedback, self.current_proof = self.api.verify_with_agda(self.current_proof)
        self.proof_result.emit(is_valid, self.current_proof, self.current_feedback)
        if is_valid:
            self.status_update.emit("Inactive")
            return
        while not is_valid:
            if self.stopped:
                self.status_update.emit("Stopped")
                self.progress_update.emit(f"Iteration {self.refinements + 1}: Proof verification has been stopped.")
                self.proof_result.emit(is_valid, self.current_proof, "Proof Verification has been stopped.")
                return

            if self.refinements >= constants.ITERATIONS_LIMIT:
                feedback = "Reached the iteration limit without finding a valid proof."
                self.proof_result.emit(is_valid, self.api.clean_agda_code(self.current_proof), feedback)
                self.status_update.emit("Inactive")
                return

            self.refinements += 1

            self.current_proof = self.api.refine_proof_with_chatgpt(self.statement, self.current_proof, self.current_feedback)
            is_valid, self.current_feedback, self.current_proof = self.api.verify_with_agda(self.current_proof)
            self.proof_result.emit(is_valid, self.current_proof, self.current_feedback)

            if is_valid:
                break

            if self.paused:
                self.status_update.emit("Paused")
                self.progress_update.emit(f"Iteration {self.refinements + 1}: Proof verification is paused.")
                while self.paused and not self.stopped:
                    QThread.msleep(100)
        if is_valid:
            self.proof_result.emit(True, self.api.clean_agda_code(self.current_proof), "Valid proof found.")
        self.status_update.emit("Inactive")
