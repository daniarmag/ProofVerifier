from PyQt5.QtCore import QObject, QThread, pyqtSignal
from utils import constants

class ProofWorker(QObject):
    """
    Worker class for running the proof generation and verification in a separate thread.
    """
    proof_result = pyqtSignal(bool, str, str)
    progress_update = pyqtSignal(str)  # Signal to send intermediate updates

    def __init__(self, api, statement):
        super().__init__()
        self.api = api
        self.statement = statement
        self.refinements = 0

    def run(self):
        """
        Runs the iterative proof generation and verification process.
        """
        proof = self.api.generate_proof_with_chatgpt(self.statement)
        is_valid, feedback, proof = self.api.verify_with_agda(proof)
        self.progress_update.emit(f"Iteration {self.refinements + 1}: Initial proof verification {'passed' if is_valid else 'failed'}.")
        self.proof_result.emit(is_valid, proof, "Initial proof attempt:\n" + feedback)
        while not is_valid and self.refinements < constants.ITERATIONS_LIMIT:
            self.refinements += 1
            self.progress_update.emit(f"Iteration {self.refinements}: Refining proof...")
            proof = self.api.refine_proof_with_chatgpt(self.statement, proof, feedback)
            is_valid, feedback, proof = self.api.verify_with_agda(proof)
            self.proof_result.emit(is_valid, proof, f"Iteration {self.refinements} Feedback:\n" + feedback)
            self.progress_update.emit(f"Iteration {self.refinements}: Proof verification {'passed' if is_valid else 'failed'}.")

        feedback = "Reached the iteration limit without finding a valid proof." if not is_valid else "Valid proof found."
        self.proof_result.emit(is_valid, self.api.clean_agda_code(proof), feedback)
