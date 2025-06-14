# summarize_audio.py
# whisper 테스트용
# 전체 파이프라인에서는 사용되지 않음.
import whisper
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

# 1. Whisper로 음성 파일 STT
def transcribe_audio(file_path):
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result["text"]

# 2. GPT로 요약
def summarize_text(transcript):
    messages = [
        {"role": "system", "content": (
                "You are a kind and knowledgeable assistant who summarizes doctor-patient consultations. "
                "Your goal is to explain the important points in a way that a person without medical knowledge can understand. "
                "Focus on clearly summarizing the health concerns and medical advice from the consultation in simple, non-technical language. "
                "Avoid using medical jargon. Be concise, friendly, and easy to understand."
            )},
        {"role": "user", "content": (
            "다음은 의사와 환자의 상담 녹음입니다. 의학 지식이 없는 사람이 자신의 건강 상태를 쉽게 이해할 수 있도록, 중요한 증상, 진단, 처방 또는 의사의 조언을 간단하고 명확하게 요약해주세요. 요약 언어는 녹음본과 동일한 언어를 사용하세요.:\n\n" + transcript
        )}
    ]
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    file_path = "consultation.mp3" 
    print("🎙️ 음성 인식 중...")
    transcript = transcribe_audio(file_path)
    print("📝 요약 중...")
    summary = summarize_text(transcript)
    print("✅ 요약 결과:")
    print(summary)
