"""Natural Korean quality policy for customer-facing report prose.

The policy does not punish repetition by itself. In Korean fortune reports,
stable repetition can be more natural than forced variation. This checker
focuses on awkward collocations, translation-style particles, abstract prose,
multi-core sentences, conditional escape language, and internal register leaks.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass


NATURAL_KOREAN_POLICY_VERSION = "natural_korean_policy_v5"


@dataclass(frozen=True)
class NaturalKoreanIssue:
    """One detected naturalness issue in a Korean sentence."""

    code: str
    marker: str
    severity: int
    reason: str
    suggestion: str


TRANSLATION_STYLE_MARKERS = (
    "을 통해",
    "를 통해",
    "에 있어",
    "에 대한",
    "와 관련",
    "과 관련",
    "와 관련하여",
    "과 관련하여",
    "의 경우",
    "로부터",
    "하기 위해",
    "하기 위한",
    "하는 중",
    "가지고 있는",
    "위치하고 있는",
    "요구합니다",
)

PASSIVE_REPORT_ENDINGS = (
    "드러납니다",
    "나타납니다",
    "확인됩니다",
    "정해집니다",
    "이어집니다",
    "반영됩니다",
    "구체화됩니다",
    "부각됩니다",
    "작용합니다",
    "연동됩니다",
    "평가됩니다",
    "예상됩니다",
)

ABSTRACT_NOUNS = (
    "기준",
    "조건",
    "가능성",
    "판단",
    "관리",
    "조정",
    "안정",
    "체감",
    "작용",
    "요소",
    "구조",
    "역할",
    "방식",
    "성향",
    "상황",
    "국면",
    "비중",
)

SCENE_NOUNS = (
    "돈",
    "수입",
    "보수",
    "정산",
    "계약",
    "통장",
    "현금",
    "고정비",
    "자산",
    "일",
    "업무",
    "직무",
    "회의",
    "평가",
    "보고",
    "문서",
    "연락",
    "말투",
    "만남",
    "약속",
    "대화",
    "배우자",
    "생활비",
    "주거",
    "가족",
    "집안일",
)

WEAK_ABSTRACT_SUBJECTS = (
    "운",
    "기준",
    "조건",
    "가능성",
    "요소",
    "구조",
    "성향",
    "역할",
    "방식",
    "국면",
)

AWKWARD_COLLOCATIONS = {
    "운이 좌우": "운세 상담서에서는 '좌우합니다'보다 실제 결론을 바로 말해야 합니다.",
    "결과가 남습니다": "결과가 남는다는 말은 추상적입니다. 보수, 평가, 자리, 계약처럼 남는 대상을 밝혀야 합니다.",
    "성과가 남습니다": "성과가 남는다는 말은 기계적으로 들립니다. 좋은 평가를 받는다, 보수가 오른다처럼 말해야 합니다.",
    "좋은 성과를 냅니다": "너무 범용적인 칭찬입니다. 돈, 인정, 관계 안정처럼 영역별 결과를 말해야 합니다.",
    "실제로 남습니다": "'실제로'가 붙으면 오히려 자신 없어 보입니다. 무엇이 남는지 바로 말해야 합니다.",
    "수입이 됩니다": "'수입이 됩니다'는 번역투에 가깝습니다. 수입으로 바뀐다, 수입으로 이어진다처럼 자연스럽게 말합니다.",
    "평가도 굳어집니다": "평가는 굳어진다보다 안정된다, 좋아진다, 빨라진다가 자연스럽습니다.",
    "주거 문제도 실제로 다뤄집니다": "'실제로 다뤄진다'는 보고서식입니다. 함께 논의된다, 결정된다처럼 상담 장면으로 말해야 합니다.",
    "일에서 실력을 인정받습니다": "앞 문맥에 '실력을 인정받는 일'이 붙으면 같은 의미가 반복됩니다. 축별 완성 문장으로 다시 써야 합니다.",
    "일에서 인정과 다음 역할": "앞 문맥에 '인정을 받는 일'이 붙으면 인정이 반복됩니다. 축별 완성 문장으로 다시 써야 합니다.",
    "공식 평가를 받는 일에서 공식 평가": "같은 의미가 한 문장 안에서 반복됩니다. 명예운의 결과를 별도 문장으로 써야 합니다.",
    "기준을 세우는 일에서 받을 보수": "수입 확대 설명에서 기준과 보수가 어색하게 겹칩니다. 보수 기준을 잘 세운다, 받을 보수가 커진다로 나누어 말해야 합니다.",
    "일에서 강점이 분명하게 살아납니다": "축 설명의 fallback 조립문입니다. 축별로 어떤 결과가 좋아지는지 완성 문장으로 써야 합니다.",
    "생각과 감정을 알아듣게 전합니다": "누가 알아듣는지 빠져 있어 어색합니다. 상대가 알아듣게 전한다고 써야 합니다.",
    "크게 움직입니다": "'크게 움직입니다'는 운세 결론을 흐립니다. 실제로 생기는 일이나 달라지는 대상을 말해야 합니다.",
    "구체적으로 움직입니다": "'구체적으로 움직입니다'는 내부 계산어처럼 들립니다. 맡게 되는 일, 정해지는 금액, 달라지는 관계를 직접 말해야 합니다.",
    "빠르게 움직입니다": "'빠르게 움직입니다'는 대상이 흐립니다. 빠르게 달라집니다, 빨리 정해집니다처럼 실제 변화를 말해야 합니다.",
    "태도가 먼저 움직입니다": "사람의 태도는 움직인다기보다 드러납니다.",
    "바로 움직이는 돈": "돈이 움직인다는 말보다 바로 쓰고 정리해야 하는 돈처럼 실제 생활 표현으로 씁니다.",
    "확실해집니다": "'확실해집니다'가 반복되면 기계적 강조로 읽힙니다. 정해집니다, 드러납니다, 인정받습니다처럼 맥락에 맞게 씁니다.",
    "잡히며": "'잡히며'가 반복되면 조립 문장처럼 읽힙니다. 정해지며, 분명해지며, 나뉘며처럼 씁니다.",
    "인정받는 일에서 인정받을 일이": "같은 뜻의 말을 한 문장 안에서 겹쳐 상담문 흐름이 어색합니다.",
    "인정을 받는 일에서 인정받을 일이": "같은 뜻의 말을 한 문장 안에서 겹쳐 상담문 흐름이 어색합니다.",
    "사회적 인정받을": "조사가 빠져 한국어 문장이 깨집니다. '사회적 인정을 받을'처럼 씁니다.",
    "믿고 따르는 힘": "사람을 도구적으로 다루는 표현처럼 들립니다. 신뢰를 주는 힘처럼 씁니다.",
    "구간은 행동으로 옮길 만한 때": "구간과 때가 겹쳐 명사 호응이 어색합니다.",
    "일이 강해지는 구간에는": "사건명 뒤에 '강해지는 구간'을 붙이면 조립 문장처럼 보입니다.",
    "일이 강한 달에는": "사건명 뒤에 '강한 달'을 붙이면 조립 문장처럼 보입니다.",
    "일이 가장 유리합니다": "'일이 가장 유리하다'는 주어와 서술어의 결속이 약합니다. 좋은 기회, 좋은 결과처럼 결론을 직접 말해야 합니다.",
    "먼저 크게 나타납니다": "강조어가 붙었지만 장면이 흐립니다. 무엇이 먼저 커지는지, 무엇이 달라지는지 직접 말해야 합니다.",
    "중요한 선택도 함께 달라집니다": "선택이 달라진다는 말만으로는 고객이 체감할 장면이 부족합니다. 돈, 일, 관계 중 무엇이 달라지는지 나누어 말해야 합니다.",
    "실제 변화가 같이 생깁니다": "'실제 변화'와 '같이 생깁니다'가 겹쳐 조립 문장처럼 들립니다.",
    "업무 범위가 넓어지는 일이 강해지는": "사건명과 시기 설명이 겹쳐 한국어 호흡이 무너집니다.",
    "권한 문제도 커집니다": "좋은 직업운을 말하는 자리에서 권한을 문제로만 키우면 결론이 불필요하게 부정적으로 들립니다.",
    "인정받을 자리가 커집니다": "자리가 커진다는 말보다 인정받을 자리가 생긴다, 넓어진다처럼 실제 결과를 말해야 합니다.",
    "피해야 할 업무 조건": "상품 문장에서는 조건보다 환경, 자리, 업무 방식처럼 실제 장면으로 말하는 편이 자연스럽습니다.",
    "직업운의 이익": "직업운은 이익보다 인정, 보상, 부담처럼 실제 결과로 말해야 자연스럽습니다.",
    "거리감이가": "명리 키워드에 조사가 한 번 더 붙은 형태입니다. '거리감이'처럼 한 번만 붙여야 합니다.",
    "결혼 논의 진전": "고객 문장에서는 딱딱한 내부 라벨처럼 들립니다. 결혼 이야기, 결혼 이야기가 구체화된다처럼 씁니다.",
    "신중하게 다뤄야 하는 영역입니다": "완충하려는 의도는 보이지만 의미가 흐립니다. 아직 강하게 자리한 편은 아닙니다처럼 상태를 분명히 말합니다.",
    "결혼 이야기가 결혼 이야기": "같은 말을 반복해 붙인 조립문입니다. 결혼 이야기가 구체화된다처럼 바로 말해야 합니다.",
    "결혼 준비가 결혼 이야기": "사건명과 상위 라벨이 겹친 조립문입니다. 결혼 준비가 구체화된다처럼 말해야 합니다.",
    "결혼 논의가 늦어집니다": "'논의가 늦어진다'는 보고서식입니다. 결혼 이야기가 늦어진다, 결혼 준비가 늦어진다처럼 고객 장면으로 말합니다.",
    "결혼 논의가 무거워집니다": "'논의가 무거워진다'는 딱딱합니다. 결혼 이야기가 무거워진다처럼 생활 언어로 낮춥니다.",
    "가족 논의가 커집니다": "가족 논의가 커진다는 호응이 약합니다. 가족 이야기가 본격적으로 나온다처럼 씁니다.",
    "결혼 이야기가 늦어집니다": "결혼 이야기 자체보다 결혼 준비나 약속이 늦어지는 결과를 말해야 합니다.",
    "결혼 이야기를 늦춥니다": "결혼 이야기를 늦춘다는 표현은 헐겁습니다. 결혼 준비를 늦춘다처럼 실제 결과로 말합니다.",
    "결혼 이야기가 무거워집니다": "이야기가 무거워진다는 표현보다 결혼 준비에 부담이 커진다고 말하는 편이 또렷합니다.",
    "결혼 이야기가 다시 멈춥니다": "이야기가 멈춘다는 말보다 결혼 준비가 다시 멈춘다고 말하는 편이 명확합니다.",
    "감정의 확신만으로 끝나는 일이 아닙니다": "부정형 해설문이라 상담 도입이 무겁습니다. 감정의 확신보다 생활의 약속으로 더 크게 다가온다처럼 긍정형으로 말합니다.",
    "함께 논의됩니다": "수동 보고서식 표현입니다. 함께 정리됩니다, 따로 말하게 됩니다처럼 실제 장면으로 말합니다.",
    "결혼 이야기를 무겁게 만듭니다": "사건이 이야기를 무겁게 만든다는 표현은 딱딱합니다. 결혼 이야기를 늦춘다처럼 결과를 직접 말합니다.",
    "결혼 논의 진전이 커질수록": "'논의 진전이 커진다'는 한국어 호응이 약합니다. 결혼 이야기가 구체화된다처럼 씁니다.",
    "결혼 논의에서 커집니다": "결혼 논의라는 장면과 '커집니다'가 헐겁게 붙어 조립 문장처럼 읽힙니다.",
    "기대치를 말로 정리하는 일이 커집니다": "추상 사건을 '커집니다'로 받으면 어색합니다. 기대치를 말로 정리하게 된다처럼 씁니다.",
    "연락과 만남 문제로 커집니다": "연애 장면이 아니라 조립된 사건명처럼 읽힙니다. 연락과 만남에서 먼저 보인다처럼 씁니다.",
    "약속과 생활 문제로 커집니다": "결혼 장면이 아니라 조립된 문제명처럼 읽힙니다. 약속과 생활의 중심이 된다처럼 씁니다.",
    "문제로 커집니다": "'문제로 커진다'는 호응이 어색합니다. 문제로 나타난다, 부담이 커진다, 먼저 다루게 된다처럼 씁니다.",
    "생활 안으로 들어옵니다": "직역투에 가깝습니다. 생활에 영향을 준다, 생활에서 다루게 된다처럼 씁니다.",
    "한결 드러납니다": "'한결'과 '드러나다'의 결합이 어색합니다. 구체화됩니다, 뚜렷해집니다처럼 씁니다.",
    "직업 현장에서 먼저 나타납니다": "직업운에서는 나타난다는 설명보다 업무 범위가 넓어진다, 평가 방식이 달라진다처럼 사건을 말해야 합니다.",
    "관계 안에서 먼저 나타납니다": "관계운에서는 나타난다는 설명보다 감정 충돌이 생긴다, 연락 방식이 달라진다처럼 사건을 말해야 합니다.",
    "결혼 문제로 먼저 드러납니다": "결혼운에서는 문제로 드러난다는 말보다 결혼 논의의 중심이 된다, 준비로 넘어간다처럼 상담 장면을 말해야 합니다.",
    "부부 생활을 꾸리는 방식에서 안정감과 부담이 함께 나타납니다": "안정감과 부담이 함께 나타난다는 말은 보고서식입니다. 안정이 커지는 이유와 부담이 커지는 장면을 나누어 말합니다.",
    "더 큰 역할로 이어집니다": "'이어집니다'가 반복되면 기계적으로 들립니다. 다음 역할도 맡게 된다처럼 실제 결과를 말합니다.",
    "년에는 재물운의 중심은": "시기 부사와 주제 조사가 겹칩니다. '2026년 재물운의 중심은'처럼 씁니다.",
    "년에는 직업운의 중심은": "시기 부사와 주제 조사가 겹칩니다. '2026년 직업운의 중심은'처럼 씁니다.",
    "년에는 연애운의 중심은": "시기 부사와 주제 조사가 겹칩니다. '2026년 연애운의 중심은'처럼 씁니다.",
    "년에는 결혼운의 중심은": "시기 부사와 주제 조사가 겹칩니다. '2026년 결혼운의 중심은'처럼 씁니다.",
    "결혼 준비가가": "명리 키워드에 조사가 한 번 더 붙은 형태입니다. '결혼 준비가'처럼 한 번만 붙여야 합니다.",
    "먼저 이뤄집니다": "상담 문장에서는 이뤄진다는 보고보다 실제로 무엇을 말하고 선택하는지 써야 합니다.",
    "올해 애정운은 연락에서 달라집니다": "'연락에서 달라집니다'보다 연락 방식, 만남의 간격처럼 대상을 밝혀야 자연스럽습니다.",
    "마음의 선택이 빨라집니다": "연애 상담문에서는 선택보다 감정이 드러나는 양상을 말하는 편이 자연스럽습니다.",
    "돈의 약속": "고객 문장에서는 정산 약속, 지급일, 받을 돈처럼 실제 표현으로 말해야 합니다.",
    "돈을 받는 기준과 나눌 몫이 느슨해": "지급 기준이 느슨하다는 내부 평가어보다 받을 금액과 나눌 몫을 흐리게 둔다처럼 장면을 말해야 합니다.",
    "지급 조건과 나눌 몫이 느슨해": "지급 조건이 느슨하다는 내부 평가어보다 받을 금액과 나눌 몫을 흐리게 둔다처럼 장면을 말해야 합니다.",
    "돈을 쓰는 방식에서 먼저 드러납니다": "돈을 쓰는 방식과 '먼저 드러납니다'가 붙으면 보고서식입니다. 돈을 쓰는 이유를 보면 성향이 보인다고 말하는 편이 자연스럽습니다.",
    "돈을 쓰는 방식를": "후처리 치환으로 조사가 깨진 문장입니다. '돈을 쓰는 이유를 보면'처럼 문장 전체를 다시 써야 합니다.",
    "성향은 돈을 쓰는 이유를 보면 성향이": "같은 문장 안에서 성향을 두 번 받아 어색합니다. 어떤 사람인지 바로 말해야 합니다.",
    "성향은 돈을 쓰는 방식를 보면 성향이": "후처리 치환과 의미 반복이 함께 생긴 문장입니다. 어떤 사람인지 바로 말해야 합니다.",
    "정보 판단도": "'정보 판단도 예민합니다'처럼 붙으면 번역투에 가깝습니다. 정보를 민감하게 판단합니다, 정보 판단 능력처럼 씁니다.",
    "정보를 민감하게 판단합니다": "정보를 판단한다는 결합은 딱딱합니다. 정보 변화에도 민감하게 반응합니다처럼 씁니다.",
    "돈 이야기가 함께 달라집니다": "돈 이야기가 달라진다는 말은 흐립니다. 돈을 받는 방식, 지출 기준, 정산 문제처럼 실제 장면을 말합니다.",
    "힘이 강해질 때": "축 이름이 고객 문장에 그대로 들어간 형태입니다. 기질이 뚜렷해진다, 기준이 분명해진다처럼 문장화합니다.",
    "중요한 동력이 됩니다": "상담문에서는 동력보다 신뢰를 중요하게 본다, 기준이 된다처럼 사람의 태도를 말합니다.",
    "평가의 무게도 커집니다": "평가의 무게라는 결합은 다소 추상적입니다. 책임도 커집니다, 기대도 커집니다처럼 실제 부담을 말합니다.",
    "집 문제를 진지하게 봅니다": "결혼 상담문에서는 집 문제보다 주거 문제가 자연스럽습니다.",
    "태도가 먼저 드러납니다": "연애와 관계 상담에서는 태도가 먼저 드러난다는 말보다 태도가 먼저 나온다, 마음을 숨기기 어렵다처럼 장면을 말해야 합니다.",
    "맡는 역할이 드러납니다": "직업 문장에서는 역할이 드러난다보다 맡는 역할이 분명해진다, 새 역할을 맡게 된다고 말해야 합니다.",
    "가장 먼저 보이고": "보고서식 연결입니다. 한 문장에 하나의 결론만 두고, 두드러진다처럼 끊어 말해야 합니다.",
    "초반부터 크게 잡히는 편은 아니어서": "상품 문장에서는 소극적 설명보다 아직 크게 강한 영역은 아니다처럼 바로 말해야 합니다.",
    "기대하는 관계 속도는 초기에 드러납니다": "관계의 속도가 드러난다는 말은 어색합니다. 서로 원하는 속도가 보인다처럼 말해야 합니다.",
    "기대하는 관계의 속도는 초기에 드러납니다": "관계의 속도가 드러난다는 말은 어색합니다. 서로 원하는 속도가 보인다처럼 말해야 합니다.",
    "보상과 정산에서 받을 돈이 정해집니다": "받을 돈이 정해진다는 말은 계약서 설명처럼 딱딱합니다. 받을 돈이 보인다, 확정된다처럼 맥락에 맞춰야 합니다.",
    "프로젝트 정산 금액도 이 시기에 정해집니다": "정산 금액은 정해진다보다 확정된다, 마무리된다가 자연스럽습니다.",
    "기준이 드러": "기준은 드러난다기보다 세워지거나 분명해집니다.",
    "조건이 드러": "조건은 드러난다기보다 확인되거나 정리됩니다.",
    "가능성이 드러": "가능성은 드러난다기보다 커지거나 열립니다. 운세 문장에서는 사건을 먼저 말해야 합니다.",
    "역할이 드러": "역할은 드러난다기보다 맡게 되거나 커집니다.",
    "방식이 드러": "방식은 드러난다기보다 보이거나 달라집니다.",
    "수입을 자산으로 남기는 방식이 드러납니다": "방식이 드러난다는 보고서식입니다. 들어온 돈을 자산으로 남기려 한다처럼 사람의 행동으로 말합니다.",
    "결과물이 보이면 인정도 빨라집니다": "조건문이 설명서처럼 읽힙니다. 결과물이 쌓이며 인정도 빨라진다고 말합니다.",
    "업무 범위가 넓어지는 구간에는": "구간이라는 말은 운세 상담문에서 딱딱합니다. 업무 범위가 넓어지는 때라고 말합니다.",
    "행동으로 옮길 일이 생깁니다": "무엇을 행동으로 옮기는지 흐립니다. 미뤄 둔 일을 처리하게 됩니다처럼 실제 장면을 말합니다.",
    "별도 문제로 커집니다": "문제로 커진다는 호응이 어색합니다. 따로 부담으로 남는다고 말합니다.",
    "생활 방식에서 결론이 납니다": "본문 설명 자리에 들어가면 결론형 조립문처럼 보입니다. 생활 방식이 더 중요해진다고 말합니다.",
    "자연스럽게 따라옵니다": "'따라옵니다'는 결과가 흐립니다. 더 큰 역할을 맡게 된다, 평가가 빨라진다처럼 직접 말합니다.",
    "빠르게 따라옵니다": "'따라옵니다'는 결과가 흐립니다. 평가가 빨라진다처럼 직접 말합니다.",
    "책임 있는 자리도 따라옵니다": "책임 있는 자리가 따라온다는 말은 흐립니다. 책임 있는 자리도 맡게 된다고 말합니다.",
    "직업운의 중심은 맡는 역할입니다": "내부 라벨처럼 읽힙니다. 맡는 역할이 분명해진다고 말합니다.",
    "나뉘어 드러납니다": "나뉘어 드러난다는 말은 보고서식입니다. 갈립니다, 나뉩니다처럼 바로 말합니다.",
    "현실적인 사건으로 드러납니다": "현실적인 사건으로 드러난다는 말은 내부 분석어처럼 들립니다. 실제로 다루게 된다고 말합니다.",
    "생활 방식의 차이가 먼저 드러납니다": "관계 갈등 장면에서는 드러난다보다 차이가 커진다고 말하는 편이 자연스럽습니다.",
    "정서적으로 기대는 방식도 드러납니다": "가정운 문장에서는 방식이 드러난다보다 기대는 방식이 분명해진다고 말합니다.",
    "이 운에서 가장 크게 드러납니다": "이론 근거 문장이라도 보고서식으로 굳습니다. 이 운의 중심을 잡는다고 말합니다.",
    "가장 먼저 드러납니다": "고객 문장에서는 먼저 보게 됩니다, 먼저 다루게 됩니다처럼 사람의 판단으로 말합니다.",
    "반복되는 문제로 이어집니다": "문제로 이어진다는 말은 흐립니다. 반복해서 다루게 된다고 말합니다.",
    "중요한 문제가 됩니다": "'중요한 문제'는 추상적입니다. 실제로 무엇이 달라지는지 바로 말해야 합니다.",
    "무게가 큽니다": "상담문에서는 무게가 크다는 말보다 계속 중요해진다, 부담이 커진다처럼 장면을 말합니다.",
    "약속의 선": "관계 상담문에서는 약속의 선보다 관계의 기준, 거리감의 기준이 자연스럽습니다.",
    "평가로 연결": "연결된다는 말은 흐립니다. 평가받는 근거가 된다, 인정받는 자리로 바뀐다처럼 결과를 직접 말합니다.",
    "인정도 따릅니다": "'따릅니다'는 결과가 약하게 들립니다. 인정받을 자리도 생긴다고 말합니다.",
    "재물운의 결론입니다": "고객 문장에서는 결론 명사보다 손에 남는 돈이 중요해진다고 말하는 편이 자연스럽습니다.",
    "까지에는": "날짜 구간 뒤에는 '까지는'이 자연스럽습니다. '까지에는'은 불필요하게 꺾입니다.",
    "일 분명합니다": "사건명 뒤에는 조사가 필요합니다. '일이 분명합니다'처럼 씁니다.",
    "일 가장 뚜렷합니다": "사건명 뒤에는 조사가 필요합니다. '일이 가장 뚜렷합니다'처럼 씁니다.",
    "일 매우 뚜렷합니다": "사건명 뒤에는 조사가 필요합니다. '일이 매우 뚜렷합니다'처럼 씁니다.",
    "현금 변화": "상담문에서는 현금 변화보다 돈이 오가는 변화, 돈의 움직임이 자연스럽습니다.",
    "현금 이동": "상담문에서는 현금 이동보다 수입과 지출 시점, 돈이 오가는 변화가 자연스럽습니다.",
    "업무 정보 이동": "업무 정보 이동은 기계적으로 보입니다. 업무 정보와 보상 기준처럼 말합니다.",
    "사회적 판단": "사회적 판단은 추상적입니다. 사회적 평가, 평판, 돈의 기준처럼 장면을 말합니다.",
    "중요한 비중": "'중요하다'와 '비중'이 겹쳐 어색합니다.",
    "비중이 커집니다": "고객 문장에서는 보고서식 표현보다 '더 크게 봅니다', '더 중요해집니다'가 자연스럽습니다.",
    "같이 깊고 얕": "해석의 층위를 직접 말하면 상담문보다 분석 설명처럼 보입니다.",
    "함께 읽을 때": "고객 리포트에서는 분석 방법보다 실제 결론을 먼저 말해야 합니다.",
    "의 안정됩니다": "'마음의 안정됩니다'처럼 명사구와 서술어가 붙으면 한국어 문장이 깨집니다.",
}

ASSEMBLED_GRAMMAR_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(r"(?:재물|직업|연애|관계|결혼|성향|건강)에서는 [^.!?。！？]{1,48}에서는"),
        "에서는 ... 에서는",
        "같은 문장 안에서 '에서는'이 두 번 반복되어 조건명과 서술이 어색하게 붙습니다.",
    ),
    (
        re.compile(r"[가-힣]+의 안정됩니다|[가-힣]+의 [가-힣]{1,12}됩니다"),
        "의 ... 됩니다",
        "명사형 표현을 줄이는 과정에서 조사와 서술어가 맞지 않습니다.",
    ),
)

CONDITION_ESCAPE_MARKERS = (
    "조건에 따라",
    "조건이 맞으면",
    "조건이 맞을 때",
    "경우에 따라",
    "좋을 수 있습니다",
    "좋아질 수 있습니다",
    "가능합니다",
)

INSTRUCTIONAL_POSITIVE_CONDITION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(잡히면|맞추면|정리되면|분명하면|세워지면|보이면)"
        r"[^.!?。！？]{0,28}"
        r"(돈이 남|이익으로 남|관계가 안정|관계도 오래|재물운이 안정|"
        r"손에 남는 돈|인정도 빨라|마음도 오래|오해가 줄|결혼 논의도 앞으로)"
    ),
)

NEGATED_IDENTITY_OPENINGS = (
    "당신은 돈 자체에만 집착하는 사람은 아닙니다",
    "당신은 사랑을 가볍게 보는 사람은 아닙니다",
    "당신은 감정만으로 움직이기보다",
    "당신은 인생을 쉽게 흘려보내는 사람이라기보다",
)

CODE_REGISTER_MARKERS = (
    "프레임",
    "레이어",
    "프로파일",
    "분석 축",
    "축 점수",
    "체크포인트",
    "패턴",
    "스코어",
    "템플릿",
)

AI_SLOPE_MARKERS = (
    "흐름",
    "리듬",
    "패턴",
    "판",
    "통로",
)


def natural_korean_issues(text: str) -> list[NaturalKoreanIssue]:
    """Return naturalness issues detected in a customer-facing sentence."""
    compact = " ".join(str(text).split())
    if not compact:
        return []

    issues: list[NaturalKoreanIssue] = []
    issues.extend(_translation_style_issues(compact))
    issues.extend(_passive_report_issues(compact))
    issues.extend(_abstract_density_issues(compact))
    issues.extend(_weak_subject_predicate_issues(compact))
    issues.extend(_awkward_collocation_issues(compact))
    issues.extend(_assembled_grammar_issues(compact))
    issues.extend(_condition_escape_issues(compact))
    issues.extend(_instructional_positive_condition_issues(compact))
    issues.extend(_negated_identity_issues(compact))
    issues.extend(_code_register_issues(compact))
    issues.extend(_multi_core_sentence_issues(compact))
    issues.extend(_ai_slope_issues(compact))
    return _dedupe_issues(issues)


def natural_korean_score(text: str) -> int:
    """Return a 0-100 readability-naturalness score for one sentence."""
    issues = natural_korean_issues(text)
    penalty = sum(issue.severity for issue in issues)
    return max(0, 100 - penalty)


def natural_korean_summary(texts: list[str]) -> dict[str, object]:
    """Summarize natural Korean issues for a group of sentences."""
    issues: list[NaturalKoreanIssue] = []
    scores: list[int] = []
    for text in texts:
        if not str(text).strip():
            continue
        current = natural_korean_issues(text)
        issues.extend(current)
        scores.append(max(0, 100 - sum(issue.severity for issue in current)))

    counts = Counter(issue.code for issue in issues)
    marker_counts = Counter(issue.marker for issue in issues)
    return {
        "policy_version": NATURAL_KOREAN_POLICY_VERSION,
        "sentence_count": len(scores),
        "issue_count": len(issues),
        "issue_counts": dict(counts.most_common()),
        "marker_counts_top": dict(marker_counts.most_common(30)),
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
    }


def _translation_style_issues(text: str) -> list[NaturalKoreanIssue]:
    return [
        NaturalKoreanIssue(
            "translation_style",
            marker,
            9,
            "번역투 조사와 표현은 한국어 문장의 힘을 약하게 만듭니다.",
            "조사를 줄이고, 주어와 동사가 바로 맞물리는 문장으로 바꿉니다.",
        )
        for marker in TRANSLATION_STYLE_MARKERS
        if marker in text
    ]


def _passive_report_issues(text: str) -> list[NaturalKoreanIssue]:
    return [
        NaturalKoreanIssue(
            "passive_report_ending",
            marker,
            7,
            "상태를 보고하는 서술은 운세 상담의 확신을 약하게 만듭니다.",
            "주어를 사람이나 실제 사건으로 바꾸고 능동 동사를 씁니다.",
        )
        for marker in PASSIVE_REPORT_ENDINGS
        if marker in text
    ]


def _abstract_density_issues(text: str) -> list[NaturalKoreanIssue]:
    abstract_count = sum(text.count(marker) for marker in ABSTRACT_NOUNS)
    scene_count = sum(text.count(marker) for marker in SCENE_NOUNS)
    if abstract_count >= 3 and scene_count == 0:
        return [
            NaturalKoreanIssue(
                "abstract_without_scene",
                str(abstract_count),
                12,
                "추상 명사가 많고 생활 장면이 없으면 독자가 자기 이야기로 받아들이기 어렵습니다.",
                "돈, 일, 연락, 생활비처럼 손에 잡히는 명사를 한 문장 안에 넣습니다.",
            )
        ]
    if abstract_count >= 5:
        return [
            NaturalKoreanIssue(
                "abstract_density",
                str(abstract_count),
                8,
                "추상 명사가 한 문장에 몰리면 설명문처럼 굳어집니다.",
                "추상어를 다음 문장으로 나누고 실제 행동이나 장면을 붙입니다.",
            )
        ]
    return []


def _weak_subject_predicate_issues(text: str) -> list[NaturalKoreanIssue]:
    issues: list[NaturalKoreanIssue] = []
    for subject in WEAK_ABSTRACT_SUBJECTS:
        for ending in PASSIVE_REPORT_ENDINGS:
            if re.search(rf"{re.escape(subject)}[은는이가] [^.!?。！？]{{0,32}}{re.escape(ending)}", text):
                issues.append(
                    NaturalKoreanIssue(
                        "weak_subject_passive_predicate",
                        f"{subject}+{ending}",
                        12,
                        "추상 주어와 수동 서술이 붙으면 한국어 상담 문장으로 어색해집니다.",
                        "주어를 실제 사람, 돈, 일, 연락, 가족 문제로 바꿉니다.",
                    )
                )
    return issues


def _awkward_collocation_issues(text: str) -> list[NaturalKoreanIssue]:
    return [
        NaturalKoreanIssue(
            "awkward_collocation",
            marker,
            11,
            reason,
            "명사와 서술어가 한국어에서 자연스럽게 붙는지 다시 맞춥니다.",
        )
        for marker, reason in AWKWARD_COLLOCATIONS.items()
        if marker in text
    ]


def _assembled_grammar_issues(text: str) -> list[NaturalKoreanIssue]:
    return [
        NaturalKoreanIssue(
            "assembled_grammar_break",
            marker,
            13,
            reason,
            "조립된 조건명은 조사까지 포함해 다시 문장으로 다듬습니다.",
        )
        for pattern, marker, reason in ASSEMBLED_GRAMMAR_PATTERNS
        if pattern.search(text)
    ]


def _condition_escape_issues(text: str) -> list[NaturalKoreanIssue]:
    issues: list[NaturalKoreanIssue] = []
    for marker in CONDITION_ESCAPE_MARKERS:
        if marker not in text:
            continue
        severity = 12 if marker.startswith("조건") else 5
        issues.append(
            NaturalKoreanIssue(
                "conditional_escape",
                marker,
                severity,
                "조건부 표현이 많으면 상담서가 결론을 피하는 글처럼 보입니다.",
                "운세 결론을 먼저 말하고 보완 설명은 다음 문장으로 분리합니다.",
            )
        )
    return issues


def _instructional_positive_condition_issues(text: str) -> list[NaturalKoreanIssue]:
    issues: list[NaturalKoreanIssue] = []
    for pattern in INSTRUCTIONAL_POSITIVE_CONDITION_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        issues.append(
            NaturalKoreanIssue(
                "instructional_positive_condition",
                match.group(0),
                8,
                "'잡히면 좋아진다' 식 문장은 운세 상담보다 사용 설명서처럼 읽힙니다.",
                "조건문을 줄이고, 실제로 정해지는 일과 그 결과를 진행형으로 말합니다.",
            )
        )
    return issues


def _negated_identity_issues(text: str) -> list[NaturalKoreanIssue]:
    return [
        NaturalKoreanIssue(
            "negated_identity_opening",
            marker,
            8,
            "부정으로 시작하는 성향 문장은 유형을 확정하지 못한다는 인상을 줍니다.",
            "당신이 어떤 사람인지 먼저 긍정형으로 규정합니다.",
        )
        for marker in NEGATED_IDENTITY_OPENINGS
        if text.startswith(marker)
    ]


def _code_register_issues(text: str) -> list[NaturalKoreanIssue]:
    return [
        NaturalKoreanIssue(
            "code_register_leak",
            marker,
            10,
            "개발 내부 용어가 고객 문장에 남으면 리포트의 몰입이 깨집니다.",
            "서비스 화면에서는 생활어와 상담어로 바꿉니다.",
        )
        for marker in CODE_REGISTER_MARKERS
        if marker in text
    ]


def _multi_core_sentence_issues(text: str) -> list[NaturalKoreanIssue]:
    comma_like_count = text.count(",") + text.count("·") + text.count("/")
    connective_count = sum(text.count(marker) for marker in ("그리고", "또한", "동시에", "함께", "뿐 아니라"))
    if len(text) >= 60 and comma_like_count + connective_count >= 3:
        return [
            NaturalKoreanIssue(
                "multi_core_sentence",
                f"len={len(text)}",
                9,
                "한 문장 안에 핵심이 여러 개 들어가면 독자가 결론을 놓칩니다.",
                "한 문장에는 하나의 핵심만 담고 나머지는 다음 문장으로 보냅니다.",
            )
        ]
    return []


def _ai_slope_issues(text: str) -> list[NaturalKoreanIssue]:
    issues: list[NaturalKoreanIssue] = []
    for marker in AI_SLOPE_MARKERS:
        if marker == "판":
            found = bool(re.search(r"(?:^|[\s'\"“‘])판(?:[은는이가을를도에]|$)", text))
        else:
            found = marker in text
        if not found:
            continue
        issues.append(
            NaturalKoreanIssue(
                "ai_sounding_metaphor",
                marker,
                11,
                "상용 AI 문장처럼 보이는 비유는 신뢰도를 떨어뜨립니다.",
                "구체적인 사건, 행동, 생활 묘사로 바꿉니다.",
            )
        )
    return issues


def _dedupe_issues(issues: list[NaturalKoreanIssue]) -> list[NaturalKoreanIssue]:
    seen: set[tuple[str, str]] = set()
    deduped: list[NaturalKoreanIssue] = []
    for issue in issues:
        key = (issue.code, issue.marker)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped
