# medical_filter.py
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4", temperature=0)

def medical_filter_node(state):
    user_input = state["user_input"]
    messages = [
        SystemMessage(content=(
            "You are a medical filter. "
            "You will be given a user question, possibly in Korean or English. "
            "Reply with 'yes' if the question is about health, medicine, or the human body. "
            "Reply with 'no' otherwise. Only reply with 'yes' or 'no'."
        )),
        HumanMessage(content=f"{user_input}")
    ]
    response = llm.invoke(messages)
    result = response.content.strip().lower()
    print("판단된 응답:", result) 
    is_medical = result.startswith("yes")
    return {**state, "is_medical": is_medical}
