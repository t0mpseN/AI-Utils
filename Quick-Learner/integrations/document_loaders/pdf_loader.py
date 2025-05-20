from langchain_community.document_loaders import PyPDFLoader
from langchain_core.vectorstores import InMemoryVectorStore
from ..model_loaders.simple_interpreter import load_embedding_model

def PDFLoader(file_path):
    loader = PyPDFLoader(file_path)
    pages = []

    for page in loader.lazy_load():
        pages.append(page)

    embed = load_embedding_model()
    vector_store = InMemoryVectorStore.from_documents(pages, embed)

    question = input("Ask a question about the PDF: ")

    docs = vector_store.similarity_search(question, k=2)
    for doc in docs:
        print(f'Page {doc.metadata["page"]}: {doc.page_content[:-1]}\n')