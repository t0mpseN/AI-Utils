import os
import json
from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, messages_from_dict, messages_to_dict

class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, storage_path: str, session_id: str):
        self.file_path = os.path.join(storage_path, f"{session_id}.json")
        os.makedirs(storage_path, exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def get_messages(self) -> List[BaseMessage]:
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            messages = messages_from_dict(data)
            print("DEBUG: get_messages returned:", messages)
            return messages

    def add_message(self, message: BaseMessage) -> None:
        messages = self.get_messages()
        messages.append(message)
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump(messages_to_dict(messages), f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        with open(self.file_path, 'w', encoding='utf-8') as f:
            json.dump([], f)
