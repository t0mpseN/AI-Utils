from ..document_loaders import pdf_loader, chm_loader

def pick_assistant(file_type):
    if file_type == "pdf" or "txt":
        return pdf_loader.Assistant
    elif file_type == "chm":
        return chm_loader.Assistant
    elif file_type == "pdf_image":
        return ""
    else:
        return Exception("File Type not supported.")