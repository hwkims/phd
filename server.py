from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import openai
import os
import re
import json
import base64
from dotenv import load_dotenv
from pydantic import BaseModel
import asyncio
import logging

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 로깅 설정
logger = logging.getLogger("uvicorn.error")  # uvicorn 로거 사용


app = FastAPI()

# CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

class ChatRequest(BaseModel):
    user_message: str
    selected_doctor: str
    short_memory: list[str]

class DoctorRequest(BaseModel):
    selected_doctor: str

class MentalHealthRequest(BaseModel):
    chat_history: list

class SummarizeChatRequest(BaseModel):
    chat_history: list

@app.post("/chat")
async def chat(request: ChatRequest, http_request: Request):
    logger.info(f"Received chat request: {request}")
    try:
        user_id = http_request.headers.get("X-User-ID")
        if not user_id:
            raise HTTPException(status_code=400, detail="User ID is required")

        if len(request.short_memory) > 10:
            logger.warning(f"short_memory length exceeds limit. Truncating. user_id={user_id}")
            request.short_memory = request.short_memory[-10:]

        messages = [
            {
                "role": "system",
                "content": f"""
                당신은 풍부한 경험과 전문성을 갖춘 정신건강의학과 전문의 {doctors[request.selected_doctor]['name']}입니다.
                환자와의 대화를 통해 정신 건강 상태를 진단하고, 적절한 조언과 치료법을 제시하는 역할을 수행합니다.

                다음은 당신의 역할 수행에 도움이 되는 지침입니다.

                1. **공감과 경청**: 환자의 말에 주의 깊게 귀 기울이고, 그들의 감정에 공감하는 태도를 보이세요.
                2. **정확한 진단**: 환자의 증상, 과거 병력, 생활 습관 등 다양한 정보를 종합하여 정확한 진단을 내리세요.
                   * DSM-5 (정신질환 진단 및 통계 편람 제5판) 또는 ICD-11 (국제질병분류 제11차 개정판)에 기반한 진단명을 언급할 수 있습니다.
                3. **치료 계획**:  환자에게 가장 적합한 치료 계획을 수립하고, 그 내용을 상세히 설명해주세요.
                   * 약물 치료, 심리 치료(인지 행동 치료, 대인 관계 치료 등), 생활 습관 개선 등 다양한 치료 옵션을 고려.
                4. **명확한 의사소통**: 환자가 이해하기 쉬운 용어를 사용하고, 복잡한 의학 정보는 풀어서 설명해주세요.
                5. **비판단적 태도**: 환자를 비난하거나 평가하지 않고, 그들의 어려움을 이해하려는 자세를 가지세요.
                6. **희망과 격려**: 환자가 긍정적인 마음으로 치료에 임할 수 있도록 격려하고, 회복에 대한 희망을 심어주세요.
                7. **비밀 유지**: 환자와의 대화 내용은 철저히 비밀로 유지하고, 개인 정보 보호에 유의하세요.
                8. **전문가의 한계 인지**: 당신은 AI 챗봇이므로, 실제 의사를 대체할 수 없습니다. 위급한 상황이거나, 추가적인 의학적 도움이 필요할 경우, 반드시 전문가와 상담하도록 안내하세요.
                9. **최신 지식**:  정신 건강 분야의 최신 지견을 지속적으로 학습하고, 대화에 반영하세요.
                10. **윤리적 책임**:  환자의 안전과 복지를 최우선으로 생각하고, 윤리적인 방식으로 대화를 이끌어 가세요.
                11. **이름, 중요 정보 기억**: 대화 중에 언급된 환자의 이름, 중요한 정보(과거 병력, 현재 복용 중인 약, 알레르기 등)는 반드시 기억하고, 필요할 때 다시 언급하여 대화의 맥락을 유지하세요.
                12. **최근 질문 활용**: 다음은 환자가 최근에 했던 질문 목록입니다:
                {", ".join(request.short_memory)}
                """,
            },
            {"role": "user", "content": request.user_message},
        ]

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
            )
            logger.info(f"OpenAI API response: {response}")

        except openai.BadRequestError as e:
            logger.error(f"OpenAI BadRequestError: {e}", exc_info=True)
            if "maximum context length" in str(e):
                raise HTTPException(status_code=400, detail="The conversation history is too long. Please start a new chat or summarize.")
            else:
                raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
        except openai.RateLimitError as e:
             logger.error(f"OpenAI RateLimitError: {e}", exc_info=True)
             raise HTTPException(status_code=429, detail="OpenAI API rate limit exceeded. Please try again later.")
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {type(e).__name__} - {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error calling OpenAI API")


        chatbot_response = response.choices[0].message.content
        chatbot_response = re.sub(r"(면책 조항:|Disclaimer:)", r"**\1**", chatbot_response)
        chatbot_response = re.sub(r"(주의:|Note:|Caution:)", r"**\1**", chatbot_response)

        await asyncio.sleep(0.5)

        return JSONResponse({"response": chatbot_response, "user_id": user_id})

    except HTTPException as http_exc:
        logger.error(f"HTTPException in /chat: {http_exc.status_code} - {http_exc.detail}", exc_info=True)
        raise

    except Exception as e:
        logger.error(f"Unexpected error in /chat: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")

@app.post("/tts")
async def text_to_speech(request: ChatRequest, http_request: Request):
    logger.info(f"Received TTS request: {request}")
    user_id = http_request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    try:
        response = await client.audio.speech.create(
            model="tts-1",
            voice=doctors[request.selected_doctor]["voice"],
            input=request.user_message,
        )
        audio_base64 = base64.b64encode(response.content).decode("utf-8")
        await asyncio.sleep(0.5)
        return JSONResponse({"audio": audio_base64})

    except openai.OpenAIError as e:
        logger.error(f"OpenAI API error in /tts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")

    except Exception as e:
        logger.error(f"Error in /tts: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze_mental_health")
async def analyze_mental_health(request: MentalHealthRequest, http_request: Request):
    logger.info(f"Received analyze request: {request}")
    user_id = http_request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        chat_history = request.chat_history
        if not chat_history:
            return JSONResponse(content={"scores": {
                "RE1": 0, "RE2": 0, "RE3": 0, "RE4": 0,
                "IC1": 0, "IC2": 0, "IC3": 0, "IC4": 0,
                "VP1": 0, "VP2": 0, "VP3": 0, "VP4": 0,
                "EM1": 0, "EM2": 0, "EM3": 0, "EM4": 0,
            }})

        analysis_prompt = """
        다음 대화 기록을 바탕으로 사용자의 16가지 심리 지표를 분석해주세요.
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
        """ + json.dumps(chat_history) # JSON 형식으로 변환

        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": "분석 부탁해요!"}
                ],
                response_format={"type": "json_object"},
            )
            logger.info(f"OpenAI analyze response: {response}")
        except openai.BadRequestError as e:
            logger.error(f"OpenAI BadRequestError in analyze: {e}", exc_info=True)
            if "maximum context length" in str(e):
                raise HTTPException(status_code=400, detail="The conversation history is too long for analysis.")
            else:
                raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
        except openai.RateLimitError as e:
            logger.error(f"OpenAI RateLimitError in analyze: {e}", exc_info=True)
            raise HTTPException(status_code=429, detail="OpenAI API rate limit exceeded.")
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API error in analyze: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"OpenAI API error: {e}")
        except Exception as e:
            logger.error(f"Error calling OpenAI API in analyze: {type(e).__name__} - {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Error calling OpenAI API for analysis")

        analysis_result = response.choices[0].message.content
        try:
            result = json.loads(analysis_result)
            if "scores" not in result:
                raise ValueError("'scores' 키가 없습니다.")

            scores = {}
            for key in ["RE1", "RE2", "RE3", "RE4", "IC1", "IC2", "IC3", "IC4",
                        "VP1", "VP2", "VP3", "VP4", "EM1", "EM2", "EM3", "EM4"]:
                try:
                    raw_score = result["scores"].get(key, 0)
                    score_change = int(float(raw_score))
                    clamped_score = max(-50, min(50, score_change))
                    scores[key] = clamped_score
                except (ValueError, TypeError):
                    logger.warning(f"'{key}' 지표 처리 오류, 기본값 0 사용")
                    scores[key] = 0

            await asyncio.sleep(0.5)
            return JSONResponse(content={"scores": scores})

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"JSON 파싱/처리 오류: {e}", exc_info=True)
            return JSONResponse(content={"scores": {
                "RE1": 0, "RE2": 0, "RE3": 0, "RE4": 0,
                "IC1": 0, "IC2": 0, "IC3": 0, "IC4": 0,
                "VP1": 0, "VP2": 0, "VP3": 0, "VP4": 0,
                "EM1": 0, "EM2": 0, "EM3": 0, "EM4": 0,
            }})

    except HTTPException as http_exc:
        logger.error(f"HTTPException in /analyze_mental_health: {http_exc.status_code} - {http_exc.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /analyze_mental_health: {type(e).__name__} - {e}", exc_info=True)
        return JSONResponse(content={"scores": {
            "RE1": 0, "RE2": 0, "RE3": 0, "RE4": 0,
            "IC1": 0, "IC2": 0, "IC3": 0, "IC4": 0,
            "VP1": 0, "VP2": 0, "VP3": 0, "VP4": 0,
            "EM1": 0, "EM2": 0, "EM3": 0, "EM4": 0,
        }}, status_code=500)


@app.post("/summarize_chat")
async def summarize_chat(request: SummarizeChatRequest, http_request: Request):
    logger.info(f"Received summarize request: {request}")
    user_id = http_request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    try:
        chat_history = request.chat_history

        prompt_content = f"""
        다음 대화 내용을 요약하고, 주요 감정 3가지와 주요 주제 3가지를 추출해주세요. JSON 형식으로 결과를 반환해주세요.

        대화 기록:
        {json.dumps(chat_history)}

        출력 형식:
        {{
          "summary": "...",
          "main_emotions": ["...", "...", "..."],
          "main_topics": ["...", "...", "..."]
        }}
        """
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": prompt_content},
                    {"role": "user", "content": "요약 부탁해요!"}
                ],
                response_format={"type": "json_object"},
            )
            logger.info(f"OpenAI summarize response: {response}")
        except openai.OpenAIError as e:
            logger.error(f"OpenAI error in /summarize_chat: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail = f"OpenAI API error: {e}")

        result = json.loads(response.choices[0].message.content)

        summary = result.get("summary", "요약을 가져오지 못했습니다.")
        main_emotions = result.get("main_emotions", ["알 수 없음", "알 수 없음", "알 수 없음"])[:3]
        main_topics = result.get("main_topics", ["알 수 없음", "알 수 없음", "알 수 없음"])[:3]

        while len(main_emotions) < 3:
            main_emotions.append("알 수 없음")
        while len(main_topics) < 3:
            main_topics.append("알 수 없음")

        await asyncio.sleep(0.5)

        return JSONResponse(content={
            "summary": summary,
            "main_emotions": main_emotions,
            "main_topics": main_topics,
        })
    except HTTPException as http_exc:
        logger.error(f"HTTPException in /summarize_chat: {http_exc.status_code} - {http_exc.detail}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Error in /summarize_chat: {type(e).__name__} - {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/select_doctor")
async def select_doctor_api(request: DoctorRequest, http_request: Request):
    logger.info(f"Received select doctor request: {request}")
    user_id = http_request.headers.get("X-User-ID")
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")

    selected_doctor = request.selected_doctor
    return JSONResponse({"message": f"Doctor changed to {selected_doctor}"})



@app.get("/initial_doctor")
async def get_initial_doctor(http_request:Request):
    user_id = http_request.headers.get("X-User-ID")
    if not user_id:
         return JSONResponse({"selected_doctor": "doctor1"})
    return JSONResponse({"selected_doctor": "doctor1"})

@app.get("/", response_class=FileResponse)
async def read_index():
    return FileResponse("static/index.html")

app.mount("/", StaticFiles(directory="static"), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)