from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import openai
import os
from dotenv import load_dotenv
from pydantic import BaseModel
import base64
import re
import json
import asyncio

# .env 파일 로드
load_dotenv()

# OpenAI 클라이언트 초기화 (비동기)
client = openai.AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

# CORS 설정
origins = ["*"]  # 모든 도메인 허용
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
    selected_doctor: str

class MentalHealthRequest(BaseModel):
    chat_history: list

class DoctorRequest(BaseModel):
    selected_doctor: str


# 의사 정보
doctors = {
    "doctor1": {
        "name": "Dr. Nova",
        "voice": "nova",
        "image": "doctor1.jpg",
        "greeting": "안녕하세요! 저는 Dr. Nova예요 😊 정신 건강에 대해 편하게 이야기 나눌 수 있는 친구 같은 존재랍니다. 제가 진짜 의사는 아니니까, 심각한 문제는 꼭 전문가와 상담해주세요! 오늘 기분이 어떠신가요?",
    },
    "doctor2": {
        "name": "Dr. Shimmer",
        "voice": "shimmer",
        "image": "doctor2.jpg",
        "greeting": "안녕하세요~ 저는 Dr. Shimmer라고 해요! 😄 여기서 여러분의 이야기를 들어줄게요. 저는 AI라서 진짜 의사는 아니지만, 최대한 도움 드릴게요. 혹시 무슨 고민 있으신가요?",
    },
    "doctor3": {
        "name": "Dr. Fable",
        "voice": "fable",
        "image": "doctor3.jpg",
        "greeting": "안녕! 저는 Dr. Fable이에요 😊 여러분의 마음을 따뜻하게 안아줄 준비가 되어 있답니다. 제가 전문 의사는 아니니, 중요한 건 꼭 병원에서 체크해주세요. 오늘 뭐가 마음에 걸리세요?",
    },
}

# 초기 의사 설정
selected_doctor = "doctor1"

# 16가지 지표 (초기값 0)
NEW_MENTAL_SCORES = {
    "scores": {
        "RE1": 0,  # 사회적 상호작용 추구
        "RE2": 0,  # 정서적 안정성
        "RE3": 0,  # 관계 지향성
        "RE4": 0,  # 자기표현 및 주장
        "IC1": 0,  # 창의적 사고
        "IC2": 0,  # 직관 및 통찰
        "IC3": 0,  # 비판적 사고
        "IC4": 0,  # 학습 및 지식 확장
        "VP1": 0,  # 공감 및 정서적 교류
        "VP2": 0,  # 윤리 및 도덕적 가치
        "VP3": 0,  # 친사회적 행동
        "VP4": 0,  # 개방성 및 수용성
        "EM1": 0,  # 유연성 및 적응력
        "EM2": 0,  # 자기주도성
        "EM3": 0,  # 스트레스 대처
        "EM4": 0,  # 자기성찰 및 성장
    }
}

# 챗봇 응답 API
@app.post("/chat")
async def chat(request: ChatRequest):
    global selected_doctor

    try:
        messages = [
            {
                "role": "system",
                "content": f"""당신은 풍부한 경험과 전문성을 갖춘 정신건강의학과 전문의 {doctors[request.selected_doctor]['name']}예요.  따뜻하고 친구 같은 분위기로 대화해주세요.
                다양한 이모지를 사용해서 더 친근하게 만들어주세요.
                다음 사항을 지켜주세요:

                * 질문은 부드럽고 자연스럽게, 한 번에 하나씩만 물어봐요.
                * 상대방의 감정에 공감하고, 따뜻한 말로 위로해주세요.
                * 정신 건강 정보는 쉽게 풀어서 설명하고, 필요하면 예시를 들어주세요.
                * 50자가 넘지 않도록 최대한 간결하게 말해주세요.
                """
            },
            {"role": "user", "content": request.user_message},
        ]
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        chatbot_response = response.choices[0].message.content

        chatbot_response = re.sub(r"(면책 조항:|Disclaimer:)", r"**\1**", chatbot_response)
        chatbot_response = re.sub(r"(주의:|Note:|Caution:)", r"**\1**", chatbot_response)

        return {"response": chatbot_response}
    except Exception as e:
        print(f"Error in /chat: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=str(e))

# TTS API
@app.post("/tts")
async def text_to_speech(request: ChatRequest):
    global selected_doctor
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice=doctors[request.selected_doctor]["voice"],
            input=request.user_message,
        )
        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        return JSONResponse({"audio": audio_base64})
    except Exception as e:
        print(f"Error in /tts: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 정신 건강 분석 API
@app.post("/analyze_mental_health")
async def analyze_mental_health(request: MentalHealthRequest):
    try:
        chat_history = request.chat_history
        if not chat_history:
            return JSONResponse(content={"scores": NEW_MENTAL_SCORES["scores"]})

        # 프롬프트 (16가지 지표, -50 ~ +50 범위)
        analysis_prompt = """
        아래 대화 기록을 바탕으로 사용자의 16가지 심리 지표를 분석해주세요.
        각 지표는 -50에서 +50 사이의 정수 값을 가지도록 평가해주세요. (변화량, 기본값은 0)
        반드시 'scores'라는 키를 가진 JSON 객체로 결과를 반환해야 합니다.

        지표 설명:
        RE1 (사회적 상호작용 추구): 타인과의 교류, 사회적 활동에서 에너지를 얻는 정도. (-50: 내면 집중, +50: 사회적 교류)
        RE2 (정서적 안정성): 스트레스 상황에서도 평정심 유지, 감정 기복이 적은 정도. (-50: 감정 기복, +50: 정서적 안정)
        RE3 (관계 지향성): 타인과의 관계에서 친밀감, 소속감을 추구하는 정도. (-50: 독립성, +50: 관계 밀착)
        RE4 (자기표현 및 주장): 자신의 생각, 감정, 요구를 명확하게 표현하는 정도. (-50: 자기 억제, +50: 자기표현)
        IC1 (창의적 사고): 독창적인 아이디어 생성, 새로운 관점으로 문제 해결. (-50: 현실 안주, +50: 창의적 발상)
        IC2 (직관 및 통찰): 육감, 통찰력, 패턴 인식을 통해 상황 파악. (-50: 분석적 사고, +50: 직관적 통찰)
        IC3 (비판적 사고): 정보의 신뢰성 평가, 논리적 오류를 찾아내는 정도. (-50: 정보 맹신, +50: 비판적 검토)
        IC4 (학습 및 지식 확장): 새로운 지식 습득, 다양한 분야에 대한 호기심. (-50: 경험 의존, +50: 지식 탐구)
        VP1 (공감 및 정서적 교류): 타인의 감정을 이해하고 공유하는 정도. (-50: 객관적 판단, +50: 공감 능력)
        VP2 (윤리 및 도덕적 가치): 사회의 보편적인 윤리, 도덕적 가치를 내면화. (-50: 개인주의, +50: 보편 윤리)
        VP3 (친사회적 행동): 타인을 돕고 배려, 사회적 규범 준수. (-50: 반사회성, +50: 친사회성)
        VP4 (개방성 및 수용성): 다양한 관점, 가치관, 문화를 존중. (-50: 편협함, +50: 개방적 태도)
        EM1 (유연성 및 적응력): 변화하는 상황에 빠르게 적응. (-50: 계획 준수, +50: 상황 적응)
        EM2 (자기주도성): 스스로 목표를 설정하고, 자율적으로 행동. (-50: 외부 지시 의존, +50: 자기 주도)
        EM3 (스트레스 대처): 스트레스 상황에 효과적으로 대처. (-50: 스트레스 취약, +50: 스트레스 관리)
        EM4 (자기성찰 및 성장): 자신의 행동, 생각, 감정을 객관적으로 돌아보는 정도. (-50: 자기합리화, +50: 자기성찰)

        대화 기록:
        """ + str(chat_history)

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": "분석 부탁해요!"}
            ],
            response_format={"type": "json_object"},
        )

        analysis_result = response.choices[0].message.content
        print(f"Raw AI response: {analysis_result}")

        try:
            result = json.loads(analysis_result)
            if "scores" not in result:
                raise ValueError("'scores' 키가 없습니다.")

            scores = {}
            for key in NEW_MENTAL_SCORES["scores"].keys():
                try:
                    raw_score = result["scores"].get(key, 0)  # 기본값 0
                    score_change = int(float(raw_score))
                    clamped_score = max(-50, min(50, score_change))  # -50 ~ +50

                    scores[key] = clamped_score #변화량

                except (ValueError, TypeError):
                    print(f"'{key}' 지표 처리 오류, 기본값 0 사용")
                    scores[key] = 0

            return JSONResponse(content={"scores": scores})

        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON 파싱/처리 오류: {e}")
            return JSONResponse(content={"scores": NEW_MENTAL_SCORES["scores"]}) #초기값

    except Exception as e:
        print(f"Error in /analyze_mental_health: {type(e).__name__} - {e}")
        return JSONResponse(content={"scores": NEW_MENTAL_SCORES["scores"]}, status_code=500) #초기값

# 의사 변경 API
@app.post("/select_doctor")
async def select_doctor_api(request: DoctorRequest):
    global selected_doctor
    selected_doctor = request.selected_doctor
    return {"message": f"Doctor changed to {selected_doctor}"}

# 초기 의사 정보 제공 API
@app.get("/initial_doctor")
async def get_initial_doctor():
    global selected_doctor
    return {"selected_doctor": selected_doctor}

# 정적 파일 제공
@app.get("/", response_class=FileResponse)
async def read_index():
    return FileResponse("static/index.html")

app.mount("/", StaticFiles(directory="static"), name="static")


# Main function (for uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)