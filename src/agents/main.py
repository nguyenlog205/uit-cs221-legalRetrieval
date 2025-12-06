import asyncio
import sys

from intention_classifier import IntentionClassifier
from src.agents.database_manager import DatabaseManager
from src.agents.general_generator import GeneralGenerator
from src.agents.specialized_generator import SpecificGenerator
from src.utils import load_configs

class MultiAgentRAG:
    def __init__(
        self,
        config_path: str
    ):
        self.config = load_configs(config_path)
        
        print("==============================================================")
        print("            MULTI-AGENT RAG SYSTEM INITIALIZATION             ")
        print("==============================================================")
        print(">> [1/4] Waking up Intention Classifier...")
        self.intention_classifier = IntentionClassifier(
            model_id=self.config.get("classifier_model", "gemini-2.0-flash-exp")
        )
        
        print(">> [2/4] Connecting to Database Manager...")
        self.database_manager = DatabaseManager(
            config=self.config.get("database", {})
        )
        
        print(">> [3/4] Preparing General Conversation Agent...")
        self.general_generator = GeneralGenerator(
            model_id=self.config.get("general_model", "gemini-2.0-flash-exp")
        )
        
        print(">> [4/4] Preparing Specialized Public Health Agent...")
        self.specialized_generator = SpecificGenerator(
            model_id=self.config.get("specific_model", "gemini-1.5-pro") 
        )
        
        print(">> System Ready.\n")

    async def process_query(self, user_input: str) -> str:
        """
        The core pipeline: Input -> Classify -> (Retrieve) -> Generate -> Output
        """
        intent = await self.intention_classifier.classify(user_input)
        print(f"   [Router] Identified Intent: {intent.upper()}")

        if intent == "general":
            # Path A: General Chat (No DB)
            print("   [Flow] Routing to General Generator...")
            response = await self.general_generator.generate(user_input)
            return response

        elif intent == "specific":
            # Path B: RAG Workflow (DB + Specific Agent)
            print("   [Flow] Routing to Specialized Pipeline...")
            
            # 1. Retrieve Context
            print("   [Database] Searching for documents...")
            context_docs = await self.database_manager.search(query=user_input)
            
            if not context_docs:
                print("   [Warning] No relevant documents found in DB.")
                # Optional: Fallback logic or proceed with empty context
            
            # 2. Generate Answer with Context
            print("   [Agent] Synthesizing answer...")
            response = await self.specialized_generator.generate(
                query=user_input, 
                context=context_docs
            )
            return response
        
        else:
            return "Error: Unknown intent classification."

    async def start_interactive_session(self):
        """
        Runs the loop until the user interrupts (Ctrl+C) or types exit.
        """
        print("--- SESSION STARTED (Type 'exit' to quit) ---")
        
        while True:
            try:
                # Get input (using executor for non-blocking input in async loop)
                user_input = await asyncio.to_thread(input, "\nUser: ")
                
                if user_input.lower() in ["exit", "quit", "bye"]:
                    print(">> Shutting down system. Goodbye!")
                    break
                
                if not user_input.strip():
                    continue

                # Run the pipeline
                final_response = await self.process_query(user_input)
                
                print(f"\nBot: {final_response}")
                print("-" * 60)

            except KeyboardInterrupt:
                print("\n>> Force shutdown detected. Exiting...")
                sys.exit(0)
            except Exception as e:
                print(f">> System Error: {e}")

# --- Execution Entry Point ---
if __name__ == "__main__":
    # Create system
    rag_system = MultiAgentRAG(config_path="config.yaml")
    
    # Run the async loop
    asyncio.run(rag_system.start_interactive_session())