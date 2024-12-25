import subprocess
import openai
import re
import logging
from utils import common
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from api.proof_worker import ProofWorker

class ProofVerificationAPI(QObject):
    """
    The ProofVerificationAPI class is responsible for generating and verifying
    mathematical proofs using OpenAI's ChatGPT and Agda.
    """
    proof_result = pyqtSignal(bool, str, str)
    progress_update = pyqtSignal(str)
    update_status = pyqtSignal(str)
    run_paused = pyqtSignal()
    run_stopped = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.thread, self.worker = None, None
        self.is_cleaned_up = False



    @pyqtSlot(str)
    def generate_and_verify_proof(self, statement):
        """
        Generates a proof for the given mathematical statement and verifies it using Agda.
        If the proof is invalid, it refines the proof iteratively until a valid one is found.
        """
        if self.thread:
            if self.thread.isRunning():
                self.progress_update.emit("A proof generation process is already running.")
                return

            self.cleanup_thread()
        self.is_cleaned_up = False

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

        self.thread.start()

    def handle_proof_completion(self, is_valid, proof, feedback):
        self.proof_result.emit(is_valid, proof, feedback)
        finished_statements = ["has been stopped"]
        if is_valid or (self.worker and self.worker.refinements == common.get_iterations_limit()) or any(s for s in finished_statements if s in feedback.lower()):
            self.cleanup_thread()

    def cleanup_thread(self):
        if self.thread:
            try:
                self.thread.quit()
                self.thread.wait()
                self.thread.deleteLater()
            except RuntimeError:
                pass
            finally:
                self.thread = None
                self.worker = None
        self.is_cleaned_up = True

    def pause_proof(self):
        if self.worker:
            self.worker.pause()

    def stop_proof(self):
        if self.worker:
            self.worker.stop()

    def resume_proof(self):
        if self.worker:
            self.worker.resume()
        else:
            self.generate_and_verify_proof(self.worker.statement)

    def generate_proof_with_chatgpt(self, statement):
        """
        Generates a formal proof in Agda using ChatGPT for the given statement.
        """
        prompt = (
            f"You are an expert in Agda programming. Your task is to generate a formal proof "
            f"in Agda for the following mathematical statement: '{statement}'.\n"
            f"Requirements:\n"
            f"- The output must be a complete Agda module named 'temp_proof'.\n"
            f"- Do NOT use any libraries, not even the Agda standard library. "
            f"All definitions (e.g., natural numbers, basic functions) must be implemented from scratch.\n"
            f"- Output only valid Agda code, without any comments, explanations, or extra text."
        )
        response = openai.chat.completions.create(
            model="gpt-4o",
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
        proof = self.clean_agda_code(proof)
        # Write proof to a temporary file
        with open("temp_proof.agda", "w", encoding='utf-8') as f:
            f.write(proof)
        # Run Agda type-checker
        exit_code, feedback = common.run_command("agda --transliterate temp_proof.agda", True)
        is_valid = (exit_code == 0)
        return is_valid, feedback, proof

    def refine_proof_with_chatgpt(self, statement, previous_proof, feedback):
        """
        Refines the given Agda proof based on feedback using ChatGPT.
        """
        prompt = (
            f"You are an expert in Agda programming. Your task is to refine the following Agda proof "
            f"for the statement: '{statement}'.\n"
            f"Provided proof:\n"
            f"```\n{previous_proof}\n```\n"
            f"Feedback from the Agda compiler:\n"
            f"```\n{feedback + self.check_and_feedback_for_imports(previous_proof)}\n```\n"
            f"Requirements:\n"
            f"- Modify the proof based on the feedback to ensure it is valid and complete.\n"
            f"- The module name must remain 'temp_proof'.\n"
            f"- Do NOT use any libraries, not even the Agda standard library. "
            f"All definitions must be implemented from scratch.\n"
            f"- Output only valid Agda code, without any comments, explanations, or extra text."
        )
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a mathematical proof generator. Provide proofs in Agda syntax."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

    def check_and_feedback_for_imports(self, proof):
        """
        Checks if the proof contains 'open import' statements and generates feedback for refinement.
        """
        if re.search(r"\bopen import\b", proof):
            return (
                "The proof includes 'open import' statements, which violates the requirement to avoid using libraries. "
                "Remove all 'open import' statements and replace them with fully implemented definitions within the module."
            )
        return ""

    def clean_agda_code(self, raw_code):
        """
        Cleans the Agda code generated by ChatGPT by removing:
        - Markdown code block formatting (backticks)
        - Any module declaration
        - Comments (starting with '--')
        - Characters not supported by UTF-8
        """
        clean_code = raw_code.replace("```agda", "").replace("```", "").strip()
        clean_code = re.sub(r'.*(?=data|module)', '', clean_code, flags=re.DOTALL).strip()
        clean_code = re.sub(r'--.*\n', '', clean_code)
        clean_code = clean_code.encode("utf-8", "ignore").decode("utf-8")
        return clean_code
