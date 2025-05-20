from langchain_ollama import OllamaLLM

def setup_llm(model_name):
    return OllamaLLM(
        model=model_name,
        temperature=0.7,
        num_ctx=4096,
        top_p=0.9,
        template="""[INST] <<SYS>>
        You are QuickLearner, a Brazilian technical documentation expert.
        Respond in the same language as the question.
        Provide specific excerpts from documents when available.
        <</SYS>>
        
        {context}
        {question} [/INST]""",
        format="",
        stop=["\n\n"],
        system=(
            "Você é um engenheiro civil especializado em normas ABNT. "
            "Sua função é extrair informações EXATAS dos documentos técnicos. "
            "Quando não houver detalhes completos, explique o que deveria constar "
            "segundo as boas práticas."
        )
    )