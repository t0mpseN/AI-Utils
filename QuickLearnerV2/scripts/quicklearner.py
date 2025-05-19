# quicklearner.py
import re
from pathlib import Path
from document_processor import load_documents, split_documents
from vector_store import create_vector_store
from ollama_integration import setup_llm
from rag_pipeline import create_rag_pipeline
from conversation_manager import ConversationManager

class QuickLearner:
    def __init__(self, document_directory, model_name="steamdj/llama3.1-cpu-only:latest"):
        # Convert to absolute path
        doc_path = Path(document_directory)
        if not doc_path.is_absolute():
            doc_path = Path(__file__).parent / document_directory
        
        if not doc_path.exists():
            raise ValueError(f"Document directory not found at: {doc_path}")
        
        # Load and process documents
        documents = load_documents(str(doc_path))
        split_docs = split_documents(documents)
        
        # Create vector store
        self.vector_store = create_vector_store(split_docs)
        
        # Setup LLM and RAG pipeline
        self.llm = setup_llm(model_name)
        self.qa_pipeline = create_rag_pipeline(self.llm, self.vector_store)

        # Initialize conversation manager
        self.convo_manager = ConversationManager()
    
    def query(self, question):
        # Add user question to history
        self.convo_manager.add_message("user", question)
        
        # Get conversation context
        context = self.convo_manager.load_context()
        
        # Enhanced prompt with conversation history
        enhanced_prompt = f"""
        Conversation history:
        {self._format_history(context)}
        
        New question: {question}
        """

        # Get AI response
        result = self.qa_pipeline.invoke({"query": enhanced_prompt})

        # Add AI response to history
        self.convo_manager.add_message("assistant", result["result"])
        self.convo_manager.save_conversation()
            
        # Clean the AI response
        clean_answer = self._clean_response(result["result"])
        print(f"Answer CLEANED: {clean_answer}")
        
        answer = result["result"]
            
        # If response is too short but sources exist
        if len(result["result"].split()) < 15 and result["source_documents"]:
            # Attempt direct extraction
            context = "\n".join(doc.page_content for doc in result["source_documents"][:3])
            manual_prompt = f"""
            Extraia informações EXATAS desta norma técnica para responder:
            Pergunta: {question}
            
            Texto relevante:
            {context}
            
            Responda em bullet points com:
            - Parágrafos exatos entre aspas
            - Referências de página
            - Se ausente, declare claramente
            """
            
            detailed_response = self.llm.invoke(manual_prompt)
            return {
                "answer": detailed_response,
                "sources": result["source_documents"]
            }
        
        return {
            "answer": answer,
            "sources": [doc.metadata for doc in result["source_documents"]]
        }
        
    def _format_history(self, messages):
        return "\n".join(
            f"{msg['role']}: {msg['content']}" 
            for msg in messages
        )
    

    def _clean_response(self, text):
        """Ensures clean output even with template formatting"""
        # Remove any residual template artifacts
        text = text.replace('[INST]', '').replace('[/INST]', '')
        text = re.sub(r'<<SYS>>.*?<</SYS>>', '', text, flags=re.DOTALL)
        
        # Clean numbered lists
        text = re.sub(r'(\d+\.)\s+', r'\1 ', text)
        
        # Remove excessive whitespace
        return '\n'.join(line.strip() for line in text.split('\n') if line.strip())