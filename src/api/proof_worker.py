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

    def run(self):

        proof = self.api.generate_proof_with_chatgpt(self.statement)
        is_valid, feedback, proof = self.api.verify_with_agda(proof)
        self.proof_result.emit(is_valid, proof, feedback)
        if is_valid:
            self.status_update.emit("Inactive")
            return

        while not is_valid and self.refinements < constants.ITERATIONS_LIMIT:
            self.refinements += 1
            proof = self.api.refine_proof_with_chatgpt(self.statement, proof, feedback)
            is_valid, feedback, proof = self.api.verify_with_agda(proof)
            self.proof_result.emit(is_valid, proof, f"Iteration {self.refinements} Feedback:\n{feedback}")
            if is_valid:
                break
        feedback = "Reached the iteration limit without finding a valid proof." if not is_valid else "Valid proof found."
        self.proof_result.emit(is_valid, self.api.clean_agda_code(proof), feedback)
        self.status_update.emit("Inactive")
