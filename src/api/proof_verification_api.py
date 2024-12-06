import subprocess
import openai
from utils import common
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class ProofVerificationAPI(QObject):
    """
    The ProofVerificationAPI class is responsible for generating and verifying
    mathematical proofs using OpenAI's ChatGPT and Agda.
    """
    proof_result = pyqtSignal(bool, str, str)

    def __init__(self):
        super().__init__()
        ###################
        # INSERT KEY HERE #
        ###################
        self.openai_api_key = ""
        openai.api_key = self.openai_api_key

    @pyqtSlot(str)
    def generate_and_verify_proof(self, statement):
        """
        Generates a proof for the given mathematical statement and verifies it using Agda.
        If the proof is invalid, it refines the proof iteratively until a valid one is found.
        """
        proof = self.generate_proof_with_chatgpt(statement)
        is_valid, feedback = self.verify_with_agda(proof)
        while not is_valid:
            proof = self.refine_proof_with_chatgpt(statement, proof, feedback)
            is_valid, feedback = self.verify_with_agda(proof)
        self.proof_result.emit(is_valid, proof, feedback)

    def generate_proof_with_chatgpt(self, statement):
        """
        Generates a formal proof in Agda using ChatGPT for the given statement.
        """
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
        """
        Verifies the given Agda proof using the Agda type-checker.
         """
        # Write proof to a temporary file
        with open("temp_proof.agda", "w") as f:
            f.write(proof)
        # Run Agda type-checker
        result = common.run_command(["agda", "temp_proof.agda"], True)
        is_valid = result.returncode == 0
        feedback = result.stdout if is_valid else result.stderr
        return is_valid, feedback

    def refine_proof_with_chatgpt(self, statement, previous_proof, feedback):
        """
        Refines the given Agda proof based on feedback using ChatGPT.
        """
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
