# medot/main.py
from langgraph.graph import StateGraph, END
from nodes.medical_filter import medical_filter_node
from nodes.gpt_response_rag import gpt_response_node
from typing import TypedDict, Optional

class ChatState(TypedDict):
    user_input: str
    is_medical: Optional[bool]
    answer: Optional[str]



# 그래프 정의
builder = StateGraph(ChatState) 
builder.add_node("MedicalFilter", medical_filter_node)
builder.add_node("GPTResponse", gpt_response_node)

# 분기 처리
def condition_router(state):
    return "GPTResponse" if state["is_medical"] else END

builder.set_entry_point("MedicalFilter")
builder.add_conditional_edges("MedicalFilter", condition_router, {
    "GPTResponse": "GPTResponse",
    END: END
})
builder.add_edge("GPTResponse", END)

app = builder.compile()

# 실행
if __name__ == "__main__":
    while True:
        user_input = input("질문을 입력하세요: ")
        result = app.invoke({"user_input": user_input})
        print("결과:", result.get("answer", "의학 질문만 응답 가능합니다."))
