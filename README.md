**Project Status: WIP**

--------------------------------------------------------------------------------------------------

**Abstract**

Recent advancements in artificial intelligence, particularly large language models (LLMs) such as ChatGPT, have demonstrated their capacity to generate mathematical proofs with remarkable skill. Nevertheless, ChatGPT is not yet capable of verifying the accuracy of its proofs, which presents a major obstacle to their integration into formal mathematical studies [2,5]. In order to solve this problem, this project aims to create an interactive proof verification system that makes use of the ideas behind Vladimir Voevodsky's Homotopy type theory [4] and Per Martin-Löf's intuitionistic type theory [3]. Our suggested method builds a framework in which the correctness of proofs produced by ChatGPT may be verified using a formal proof language, Agda [9]. The system features an API that lets ChatGPT and the formal proof environment interact, ensuring that proofs are both generated and validated. This integration aims to enhance the reliability of AI-assisted mathematical proofs, and by that accelerating mathematical research and improving the overall trustworthiness of AI-generated results.

**Our System's API**

Our system features an API designed to bridge the gap between natural language mathematical statements and formal verification processes. The API serves as an interface that allows interaction between AI-driven proof generation and formal verification methods, aiming to streamline the iterative process of proof generation and validation. It is structured to facilitate seamless communication between ChatGPT and the Agda-based formal verification system, ensuring that proofs are generated correctly.
The API accepts natural language input, translating it into a semi-formal proof structure that is subsequently validated by Agda. The system is designed for iterative refinement, where failed proofs are analyzed, and feedback is provided to the proof generation module, enabling continuous improvement until convergence is achieved. This architecture allows for efficient proof discovery and enhances the reliability of AI-generated mathematical proofs.
