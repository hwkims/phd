import asyncio
import os
import re

import edge_tts
from moviepy.editor import (
    AudioFileClip,
    CompositeAudioClip,
    ConcatenateClip,
    ImageClip,
    TextClip,
    VideoFileClip,
)
from moviepy.video.tools.subtitles import SubtitlesClip
from PIL import Image, ImageDraw, ImageFont
from pydub import AudioSegment
from youtube_transcript_api import YouTubeTranscriptApi

# DuckDuckGo 이미지 검색을 위한 라이브러리 (설치 필요: pip install duckduckgo_search)
from duckduckgo_search import DDGS


def search_images(query, max_results=3):
    """DuckDuckGo에서 이미지를 검색하여 URL 목록을 반환합니다."""
    results = []
    with DDGS() as ddgs:
        for r in ddgs.images(
            query,
            safesearch="Off",
            max_results=max_results,
            region="kr-kr",  # 한국 지역 설정
        ):
            results.append(r["image"])
    return results


async def generate_tts(text, voice="ko-KR-HyunsuNeural", output_file="temp.mp3"):
    """edge-tts를 사용하여 텍스트를 음성으로 변환합니다."""
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)
    return output_file


def create_code_image(code_text, font_size=32, width=1280, height=720):
    """코드 텍스트를 이미지로 변환 (간단한 버전)"""
    img = Image.new("RGB", (width, height), color="black")
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(
        "NanumGothicCoding-Regular.ttf", font_size
    )  # 나눔고딕코딩 폰트 사용

    # 코드 텍스트 줄바꿈 처리
    lines = code_text.splitlines()
    y_offset = 50
    for line in lines:
        d.text((50, y_offset), line, font=font, fill="white")
        y_offset += font_size + 5

    return img


def create_video_from_script(script, output_filename="tutorial_video.mp4"):
    """대본을 기반으로 영상을 생성합니다."""
    clips = []
    section_num = 0  # 섹션 번호

    # 섹션 분할 (문단 또는 특정 패턴으로)
    sections = re.split(r"\n\n+", script.strip())  # 빈 줄 두 개 이상으로 분할

    for section in sections:
        section_num += 1
        print(f"Processing section {section_num}...")

        # 섹션 제목 (첫 문장)
        title = section.split(".")[0] + "."

        # 1. TTS 음성 생성
        tts_filename = f"tts_{section_num}.mp3"
        asyncio.run(generate_tts(section, output_file=tts_filename))

        # 음성 파일 길이 확인
        audio = AudioSegment.from_file(tts_filename)
        duration = audio.duration_seconds

        # 2. 이미지 검색 및 생성
        #   - 섹션 제목으로 DuckDuckGo 이미지 검색
        #   - 코드 포함 여부 확인 후, 코드 이미지 생성
        image_urls = search_images(title + " tech", max_results=3)  # 검색어 수정
        if "```" in section:  # 코드 블록이 있으면
            code_start = section.find("```") + 3
            code_end = section.find("```", code_start)
            code_text = section[code_start:code_end].strip()
            code_image = create_code_image(code_text)
            code_image_path = f"code_image_{section_num}.png"
            code_image.save(code_image_path)
            image_clip = ImageClip(code_image_path, duration=duration)
            clips.append(image_clip)

        elif image_urls:
            # 검색된 이미지 중 첫 번째 이미지 사용
            image_clip = ImageClip(image_urls[0], duration=duration)
            clips.append(image_clip)

        else:
            # 이미지를 찾지 못한 경우, 기본 이미지 또는 제목 텍스트 클립
            text_clip = TextClip(
                title, fontsize=48, color="white", size=(1280, 720), bg_color="gray"
            )
            text_clip = text_clip.set_duration(duration)
            clips.append(text_clip)

        # 3. 음성 추가
        audio_clip = AudioFileClip(tts_filename)

        # 배경 음악 추가 (선택 사항)
        try:  # 배경 음악 파일이 없는 경우 에러 처리
            bgm_clip = AudioFileClip("background_music.mp3").subclip(
                0, duration
            )  # 전체 길이 맞춤.
            bgm_clip = bgm_clip.volumex(0.1)  # 볼륨 조절 (10%)
            audio_clip = CompositeAudioClip([audio_clip, bgm_clip])
            # audio_clip = audio_clip.set_duration(duration) # duration 설정은 나중에
        except:
            print("배경 음악 파일을 찾을 수 없습니다. 배경 음악 없이 진행합니다.")

        clips[-1] = clips[-1].set_audio(audio_clip)  # 마지막 클립에 음성 추가
        clips[-1] = clips[-1].set_duration(
            duration
        )  # duration 설정은 set_audio() 다음에 해야 함.

    # 4. 클립 합치기
    final_clip = ConcatenateClip(clips)

    # 5. 자막 추가 (선택 사항):  youtube_transcript_api 사용 또는 직접 생성
    # generator = lambda txt: TextClip(
    #     txt, font="Arial", fontsize=24, color="white", bg_color="black"
    # )
    # subtitles = SubtitlesClip("subtitles.srt", generator) # .srt 파일 필요
    # final_clip = CompositeVideoClip([final_clip, subtitles])

    # 6. 영상 저장
    final_clip.write_videofile(
        output_filename,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        threads=4,  # 멀티스레딩
        preset="ultrafast",  # 인코딩 속도
    )

    # 임시 파일 삭제
    for i in range(1, section_num + 1):
        try:
            os.remove(f"tts_{i}.mp3")
            if os.path.exists(f"code_image_{i}.png"):
                os.remove(f"code_image_{i}.png")

        except:
            pass


if __name__ == "__main__":
    script = """
안녕하세요! 오늘은 FastAPI, DuckDNS, 그리고 Open AI API를 이용해서 여러분만의 AI 챗봇, "마음챙김 챗봇"을 만들고 전 세계와 공유하는 방법을 알아보겠습니다. 챗봇 제작부터 배포까지, 모든 과정을 쉽고 자세하게 설명해 드릴게요. 준비되셨나요?

"마음챙김 챗봇"은 현대인의 정신 건강을 돕기 위해 개발된 AI 기반 심리 상담 챗봇입니다. Open AI의 최신 언어 모델인 GPT-4o를 사용해서 친구와 대화하듯 자연스럽고 편안한 대화를 제공하고, 딱딱한 질의응답이 아니라 사용자의 감정에 공감하며 대화를 이어나갑니다. MBTI 성격 유형 검사를 기반으로 사용자의 4대 기능과 16가지 세부 지표를 분석하여 더욱 심층적인 심리 상태를 파악하고, 심리 분석 결과를 바탕으로 사용자의 특성과 상황에 맞는 개인별 맞춤형 조언과 정보를 제공합니다. Chart.js를 활용하여 심리 분석 결과를 보기 쉬운 그래프 형태로 제공하여 자신의 심리 상태를 한눈에 파악할 수 있고, Leaflet을 이용하여 현재 위치 기반 주변 정신과 병원 정보도 제공합니다. 별도 설치 없이 웹 브라우저를 통해 언제 어디서든 쉽게 접근할 수 있으며, 반응형 디자인으로 PC, 모바일, 태블릿 등 다양한 기기에서 최적화된 화면을 제공합니다.

이제 챗봇의 두뇌를 만들어 볼까요? FastAPI는 Python으로 빠르고 쉽게 API 서버를 구축할 수 있게 해주는 프레임워크입니다. 먼저, 터미널에서 pip install fastapi uvicorn openai python-dotenv pydantic 명령어로 필요한 라이브러리들을 설치합니다. 그 후 main.py 파일을 만들고, FastAPI 앱 인스턴스를 생성합니다. 챗봇과의 대화를 처리하는 /chat, 텍스트를 음성으로 변환하는 /tts, 대화 기록을 기반으로 사용자의 심리 상태를 분석하는 /analyze_mental_health, 대화 내용을 요약하는 /summarize_chat, 그리고 챗봇의 종류를 선택하는 /select_doctor와 같은 API 엔드포인트를 정의합니다. .env 파일에 Open AI API 키를 저장하고, openai 라이브러리를 사용하여 API를 호출하며, 프롬프트 엔지니어링을 통해 챗봇의 페르소나, 역할, 지침 등을 설정합니다. Pydantic을 사용하여 API 요청 및 응답 데이터의 형식을 정의하여 데이터 유효성 검사를 자동화하고, API 문서를 쉽게 생성할 수 있습니다.

이제 사용자가 챗봇과 상호작용할 수 있는 웹 인터페이스를 만들어야 합니다. HTML로 챗봇 UI의 기본 구조를 정의하는데, 채팅 메시지를 표시할 영역, 사용자 입력 창, 전송 버튼, 심리 분석 결과를 표시할 캔버스, 주변 병원 정보를 표시할 지도, 그리고 닥터 이미지와 닥터 변경 버튼을 표시할 요소들을 만듭니다. CSS로 챗봇 UI 스타일에 원하는 스타일을 적용하고, JavaScript를 사용해 사용자 입력을 받아서 FastAPI 백엔드로 전송하고, 백엔드로부터 받은 응답을 화면에 표시하거나 처리합니다. Chart.js를 사용하여 심리 분석 결과를 그래프로 시각화하고, Leaflet을 사용하여 지도 기능을 구현하고, 현재 위치 및 주변 병원 정보를 표시하며, 닥터 이미지와 닥터 변경 버튼에 대한 이벤트 리스너를 추가하여 사용자가 챗봇의 종류를 선택할 수 있도록 합니다.

이제 챗봇을 전 세계에 공개할 차례입니다. DuckDNS는 무료 동적 DNS 서비스를 제공하여, 변동하는 IP 주소에서도 챗봇에 접근할 수 있게 해줍니다. DuckDNS 웹사이트에 접속하여 원하는 계정으로 로그인하고, 원하는 도메인 이름을 입력하고 "add domain" 버튼을 클릭합니다. DuckDNS가 자동으로 현재 IP 주소를 찾아주면, "update" 버튼을 클릭하여 저장합니다.

여기서 잠깐! 좀 더 안정적이고 24시간 운영되는 챗봇을 원한다면, Vultr나 AWS와 같은 클라우드 서비스를 이용하는 것이 좋습니다. 클라우드 서비스는 가상의 서버를 제공하여, 여러분의 컴퓨터를 계속 켜두지 않아도 챗봇을 운영할 수 있게 해줍니다. Vultr나 AWS에서 가상 서버를 생성하고, 운영체제(Ubuntu 등)를 설치한 후, 위에서 설명한 FastAPI 개발 환경을 그대로 구축하면 됩니다. 그 다음, uvicorn main:app --reload --host=0.0.0.0 --port=8000 명령어를 사용하여 FastAPI 서버를 실행합니다. 이때, 클라우드 서버의 IP 주소를 DuckDNS에 등록하면, DuckDNS 도메인을 통해 챗봇에 접속할 수 있습니다. 만약, 여러분의 컴퓨터에서 직접 챗봇을 실행하려면, uvicorn main:app --reload --host=0.0.0.0 --port=8000 명령어를 사용하여 FastAPI 서버를 실행하고 --host=0.0.0.0 옵션은 외부 접속을 허용하는 중요한 설정이며 공유기를 사용하는 경우, 공유기 설정 페이지에서 외부 8000번 포트로 들어오는 요청을 내부 컴퓨터의 8000번 포트로 전달하도록 설정해야 합니다. 이제 웹 브라우저에서 여러분의 DuckDNS 도메인 주소로 접속하여 챗봇이 정상적으로 작동하는지 확인합니다.

웹사이트 보안을 위해 HTTPS를 적용하는 것이 좋습니다. Let's Encrypt는 무료로 SSL 인증서를 발급해주는 기관이며, Certbot 도구를 사용하면 간단하게 인증서를 발급받고, Nginx나 Apache 같은 웹 서버에 설정할 수 있습니다.

축하합니다! 이제 여러분의 AI 챗봇이 DuckDNS를 통해, 또는 Vultr나 AWS를 통해 전 세계 어디에서든 접근 가능하게 되었습니다. FastAPI, DuckDNS, Open AI API, 그리고 약간의 프론트엔드 지식만 있으면 누구나 챗봇 서비스를 만들 수 있습니다.
"""
    create_video_from_script(script)
