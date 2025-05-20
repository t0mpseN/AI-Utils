# rag_pipeline.py
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

def create_rag_pipeline(llm, vector_store):
    # Portuguese-optimized prompt
    prompt_template = """[INST] <<SYS>>
    Você é um assistente técnico. Analise ESTE documento completo:

    {context}

    Responda de forma:
    - Técnica e detalhada
    - Com parágrafos claros
    - Citando páginas quando relevante
    <</SYS>>

    Pergunta: {question} [/INST]"""

    # Create the prompt with correct variable names
    QA_PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 6,
                "fetch_k": 20
            }
        ),
        chain_type_kwargs={
            "prompt": QA_PROMPT,
            "document_variable_name": "context"  # Explicitly set the variable name
        },
        return_source_documents=True
    )