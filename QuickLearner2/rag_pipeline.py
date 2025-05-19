from langchain.chains import RetrievalQA

def create_rag_pipeline(llm, vector_store):
    # Create the full RAG pipeline
    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(),
        return_source_documents=True
    )