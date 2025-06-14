# gpt_response_rag.py
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA # RAG 체인을 만들기 위한 클래스
from langchain_core.messages import SystemMessage, HumanMessage # LLM에 전달할 메시지 타입
from langchain.prompts import PromptTemplate # LLM 프롬프트를 구조화하기 위한 클래스

# DB 불러오기
embedding_model = SentenceTransformerEmbeddings(model_name="jhgan/ko-sbert-nli")
db = FAISS.load_local("faiss_amc_db_chunked", embedding_model, allow_dangerous_deserialization=True)

retriever = db.as_retriever(search_type="similarity", k=3)
llm = ChatOpenAI(model="gpt-4", temperature=0.7)


prompt_template_str =  """당신은 친절하고 지식이 풍부한 의료 도우미입니다. 사용자 질문에 답변하기 위해 다음의 참고 정보를 활용하세요.

참고 정보:
{context}

만약 참고 정보에서 직접적인 답변을 찾기 어렵다면, 당신의 일반적인 의학 지식을 바탕으로 사용자에게 도움이 될 수 있는 가능한 원인, 증상 완화 방법, 또는 의학적 조언을 제공해주세요. 하지만 확정적인 진단은 내릴 수 없음을 명확히 하고, 필요한 경우 전문가와 상담할 것을 권유하세요. 사용자의 증상을 잘 이해하고 공감하는 태도를 보여주세요.

질문: {question}
답변:"""

RAG_PROMPT = PromptTemplate(
    template=prompt_template_str, input_variables=["context", "question"]
)

# RetrievalQA가 내부적으로 retriever 사용
rag_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type="stuff", # 검색된 모든 문서를 하나의 프롬프트에 넣어 처리
    return_source_documents=True,
    chain_type_kwargs={"prompt": RAG_PROMPT}
)

def gpt_response_node(state):
    user_input = state["user_input"]

    # rag체인 실행
    rag_result = rag_chain.invoke({"query": user_input})
    answer_from_rag = rag_result['result']
    source_documents_found = rag_result.get("source_documents", []) # 없으면 빈 리스트트

    # rag 결과 및 fallback 로직 결정
    if source_documents_found:
        # print(f'RAG 응답 (문서 {len(source_documents_found)}개 참고): {answer_from_rag}') # 디버그용
        final_answer = answer_from_rag
    else: 
        print("RAG에서 관련 문서를 찾지 못했습니다. LLM을 직접 사용합니다.")
        messages = [
            SystemMessage(content="당신은 친절하고 지식이 풍부한 의료 도우미입니다. 사용자의 질문에 대해 당신의 일반적인 의학 지식을 바탕으로 답변해주세요. 하지만 확정적인 진단은 내릴 수 없음을 명확히 하고, 필요한 경우 전문가와 상담할 것을 권유하세요."),
            HumanMessage(content=user_input)
        ]
        final_answer = llm.invoke(messages).content
        # print("LLM 응답:", final_answer) # 디버그용
    return {**state, "answer": final_answer}