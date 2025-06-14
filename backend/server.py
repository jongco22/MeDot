# backend/server.py

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from main import app as langgraph_app
import whisper
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

app = FastAPI()

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message", "")
    result = langgraph_app.invoke({"user_input": user_input})
    return {"answer": result.get("answer", "의학 질문만 응답 가능합니다.")}

@app.post("/summarize-audio")
async def summarize_audio(file: UploadFile = File(...)):
    # 1. 업로드된 파일 저장
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # 2. Whisper로 텍스트 변환
    model = whisper.load_model("base")
    result = model.transcribe(temp_path)
    transcript = result["text"]

    # 3. GPT로 요약
    messages = [
        {
            "role": "system",
            "content": "You are a kind and knowledgeable assistant who summarizes doctor-patient consultations. "
                "Your goal is to explain the important points in a way that a person without medical knowledge can understand. "
                "Focus on clearly summarizing the health concerns and medical advice from the consultation in simple, non-technical language. "
                "Avoid using medical jargon. Be concise, friendly, and easy to understand."
        },
        {
            "role": "user",
            "content": f"다음은 의사와 환자의 상담 녹음입니다. 의학 지식이 없는 사람이 자신의 건강 상태를 쉽게 이해할 수 있도록, 중요한 증상, 진단, 처방 또는 의사의 조언을 간단하고 명확하게 요약해주세요. 요약 언어는 녹음본과 동일한 언어를 사용하세요.\n\n{transcript}"
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
    )

    # 4. 임시 파일 삭제
    os.remove(temp_path)

    return {"summary": response.choices[0].message.content}
