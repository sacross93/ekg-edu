from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

import os
from dotenv import load_dotenv
from glob import glob

txt_files = glob("./data/*.txt")

# txt 파일 하나씩 읽어서 배열에 넣기
text_array = []
for txt_file in txt_files:
    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read()
        text_array.append(text)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY_JY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY_JY가 .env 파일에 설정되지 않았습니다.")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-preview-09-2025",
    google_api_key=GEMINI_API_KEY,
    temperature=0.0
)

# 1. 데이터를 전부 확인한 후에 반드시 핵심 주요 질환 1개만 추출해야해
# 2. 왜 그렇게 생각했는지 이유를 먼저 작성하고, 주요 질환을 답변해줘
# 3. 만약 암이 있다면 어떤 암인지도 추가로 작성해줘
# 4. 단순히 disease_name을 보고 그대로 말하는 것이 아닌 모든 disease_name을 보고 확인해서 종합적으로 너가 주요 질환을 결론내서 답변해야해


# 1. 데이터를 전부 확인한 후에 반드시 핵심 주요 질환 1개만 추출해야해
# 2. 주요 질환을 그렇게 판단하게 된 이유를 충분히 생각하도록 해
# 3. 생각이 끝났으면 이유 설명은 안해도 되고 핵심 주요 질환이 무엇이었는지만 답변해
# 4. 만약 암이 있다면 어떤 암인지도 추가로 작성해줘

prompt = PromptTemplate.from_template("""
너는 환자의 5년치 진료기록을 분석하여 핵심 주요 질환 1개를 추출하는 의료 데이터 분석 전문가야.

**핵심 주요 질환의 정의**
핵심 주요 질환은 환자의 건강에 가장 중요한 영향을 미치는 질환으로, 중증도가 높고 지속적으로 치료받는 질환을 의미해

**판단 기준**
다음 기준을 종합적으로 고려해서 판단해야 해:
    1. 질환의 중증도: 생명을 위협하거나 장기적인 건강에 심각한 영향을 미치는 질환이 우선이야
    2. 치료의 지속성: 일시적인 급성 질환보다 만성적으로 지속 관리가 필요한 질환이 더 중요해
    3. 빈도: 동일한 중증도라면 더 자주, 지속적으로 치료받는 질환을 선택해
    4. 결론: 결론적으로 구체적인 병명을 작성해줘 단순 증상만 이야기하지말고 어떤 병인지, 혹은 암인지 작성해달라는거야

**분석 프로세스**
다음 단계를 따라 충분히 생각하면서 분석해줘:
    1. 전체 진료기록에서 등장하는 모든 질환명을 파악하고 각 질환별 빈도를 계산해
    2. 각 질환의 중증도를 평가해 (악성 종양, 만성 중증 질환, 일반 만성 질환, 급성/일시적 질환 등)
    3. 중증도가 가장 높은 질환 그룹을 선택해
    4. 같은 그룹 내에서 빈도가 가장 높거나 가장 지속적으로 치료받는 질환을 선택해

**출력 형식**
분석과 사고 과정이 끝나면, 이유 설명은 생략하고 핵심 주요 질환명만 단답형으로 답변해.
질환명은 데이터에 표기된 방식 그대로 사용하되, 구체적으로 명시해줘.

의료 데이터:```{text}```

위의 기준과 프로세스를 반드시 따라서, 충분히 분석한 후 핵심 주요 질환 1개만 답변해줘:
""")

chain = prompt | llm
result = chain.invoke({"text": text_array[1]})
print(result.content)

