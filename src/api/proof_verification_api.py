import subprocess
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import openai

class ProofVerificationAPI(QObject):
    proof_result = pyqtSignal(bool, str, str)

    def __init__(self):
        super().__init__()
        self.openai_api_key = "your-openai-api-key-here"
        openai.api_key = self.openai_api_key

    @pyqtSlot(str)
    def generate_and_verify_proof(self, statement):
        proof = self.generate_proof_with_chatgpt(statement)
        is_valid, feedback = self.verify_with_agda(proof)
        while not is_valid:
            proof = self.refine_proof_with_chatgpt(statement, proof, feedback)
            is_valid, feedback = self.verify_with_agda(proof)
        self.proof_result.emit(is_valid, proof, feedback)

    def generate_proof_with_chatgpt(self, statement):
        prompt = f"Generate a formal proof in Agda for the following statement: '{statement}'"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a mathematical proof generator. Provide proofs in Agda syntax."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def verify_with_agda(self, proof):
        # Write proof to a temporary file
        with open("temp_proof.agda", "w") as f:
            f.write(proof)
        # Run Agda type-checker
        result = subprocess.run(["agda", "temp_proof.agda"], capture_output=True, text=True)
        is_valid = result.returncode == 0
        feedback = result.stdout if is_valid else result.stderr
        return is_valid, feedback

    def refine_proof_with_chatgpt(self, statement, previous_proof, feedback):
        prompt = f"Refine the following Agda proof for the statement: '{statement}'\n\nPrevious proof:\n{previous_proof}\n\nAgda feedback:\n{feedback}\n\nProvide an improved Agda proof."
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system",
                 "content": "You are a mathematical proof refiner. Improve Agda proofs based on compiler feedback."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
