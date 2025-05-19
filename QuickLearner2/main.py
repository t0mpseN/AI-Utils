# main.py
from quicklearner import QuickLearner

if __name__ == "__main__":
    # Initialize with your documents directory
    quick_learner = QuickLearner("documents")
    
    # Query the system
    while True:
        question = input("Ask QuickLearner a question (or 'quit' to exit): ")
        if question.lower() == 'quit':
            break
        
        response = quick_learner.query(question)
        print("\nAnswer:", response["answer"])
        print("\nSources:")
        for source in response["sources"]:
            print(f"- {source['source']} (page {source.get('page', 'N/A')})")
        print()