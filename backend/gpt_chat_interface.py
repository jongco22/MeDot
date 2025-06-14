# gpt_chat_interface.py
from main import app

def chat_with_rag(user_input: str) -> str:
    result = app.invoke({"user_input": user_input})
    return result.get("answer", "의학 질문만 응답 가능합니다.")
