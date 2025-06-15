# MeDot
## 의학 전문 챗봇 웹
## directory
```
📦medot
 ┣ 📂backend
 ┣ 📂frontend
 ┣ 📜.env
 ┣ 📜.gitignore
 ┗ 📜README.md
```
## Pipeline
```
[ 사용자 ]
|
▼
[ UI: 텍스트 또는 녹음본 입력 ]
|
▼
┌─< 입력 유형 판별 >───────────────┐
|                                |
▼                                ▼
[ 텍스트일 경우 ]                  [ 녹음본일 경우 ]
|                                |
▼                                ▼
[ LangGraph DB 검색 ]            [ Whisper: 음성을 텍스트로 변환 ]
|                                |
▼                                ▼
< 관련 정보가 있는가? >            [ GPT: 변환된 텍스트 요약 ]
|         |                      |
| (예)    | (아니오)               |
▼         ▼                      |
[DB 정보로 답변] [GPT로 답변 생성]        |
|         |                      |
|         └─────────┐  ┌─────────┘
|                   |  |
└────────►[ 최종 답변 ]◄────────┘
|
▼
[ UI에 결과 표시 ]
|
▼
[ 사용자 ]
```
## local 실행(개발)
### Backend 실행 (FastAPI + LangGraph)
📦의존 패키지 설치
```
cd backend
pip install -r requirements.txt
```
🚀FastAPI 실행
```
uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 `http://localhost:8000`에서 API열림
### Frontend 실행 (React + Vite)
📦 의존 패키지 설치
```
cd frontend
npm install
```
🚀 프론트엔드 실행
```
npm run dev
```
`http://localhost:5173`에서 UI 실행
### frontend 화면
<img width="1280" alt="Image" src="https://github.com/user-attachments/assets/29cc2f85-1ace-4fce-8a24-fd7ed3709452" />
#### api키는 .env파일에 작성
OPENAI_API_KEY="YOUR-API-KEY"


