import os
import httpx
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate

# 1. .env 파일의 환경 변수 로드
load_dotenv()

# 2. 날씨 데이터를 가져올 외부 API 도구(Tool) 정의
@tool
def get_current_weather(latitude: float, longitude: float) -> str:
    """주어진 위도(latitude)와 경도(longitude)의 현재 날씨를 가져옵니다."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"
    
    try:
        response = httpx.get(url)
        response.raise_for_status()
        data = response.json()
        weather = data.get("current_weather", {})
        temperature = weather.get("temperature")
        windspeed = weather.get("windspeed")
        
        if temperature is not None:
            return f"현재 온도: {temperature}°C, 풍속: {windspeed}km/h"
        else:
            return "날씨 데이터를 찾을 수 없습니다."
    except Exception as e:
        return f"날씨 정보를 가져오는 중 오류가 발생했습니다: {str(e)}"

# 3. LLM, 프롬프트, 에이전트 설정 및 실행 함수
def run_weather_agent(query: str):
    # API 키 및 모델명 확인
    api_key = os.getenv("QWEN_API_KEY")
    base_url = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model_name = os.getenv("QWEN_MODEL_NAME", "qwen-turbo")

    if not api_key:
        print("[오류] .env 파일에 QWEN_API_KEY가 설정되지 않았습니다.")
        return

    # Qwen LLM 초기화 (OpenAI 호환 모드)
    llm = ChatOpenAI(
        api_key=api_key,
        base_url=base_url,
        model=model_name
    )

    # 에이전트 가이드라인 프롬프트 설정
    prompt = ChatPromptTemplate.from_messages([
        ("system", "당신은 유능한 날씨 안내 에이전트입니다. "
                   "사용자가 특정 지역의 날씨를 물어보면, 먼저 해당 지역의 대략적인 위도와 경도를 추론한 뒤 "
                   "get_current_weather 도구를 사용하여 날씨를 확인하고 친절하게 답변해주세요. "
                   "(예: 서울은 위도 37.56, 경도 126.97)"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ])

    # 도구 바인딩 및 에이전트 생성
    tools = [get_current_weather]
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 에이전트 실행기 구성 (verbose=True로 중간 생각 과정 출력)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    print(f"\n[질문]: {query}")
    print("-" * 50)
    
    # 에이전트 작동 시동
    try:
        response = agent_executor.invoke({"input": query})
        print("-" * 50)
        print(f"[최종 답변]:\n{response['output']}")
    except Exception as e:
        print(f"에이전트 실행 중 오류가 발생했습니다: {str(e)}")

if __name__ == "__main__":
    # 테스트할 질문 설정
    user_query = "서울의 현재 날씨는 어때?"
    run_weather_agent(user_query)
