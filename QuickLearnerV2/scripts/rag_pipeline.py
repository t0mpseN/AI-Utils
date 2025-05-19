#rag_pipeline.py
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate

def create_rag_pipeline(llm, vector_store):
    # Portuguese-optimized prompt
    prompt_template = """[INST] <<SYS>>
    Você é um engenheiro especialista em normas ABNT. Analise estes trechos técnicos:

    {context}

    Regras:
    1. Responda somente com o conteúdo EXATO dos documentos
    2. Se não encontrar, diga "Não localizado nos trechos fornecidos"
    3. Inclua sempre o número da página
    <</SYS>>

    Pergunta: {question} 
    [/INST]"""

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(
            search_type="mmr",  # Maximal Marginal Relevance
            search_kwargs={
                "k": 6,
                "fetch_k": 20  # Wider initial search
            }
        ),
        chain_type_kwargs={"prompt": PromptTemplate.from_template(prompt_template)},
        return_source_documents=True
    )