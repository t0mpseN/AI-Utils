#conversation_manager.py
import json
from datetime import datetime
from pathlib import Path

class ConversationManager:
    def __init__(self, storage_path="conversations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True)
        self.current_conversation = []
        
    def add_message(self, role, content):
        # Clean content before storing
        content = content.replace('\n', ' ').strip()
        timestamp = datetime.now().isoformat()
        message = {"role": role, "content": content, "timestamp": timestamp}
        self.current_conversation.append(message)
        
    def save_conversation(self):
        if not self.current_conversation:
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.storage_path / f"convo_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.current_conversation, f, indent=2)
            
    def load_context(self, max_messages=5):
        """Returns last N messages as context"""
        return self.current_conversation[-max_messages:]