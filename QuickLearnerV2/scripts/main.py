# main.py
from quicklearner import QuickLearner

def display_response(response):
    """Formats and displays the response with clean formatting"""
    print("\n" + "="*60)  # Top border
    print("ANSWER:".center(60))
    print("="*60)
    
    # Print answer with proper indentation and line wrapping
    answer_lines = response["answer"].split('\n')
    for line in answer_lines:
        print(f"  {line}")
    
    print("\n" + "-"*60)
    print("SOURCES:".center(60))
    print("-"*60)
    
    # Deduplicate and format sources
    seen_sources = set()
    for src in response["sources"]:
        source_str = f"{src['source']} (page {src.get('page', 'N/A')})"
        if source_str not in seen_sources:
            print(f"  • {source_str}")
            seen_sources.add(source_str)

if __name__ == "__main__":

    # Debug first - show document structure
    from pathlib import Path
    from document_processor import load_documents

    document_directory = "../documents"
    doc_path = Path(document_directory)
    if not doc_path.is_absolute():
        doc_path = Path(__file__).parent / document_directory

    print("\n⏳ Loading documents...")
    all_docs = load_documents(str(doc_path))
    print(f"✅ Loaded {len(all_docs)} pages total")
    
    # Substitua o bloco de debug por isto:
    print("\n🔍 Analisando estrutura do documento:")

    # 1. Mostra estatísticas básicas
    total_chars = sum(len(d.page_content) for d in all_docs)
    print(f"Total de páginas: {len(all_docs)}")
    print(f"Total de caracteres: {total_chars}")
    print(f"Média por página: {total_chars//len(all_docs)} chars")

    # 2. Identifica páginas com conteúdo real (método universal)
    def is_content_page(text):
        text = text.lower().strip()
        return (
            len(text) > 300  # Páginas com menos de 300 chars são provavelmente capas/sumários
            and not text.startswith("prefácio")
            and not text.startswith("sumário")
            and "..." not in text  # Elimina páginas com muitos ... (indicando formatação quebrada)
        )

    technical_pages = [doc for doc in all_docs if is_content_page(doc.page_content)]

    # 3. Mostra amostras inteligentes
    print(f"\n📊 Páginas técnicas identificadas: {len(technical_pages)}/{len(all_docs)}")
    for i, page in enumerate(technical_pages[:3]):  # Mostra até 3 páginas de exemplo
        content_sample = ' '.join(page.page_content.split()[:30])  # Primeiras 30 palavras
        print(f"\n📄 Página {page.metadata.get('page', '?')+1}:")
        print(f"{content_sample}...")

    if not technical_pages:
        print("\n⚠️ ATENÇÃO: Nenhuma página com conteúdo substancial foi detectada!")
        print("Prováveis causas:")
        print("- O documento pode estar em formato de imagem (OCR necessário)")
        print("- O texto pode estar em camadas não extraíveis")
        print("- O arquivo pode estar corrompido")
        
        # Debug avançado - mostra padrões encontrados
        print("\n🧐 Padrões encontrados nas primeiras páginas:")
        for i, doc in enumerate(all_docs[:3]):
            print(f"\nPágina {i+1} (Meta: {doc.metadata}):")
            print(doc.page_content[:100].replace('\n', ' ') + "...")
        
    # Now run normally
    print("\n🚀 Starting QuickLearner...")

    # Initialize with your documents directory
    quick_learner = QuickLearner("../documents")

    '''
    ql = QuickLearner("../documents")
    response = ql.query("Detalhe o procedimento completo para juntas de movimentação")
    print(response["answer"])
    '''
    
    # Query the system
    while True:
        question = input("\nAsk QuickLearner a question (or 'quit' to exit): ")
        if question.lower() == 'quit':
            break
        
        response = quick_learner.query(question)
        display_response(response)  # Use the new display function