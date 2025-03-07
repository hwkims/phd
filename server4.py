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


# 의사 정보 (이전과 동일)
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

# 새롭게 정의된 16가지 지표 (초기값 50)
NEW_MENTAL_SCORES = {
  "scores": {
        "RE1": 50,  # 자기 성찰 및 내면 탐구
        "RE2": 50,  # 정서적 안정성 및 평정심
        "RE3": 50,  # 진정성 있는 관계 형성
        "RE4": 50,  # 자기 통제 및 감정 조절
        "IC1": 50,  # 창의적 문제 해결 및 혁신
        "IC2": 50,  # 직관적 통찰 및 패턴 인식
        "IC3": 50,  # 비판적 사고 및 정보 분석
        "IC4": 50,  # 학습 민첩성 및 지식 융합
        "VP1": 50,  # 공감 능력 및 사회적 지능
        "VP2": 50,  # 도덕성 및 윤리 의식
        "VP3": 50,  # 반사회적 성향 (낮을수록 좋음)
        "VP4": 50,  # 개방성 및 포용성
        "EM1": 50,  # 적응 유연성 및 변화 수용
        "EM2": 50,  # 자기 주도 학습 및 성장
        "EM3": 50,  # 심리적 회복력 및 스트레스 관리
        "EM4": 50   # 자기 성찰 및 자기 이해
    }
}



# 챗봇 응답 API (이전과 거의 동일)
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

# TTS API (이전과 동일)
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

# 정신 건강 분석 API (새로운 지표에 맞춰 대폭 수정)
@app.post("/analyze_mental_health")
async def analyze_mental_health(request: MentalHealthRequest):
    try:
        chat_history = request.chat_history
        if not chat_history:
            return JSONResponse(content={"scores": NEW_MENTAL_SCORES["scores"]})

        # 새로운 프롬프트 (16가지 지표에 대한 설명 포함)
        analysis_prompt = f"""
        아래 대화 기록을 바탕으로 사용자의 16가지 심리 지표를 분석해주세요.
        각 지표는 -10에서 +10 사이의 정수 값을 가지도록 평가해주세요. (변화량, 기본값은 50)
        반드시 'scores'라는 키를 가진 JSON 객체로 결과를 반환해야 합니다.

        지표 설명:
        RE1 (자기 성찰 및 내면 탐구):  자신의 내면을 깊이 성찰하고, 혼자만의 시간을 통해 에너지를 얻는 정도. (높을수록 내향적)
        RE2 (정서적 안정성 및 평정심):  스트레스 상황에서도 감정 기복 없이 평정심을 유지하는 능력. (높을수록 안정적)
        RE3 (진정성 있는 관계 형성): 소수의 사람들과 깊이 있는 관계를 맺고, 진솔한 소통을 하는 능력. (높을수록 깊은 관계 지향)
        RE4 (자기 통제 및 감정 조절): 자신의 감정과 충동을 조절하고, 건강한 방식으로 해소하는 능력. (높을수록 자기 통제력 높음)
        IC1 (창의적 문제 해결 및 혁신): 독창적인 아이디어를 생성하고, 혁신적인 해결책을 제시하는 능력. (높을수록 창의적)
        IC2 (직관적 통찰 및 패턴 인식): 육감, 통찰력, 패턴 인식을 통해 정보의 숨겨진 의미를 파악하는 능력. (높을수록 직관적)
        IC3 (비판적 사고 및 정보 분석): 정보의 신뢰성을 평가하고, 논리적 오류를 찾아내며, 객관적으로 판단하는 능력. (높을수록 비판적)
        IC4 (학습 민첩성 및 지식 융합): 새로운 지식을 빠르게 습득하고, 다양한 분야의 지식을 융합하는 능력. (높을수록 학습 민첩)
        VP1 (공감 능력 및 사회적 지능): 타인의 감정을 인식하고 공감하며, 사회적 상황에 맞게 행동하는 능력. (높을수록 공감 능력 높음)
        VP2 (도덕성 및 윤리 의식): 보편적인 도덕적 원칙과 가치를 내면화하고, 공정하게 행동하는 능력. (높을수록 도덕적)
        VP3 (반사회적 성향): 타인의 권리를 무시하고, 사회적 규범을 위반하는 경향.  (낮을수록 좋음, 0에 가까울수록 친사회적)
        VP4 (개방성 및 포용성): 다양한 관점을 존중하고, 새로운 아이디어를 수용하며, 차이를 포용하는 능력 (높을수록 개방적)
        EM1 (적응 유연성 및 변화 수용): 변화하는 상황에 빠르게 적응하고, 즉흥적인 결정을 내리는 능력. (높을수록 유연)
        EM2 (자기 주도 학습 및 성장): 스스로 학습 목표를 설정하고, 지속적으로 성장하는 능력. (높을수록 자기 주도적)
        EM3 (심리적 회복력 및 스트레스 관리): 스트레스, 역경, 실패를 극복하고 긍정적인 심리 상태를 회복하는 능력 (높을수록 회복력 높음)
        EM4 (자기 성찰 및 자기 이해): 자신의 강점과 약점을 객관적으로 파악하고 성장하는 능력 (높을수록 자기 이해 높음)


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
                    raw_score = result["scores"].get(key, 0)
                    score_change = int(float(raw_score))
                    clamped_score = max(-10, min(10, score_change))  # -10 ~ +10
                    # VP3 (반사회성) 지표는 낮을수록 좋으므로, 반전시켜서 계산
                    if key == "VP3":
                        scores[key] = 50 - clamped_score
                    else:
                        scores[key] = 50 + clamped_score

                except (ValueError, TypeError):
                    print(f"'{key}' 지표 처리 오류, 기본값 50 사용")
                    scores[key] = 50

            return JSONResponse(content={"scores": scores})

        except (json.JSONDecodeError, ValueError) as e:
            print(f"JSON 파싱/처리 오류: {e}")
            return JSONResponse(content={"scores": NEW_MENTAL_SCORES["scores"]})

    except Exception as e:
        print(f"Error in /analyze_mental_health: {type(e).__name__} - {e}")
        return JSONResponse(content={"scores": NEW_MENTAL_SCORES["scores"]}, status_code=500)

# 의사 변경 API (이전과 동일)
@app.post("/select_doctor")
async def select_doctor_api(request: DoctorRequest):
    global selected_doctor
    selected_doctor = request.selected_doctor
    return {"message": f"Doctor changed to {selected_doctor}"}

# 초기 의사 정보 제공 API (이전과 동일)
@app.get("/initial_doctor")
async def get_initial_doctor():
    global selected_doctor
    return {"selected_doctor": selected_doctor}

# 정적 파일 제공 (이전과 동일)
@app.get("/", response_class=FileResponse)
async def read_index():
    return FileResponse("static/index.html")

app.mount("/", StaticFiles(directory="static"), name="static")


# Main function (for uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)