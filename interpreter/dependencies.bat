@echo off
echo Installing required Python packages...
pip install chromadb sentence-transformers beautifulsoup4 PyMuPDF requests langchain langchain-community langchain-huggingface langchain-ollama chm
echo.
echo Done! You can now run the main assistant script.
pause
