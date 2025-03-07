from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import openai
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import base64
import re  # 정규 표현식

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화 (비동기)
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# CORS 설정
origins = ["*"]  # 모든 도메인 허용 (실제 배포 시에는 프론트엔드 도메인만!)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 요청 데이터 모델
class ChatRequest(BaseModel):
    user_message: str
    selected_doctor: str  # 의사 선택

# 의사 정보 (클라이언트와 동기화, 환영 메시지 추가)
doctors = {
    "doctor1": {
        "name": "Dr. Nova",
        "voice": "nova",
        "image": "doctor1.jpg",
        "greeting": "안녕하세요, 저는 AI 정신과 의사 Dr. Nova입니다. 저는 실제 의사는 아니며, 제가 제공하는 정보는 참고용일 뿐입니다. 정확한 진단과 치료는 반드시 전문의와 상담하세요. 어떤 점이 힘드신가요?",
    },
    "doctor2": {
        "name": "Dr. Shimmer",
        "voice": "shimmer",
        "image": "doctor2.jpg",
        "greeting": "안녕하세요, AI 정신과 의사 Dr. Shimmer입니다. 저는 실제 의사가 아니며, 제가 제공하는 정보는 참고용입니다. 정확한 진단과 치료는 전문의와 상담하세요. 어떤 점이 힘드신가요?",
    },
    "doctor3": {
        "name": "Dr. Fable",
        "voice": "fable",
        "image": "doctor3.jpg",
        "greeting": "안녕하세요, AI 정신과 의사 Dr. Fable입니다. 저는 실제 의사는 아니며, 제가 제공하는 정보는 참고용일 뿐입니다. 정확한 진단과 치료는 전문의와 상담하세요. 어떤 점이 힘드신가요?",
    },
}

# 초기 의사 설정
selected_doctor = "doctor1"

# 챗봇 응답 API
@app.post("/chat")
async def chat(request: ChatRequest):
    global selected_doctor
    selected_doctor = request.selected_doctor  # 의사 정보 업데이트

    try:
        messages = [
            {
                "role": "system",
                "content": f"""당신은 {doctors[selected_doctor]['name']}입니다. 당신은 정신과 의사입니다.  최대한 친절하고 자세하게 상담해주어야 합니다.
                다음은 명심해야 할 사항입니다.

                * 매우 상세하게 질문하고, 환자의 상태를 최대한 자세히 파악합니다.
                * 환자의 감정에 공감하고, 정서적으로 지지합니다.
                * 필요한 경우, 정신 건강 의학과 관련된 추가 정보를 제공합니다. (예: 특정 질환, 치료법, 약물)
                * 환자가 구체적인 약물이나 처방을 요구하는 경우, 관련된 정보를 제공하되, 반드시 면책 조항을 명시합니다.
                * 면책 조항: 저는 AI 챗봇이며, 실제 의사가 아닙니다. 제가 제공하는 정보는 참고용일 뿐이며, 의학적 진단이나 치료를 대체할 수 없습니다.  정확한 진단과 치료는 반드시 정신과 전문의와 상담하세요.
                * 자살, 자해, 타해 위험이 의심되는 경우, 즉시 전문가의 도움을 받도록 안내합니다.
                * 대화 내용을 바탕으로, DSM-5 (정신질환 진단 및 통계 편람 제5판) 기준에 따라 가능한 진단명을 *추정*하고, 그 근거를 설명합니다. (주의: 추정일 뿐, 확진이 아님)
                * 환자의 상태에 따라, 약물 치료가 필요하다고 *판단되는 경우*,  정신건강의학과에서 사용하는 약물 (예: SSRI, SNRI, 항정신병약물, 기분안정제, 항불안제 등)에 대한 정보를 제공하고, 각 약물의 일반적인 효과, 부작용, 주의사항 등을 설명합니다. (주의: 정보 제공일 뿐, 처방이 아님)
                * 약물 정보는 일반적인 내용이며, 환자 개개인에 따라 다를 수 있음을 명시합니다.
                * 대화 마지막에, 면책 조항을 다시 한번 강조합니다.
                * 대화는 항상 희망적이고 긍정적인 메시지로 마무리합니다.
                * 질문은 한번에 하나만 합니다.
                """,
            },
            {"role": "user", "content": request.user_message},
        ]
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # gpt-4o-mini (또는 적절한 모델: gpt-4-turbo)
            messages=messages,
        )
        chatbot_response = response.choices[0].message.content

        # 면책 조항 강조 (정규 표현식 사용)
        chatbot_response = re.sub(
            r"(면책 조항:|Disclaimer:)",
            r"**\1**",  # 볼드체
            chatbot_response
        )
        chatbot_response = re.sub(
            r"(주의:|Note:|Caution:)",
            r"**\1**",  # 볼드체
            chatbot_response
        )

        return {"response": chatbot_response}

    except Exception as e:
        print(f"Error in /chat: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TTS API
@app.post("/tts")
async def text_to_speech(request: ChatRequest):
    global selected_doctor  # 전역 변수 사용

    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice=doctors[selected_doctor]["voice"],
            input=request.user_message,
        )
        # Base64 인코딩
        audio_base64 = base64.b64encode(response.content).decode("utf-8")

        return JSONResponse({"audio": audio_base64})

    except Exception as e:
        print(f"Error in /tts: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 의사 변경 API
@app.post("/select_doctor")
async def select_doctor_api(request: Request):
    global selected_doctor
    data = await request.json()
    selected_doctor = data.get("selected_doctor", selected_doctor)  # 의사 변경
    return {"message": f"Doctor changed to {selected_doctor}"}

# 초기 의사 정보 제공 API
@app.get("/initial_doctor")
async def get_initial_doctor():
    return {"selected_doctor": selected_doctor}

# 정적 파일 제공
app.mount("/", StaticFiles(directory="static", html=True), name="static")