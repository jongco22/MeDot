# embed_store.py
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import SentenceTransformerEmbeddings 
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

# json 로딩
with open("amc_health_info_all_categories_rag_data.json", "r", encoding="utf-8") as f:
    raw_data = json.load(f)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=700, # 각 청크의 최대 크기
    chunk_overlap=70, # 청크 간의 겹치는 부분
    length_function=len, # 청크의 길이를 계산하는 함수
    is_separator_regex=False # 구분자가 정규 표현식이 아닌 경우
)

all_chunked_documents = [] # 청킹된 모든 문서를 담을 리스트
for item in raw_data:
    # 각 항목에서 content와 metadata 추출
    content = item.get("content", "")
    metadata_original = item.get("metadata", {}) 

    chunks = text_splitter.split_text(content)
    for i, chunk_content in enumerate(chunks):
        # 각 청크에 대한 Document 객체 생성
        # 메타데이터에 청크 정보 추가 기능
        chunk_metadata = metadata_original.copy() # 원본 메타데이터를 복사하여 수정
        chunk_metadata["chunk_index"] = i
        
        all_chunked_documents.append(Document(page_content=chunk_content, metadata=chunk_metadata)) 

# 임베딩 + 벡터 저장
embedding_model = SentenceTransformerEmbeddings(model_name="jhgan/ko-sbert-nli") # 한국어 최적화 모델

db = FAISS.from_documents(all_chunked_documents, embedding_model) 

# 로컬에 저장 (파일명 변경 권장)
db_path = "faiss_amc_db_chunked" # 새로운 DB 경로/이름
db.save_local(db_path) 

print(f"FAISS 벡터 DB (청크됨) 저장 완료: {db_path}")
print(f"Total chunked documents created: {len(all_chunked_documents)}") # 생성된 총 청크 수 확인