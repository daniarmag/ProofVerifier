import subprocess
import openai
import re
import logging
import unicodedata
import codecs
import os
from utils import common
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from api.proof_worker import ProofWorker
logging.basicConfig(
    filename=os.path.join(common.get_proof_verifier_directory(), 'ProofVerifier.log'),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s')

class ProofVerificationAPI(QObject):
    """
    The ProofVerificationAPI class is responsible for generating and verifying mathematical proofs using OpenAI's ChatGPT and Agda.
    """
    proof_result = pyqtSignal(bool, str, str)
    progress_update = pyqtSignal(str)
    update_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.thread, self.worker = None, None
        self.proofs = set()
        self.statement = ""

    @pyqtSlot(str)
    def generate_and_verify_proof(self, statement):
        """
        Initiates the proof generation and verification process.
        Args:
            statement (str): The mathematical statement to be verified.
        """
        self.statement = statement
        if self.thread:
            if self.thread.isRunning():
                self.progress_update.emit("A proof generation process is already running.")
                return
            self.cleanup_thread()
        self.initialize_worker(statement)
        self.thread.start()

    def pause_proof(self):
        """Pauses the proof verification process."""
        if self.worker:
            self.worker.pause()

    def stop_proof(self):
        """Stops the proof verification process."""
        if self.worker:
            self.worker.stop()

    def resume_proof(self):
        """Resumes the proof verification process if paused."""
        if self.worker:
            self.worker.resume()
        else:
            self.generate_and_verify_proof(self.worker.statement)

    def initialize_worker(self, statement):
        """Initializes the worker and thread for proof verification.
        Args:
            statement (str): The mathematical statement to be verified.
        """
        self.thread = QThread()
        self.worker = ProofWorker(self, statement)
        self.worker.moveToThread(self.thread)

        # Connect signals
        self.thread.started.connect(self.worker.run)
        self.worker.proof_result.connect(self.handle_proof_completion)
        self.worker.progress_update.connect(self.progress_update.emit)
        self.worker.status_update.connect(self.update_status)

        # Thread and worker cleanup
        self.worker.proof_result.connect(self.thread.quit)
        self.worker.proof_result.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

    def cleanup_thread(self):
        """Cleans up the thread and worker resources."""
        if self.thread:
            try:
                self.thread.quit()
                self.thread.wait()
                self.thread.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.proofs = set()
                self.thread = None
                self.worker = None

    def handle_proof_completion(self, is_valid, proof, feedback):
        """
        Handles completion of the proof verification process.
        :param is_valid: bool True = Valid | False = Invalid
        :param proof: proof to display
        :param feedback: feedback to display
        """
        self.proof_result.emit(is_valid, proof, feedback)
        finished_statements = ["has been stopped"]
        if is_valid or (self.worker and self.worker.refinements == common.get_iterations_limit()) or any(s for s in finished_statements if s in feedback.lower()):
            self.cleanup_thread()

    def verify_with_agda(self, proof):
        """
        Verifies the given Agda proof using the Agda type-checker.
        :param proof: api proof that needs agda verification.
        """
        try:
            proof = self.check_if_proof_exists(ProofVerificationAPI.clean_agda_code(proof))
            if proof in self.proofs:
                # If still repeated after 5 attempts, emit a failure message.
                return False, "Failed to refine proof, refining proof and retrying..", proof
            self.proofs.add(proof)
            temp_filename = os.path.join(os.path.abspath("."), "temp_proof.agda")
            # Write proof to a temporary file
            with codecs.open(temp_filename, "w", encoding='utf-8') as f:
                f.write(proof)
            # Run Agda type-checker
            exit_code, feedback = common.run_command(f'agda --transliterate --compile-dir="{os.path.abspath(".")}" "{temp_filename}"', True)
            feedback = ProofVerificationAPI.categorize_feedback(feedback)
            is_valid = (exit_code == 0)
            # Extra layer of validation
            if is_valid:
                logging.debug("Validation of verify_with_agda")
                api_validation = self.validate_with_api(proof, self.statement)
                if "yes" not in api_validation.lower():
                    is_valid = False
                    feedback += "\nVerification failed: The statement was not confirmed as valid by the API."
            return is_valid, feedback, proof
        except Exception as e:
            logging.debug(f"Verification failed with error: {e}")
            return False, f"Error during verification: {e}", proof

    def check_if_proof_exists(self, proof):
        """
        :param: newly generated proof
        :return: after loop fix mechanism.
        """
        for attempt in range(common.get_max_api_loop_checker()):
            if proof in self.proofs:
                # Conditional inclusion of proof in feedback
                feedback = f"This proof has already been attempted, retrying..."
                self.progress_update.emit(feedback)
                proof = self.refine_proof_with_chatgpt(self.statement, proof, feedback)
                proof = self.clean_agda_code(proof)
            else:
                break
        return proof

    @staticmethod
    def categorize_feedback(feedback):
        """
        :param feedback: feedback from agda compiler.
        :return: specific feedback.
        """
        if "syntax error" in feedback.lower():
            return f"Syntax Error: {feedback}"
        elif "type mismatch" in feedback.lower():
            return f"Type Mismatch: {feedback}"
        elif "not in scope" in feedback.lower():
            return f"Not in scope error: {feedback}"
        return feedback

    @staticmethod
    def check_and_feedback_for_imports(proof):
        """
        Checks if the proof contains 'open import' statements and generates feedback for refinement.
        :param proof: the proof that we're checking for imports
        """
        if re.search(r"\bopen import\b", proof):
            return (
                "The proof includes 'open import' statements, which violates the requirement to avoid using libraries. "
                "Remove all 'open import' statements and replace them with fully implemented definitions within the module."
            )
        return ""

    @staticmethod
    def clean_agda_code(raw_code):
        """
        Cleans the Agda code generated by ChatGPT by removing:
        - Markdown code block formatting (backticks)
        - Any module declaration
        - Comments (starting with '--')
        - Characters not supported by UTF-8

        :param raw_code: code before cleaning
        """
        if not raw_code:
            return ""
        clean_code = unicodedata.normalize("NFC", raw_code)
        clean_code = clean_code.replace("```agda", "").replace("```", "").strip()
        clean_code = clean_code.replace('\r\n', '\n')
        return clean_code

    def generate_proof_with_chatgpt(self, statement):
        """
        Generates a formal proof in Agda using ChatGPT for the given statement.
        :param statement: original statement for verification
        """
        prompt = (
            f"You are an expert in Agda programming. Your task is to generate a formal proof "
            f"in Agda for the following mathematical statement: '{statement}'.\n"
            f"### Example correct agda code :\n"
            f"```\n{ProofVerificationAPI.get_agda_example()}\n```\n"
            f"Requirements:\n"
            f"- The output must be a complete Agda module named 'temp_proof'.\n"
            f"- Do NOT use any libraries or infixl, not even the Agda standard library. "
            f"All definitions (e.g., natural numbers, basic functions) must be implemented from scratch.\n"
            f"- Output only valid Agda code, without any comments, explanations, or extra text."
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a mathematical proof generator. Provide proofs in Agda syntax."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during proof generation: {e}"

    def validate_with_api(self, proof, statement):
        """
        Sends the proof to the API for additional validation.
        :param proof: The Agda proof found valid.
        :param statement: The mathematical statement being verified.
        :return: "yes" or "no" based on API response.
        """
        prompt = (
            f"You are an expert in Agda programming."
            f"Please answer with 'yes' or 'no' only."
            f"Does the following proof correctly verify the statement: '{statement}'?\n\n"
            f"Proof:\n"
            f"```\n{proof}\n```\n"
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a mathematical proof generator. Provide proofs in Agda syntax."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=3,
                temperature=0
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during correct proof validation: {e}"

    def refine_proof_with_chatgpt(self, statement, previous_proof, feedback):
        """
        Refines the given Agda proof based on feedback using ChatGPT.
        :param statement: original statement.
        :param previous_proof: proof that needs refining.
        :param feedback: current compiler feedback / processing feedback.
        """
        # Check whether there were imports in previous proof.
        import_feedback = ProofVerificationAPI.check_and_feedback_for_imports(previous_proof)
        additional_feedback = (
            f"### Additional Feedback:\n"
            f"{import_feedback}\n"
            if import_feedback else ""
        )
        # Prepare feedback.
        modified_feedback = (
            f"Feedback from the Agda compiler:\n"
            f"```\n{feedback}\n```\n"
        ) if feedback not in ["This proof has already been attempted"] else (
            f"Feedback from processing proof:\n"
            f"```\n{feedback}\n```\n"
        )
        prompt = (
            f"You are an expert in Agda programming. Your task is to refine the following Agda proof "
            f"based on the given feedback for the statement: '{statement}'.\n"
            f"### Example correct agda code :\n"
            f"```\n{ProofVerificationAPI.get_agda_example()}\n```\n"
            f"--- Start of Context ---\n"
            f"{additional_feedback}"
            f"### Previous Proof:\n"
            f"```\n{previous_proof}\n```\n"
            f"{modified_feedback}"
            f"--- End of Context ---\n"
            f"Requirements:\n"
            f"- Modify the proof based on the feedback to ensure it is valid and complete.\n"
            f"- The module name must remain 'temp_proof'.\n"
            f"- Do NOT use any libraries or infixl, not even the Agda standard library. "
            f"All definitions must be implemented from scratch.\n"
            f"- Output only valid Agda code, without any comments, explanations, or extra text."
        )
        try:
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a mathematical proof generator. Provide proofs in Agda syntax."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error during proof refinement: {e}"

    @staticmethod
    def get_agda_example():
        """ Provides an example to the API. """
        return """
            module temp_proof where
    
            data ℕ : Set where
              zero : ℕ
              succ : ℕ → ℕ
    
            add : ℕ → ℕ → ℕ
            add zero n = n
            add (succ m) n = succ (add m n)
    
            data _≡_ {A : Set} (x : A) : A → Set where
              refl : x ≡ x
            """
