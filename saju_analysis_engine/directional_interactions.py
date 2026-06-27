"""Directional element and stem interaction base values.

This layer preserves the difference between "A and B are present" and
"A sees B". Later ten-god and seasonal layers should adjust these base values,
not replace them.
"""

from __future__ import annotations

from itertools import permutations
from typing import Any

from saju_birth_engine.models import BirthChartResult

from .constants import (
    BRANCH_HIDDEN_STEMS,
    ELEMENT_CONTROLS,
    ELEMENT_GENERATES,
    POSITION_BRANCH_WEIGHTS,
    POSITION_STEM_WEIGHTS,
    STEM_METADATA,
)
from .models import DirectionalInteractionProfile, DirectionalInteractionSignal


POSITION_ORDER = ("year", "month", "day", "hour")
STEM_ORDER = ("gap", "eul", "byeong", "jeong", "mu", "gi", "gyeong", "sin", "im", "gye")
ELEMENT_ORDER = ("wood", "fire", "earth", "metal", "water")
SERVICE_DOMAINS = ("money", "career", "love", "marriage")

STEM_HANJA = {
    "gap": "甲",
    "eul": "乙",
    "byeong": "丙",
    "jeong": "丁",
    "mu": "戊",
    "gi": "己",
    "gyeong": "庚",
    "sin": "辛",
    "im": "壬",
    "gye": "癸",
}

ELEMENT_HANJA = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}


def _rule(keywords: list[str], interpretation: str) -> dict[str, Any]:
    return {"trait_keywords": keywords, "interpretation": interpretation}


ELEMENT_DIRECTION_RULES: dict[tuple[str, str], dict[str, Any]] = {
    ("wood", "wood"): _rule(["성장 반복", "협력과 경쟁", "분산"], "木이 木을 보면 성장 욕구가 반복됩니다. 협력도 되지만 경쟁과 분산도 함께 생깁니다."),
    ("wood", "fire"): _rule(["자기 증명", "사회 참여", "발표"], "木이 火를 보면 성장한 것을 보여주고 인정받으려 합니다. 발표, 사회 참여, 자기 증명의 성향입니다."),
    ("wood", "earth"): _rule(["현실 적응", "자기계발", "환경 선택"], "木이 土를 보면 가능성을 현실 조건에 맞추려 합니다. 적응, 자기계발, 환경 선택으로 이어집니다."),
    ("wood", "metal"): _rule(["평가", "교정", "선발"], "木이 金을 보면 성장성이 기준과 검증을 받습니다. 평가, 교정, 압박, 선발의 성향입니다."),
    ("wood", "water"): _rule(["학습", "준비", "충전"], "木이 水를 보면 지식과 자원을 받아 성장합니다. 학습, 준비, 충전의 성향입니다."),
    ("fire", "wood"): _rule(["표현 근거", "이력", "설득 재료"], "火가 木을 보면 표현의 근거가 생깁니다. 사람, 이력, 경험, 설득 재료를 얻습니다."),
    ("fire", "fire"): _rule(["노출 확대", "인정 욕구", "과열"], "火가 火를 보면 표현과 노출이 강해집니다. 인정 욕구, 경쟁, 과열이 생깁니다."),
    ("fire", "earth"): _rule(["표현 검토", "설득력", "논리성"], "火가 土를 보면 표현이 현실적으로 검토됩니다. 설득력, 논리성, 검수가 중요한 기준입니다."),
    ("fire", "metal"): _rule(["성과 노출", "브랜딩", "인정"], "火가 金을 보면 결과물이나 인물을 조명합니다. 성과 노출, 브랜딩, 인정의 성향입니다."),
    ("fire", "water"): _rule(["판단력", "해석", "기획"], "火가 水를 보면 정보와 현상을 종합해 판단합니다. 해석, 기획, 시비 판단의 성향입니다."),
    ("earth", "wood"): _rule(["등용", "관리", "적합성 판단"], "土가 木을 보면 환경이 가능성, 인재, 요청을 받습니다. 등용, 관리, 적합성 판단으로 이어집니다."),
    ("earth", "fire"): _rule(["메시지 해석", "사회적 반응", "자기 점검"], "土가 火를 보면 표현과 의도를 인식합니다. 메시지 해석, 사회적 반응, 자기 점검이 중요한 기준입니다."),
    ("earth", "earth"): _rule(["현실 인식 반복", "안정 욕구", "무거운 판단"], "土가 土를 보면 현실 인식이 반복됩니다. 안정성은 크지만 생각이 무거워질 수 있습니다."),
    ("earth", "metal"): _rule(["가치 책정", "규칙", "품질 판단"], "土가 金을 보면 가치와 가격을 책정합니다. 규칙, 제도, 품질, 결과 판단의 성향입니다."),
    ("earth", "water"): _rule(["정보 관리", "시장 인식", "분석"], "土가 水를 보면 정보, 돈, 시장, 감정을 인식하고 붙잡습니다. 관리, 분석, 유통 판단의 성향입니다."),
    ("metal", "wood"): _rule(["선별", "교정", "가치 판단"], "金이 木을 보면 가능성을 자르고 검증합니다. 선별, 교정, 가치 판단의 성향입니다."),
    ("metal", "fire"): _rule(["조명", "제련", "성과화"], "金이 火를 보면 결과물이 조명되거나 기술로 다뤄집니다. 노출, 제련, 성과화의 성향입니다."),
    ("metal", "earth"): _rule(["숙성", "신뢰", "등급화"], "金이 土를 보면 결과가 현실적 근거와 가격을 얻습니다. 숙성, 신뢰, 등급화의 성향입니다."),
    ("metal", "metal"): _rule(["기준 반복", "완성도", "경직"], "金이 金을 보면 기준과 완성도가 반복됩니다. 날카롭지만 경직될 수 있습니다."),
    ("metal", "water"): _rule(["보존", "유통", "전승"], "金이 水를 보면 결과를 보존하고 전달합니다. 기록, 유통, 전승, 정보화의 성향입니다."),
    ("water", "wood"): _rule(["교육", "공급", "고객 대응"], "水가 木을 보면 지식과 자원을 전달해 성장시킵니다. 교육, 공급, 고객 대응의 성향입니다."),
    ("water", "fire"): _rule(["전략", "해석", "전망"], "水가 火를 보면 정보가 현상과 만나 의미를 만듭니다. 전략, 해석, 전망의 성향입니다."),
    ("water", "earth"): _rule(["정리", "문서화", "현실 적용"], "水가 土를 보면 정보가 경로와 기준을 얻습니다. 정리, 문서화, 현실 적용의 성향입니다."),
    ("water", "metal"): _rule(["근거", "출처", "선별 기준"], "水가 金을 보면 정보가 근거와 출처를 얻습니다. 깊이, 원본성, 선별 기준이 중요합니다."),
    ("water", "water"): _rule(["사유 심화", "감수성", "실행 지연"], "水가 水를 보면 정보와 감수성이 깊어집니다. 사유는 깊지만 실행은 늦어질 수 있습니다."),
}


STEM_DIRECTION_RULES: dict[tuple[str, str], dict[str, Any]] = {
    ("gap", "gap"): _rule(["성장 경쟁", "자기 기준", "독립성"], "甲이 甲을 보면 독립 성장성이 반복되어 자기 기준과 성장 경쟁이 강해집니다."),
    ("gap", "eul"): _rule(["관계 확장", "세부 요청", "분산"], "甲이 乙을 보면 주변 관계와 세부 요청이 붙습니다. 성장 범위는 넓어지나 분산될 수 있습니다."),
    ("gap", "byeong"): _rule(["사회 참여", "실력 입증", "자기 증명"], "甲이 丙을 보면 자신을 보여줄 기회를 얻습니다. 사회 참여와 실력 입증의 성향입니다."),
    ("gap", "jeong"): _rule(["전문 고도화", "자격", "연구"], "甲이 丁을 보면 실용 지식과 기술을 고도화합니다. 자격, 연구, 신체 활용으로 이어집니다."),
    ("gap", "mu"): _rule(["자기계발", "대외 적합성", "시대 요구"], "甲이 戊를 보면 시대에 맞는 인재인지 확인합니다. 자기계발과 대외 적합성이 중요합니다."),
    ("gap", "gi"): _rule(["적응", "등용", "훈련"], "甲이 己를 보면 자기 수준을 내부 환경에 맞춥니다. 적응, 등용, 훈련의 성향입니다."),
    ("gap", "gyeong"): _rule(["실적 압박", "교정", "선발"], "甲이 庚을 보면 강한 기준과 실적 압박을 받습니다. 교정, 선발, 책임으로 이어집니다."),
    ("gap", "sin"): _rule(["세부 교정", "이미지 보완", "포장"], "甲이 辛을 보면 책잡히고 다듬어집니다. 포장, 이미지 보완, 세부 교정의 성향입니다."),
    ("gap", "im"): _rule(["실리", "고객", "활용 자원"], "甲이 壬을 보면 필요한 정보와 자원을 얻습니다. 실리, 고객, 활용 자원과 관련됩니다."),
    ("gap", "gye"): _rule(["교육", "이론", "내면 성숙"], "甲이 癸를 보면 지식과 지혜를 배워 성장합니다. 교육, 이론, 내면 성숙의 성향입니다."),
    ("eul", "gap"): _rule(["상승 기준", "후원", "큰 조직"], "乙이 甲을 보면 의지할 큰 기준이나 체계를 만납니다. 상승 기준, 후원, 큰 조직으로 이어집니다."),
    ("eul", "eul"): _rule(["관계 민감성", "협업", "분산"], "乙이 乙을 보면 관계 민감성이 반복됩니다. 협업력은 생기지만 분산도 커질 수 있습니다."),
    ("eul", "byeong"): _rule(["관계망 확장", "교류", "조직 결속"], "乙이 丙을 보면 관계망을 넓히고 도움을 받습니다. 교류, 친화성, 조직 결속의 성향입니다."),
    ("eul", "jeong"): _rule(["특수 분야", "세밀한 전문성", "연구"], "乙이 丁을 보면 특수 분야를 깊게 파고듭니다. 연구와 세밀한 전문성이 강해집니다."),
    ("eul", "mu"): _rule(["보좌", "매뉴얼 대응", "큰 틀 처리"], "乙이 戊를 보면 관계적 요구를 큰 틀에서 처리합니다. 보좌와 매뉴얼 대응의 성향입니다."),
    ("eul", "gi"): _rule(["서비스", "클레임", "세부 조율"], "乙이 己를 보면 개별 문제를 직접 해결합니다. 서비스, 클레임, 세부 조율에 강합니다."),
    ("eul", "gyeong"): _rule(["외부 구조", "명령", "생존 구조"], "乙이 庚을 보면 외부 구조와 명령을 받습니다. 고용, 편입, 생존 구조와 관련됩니다."),
    ("eul", "sin"): _rule(["편집", "관계 정리", "실력 압박"], "乙이 辛을 보면 불필요한 것을 잘라냅니다. 편집, 관계 정리, 실력 압박의 성향입니다."),
    ("eul", "im"): _rule(["제휴", "스카우트", "인맥 비즈니스"], "乙이 壬을 보면 사람과 사람을 연결합니다. 제휴, 스카우트, 인맥 비즈니스에 강합니다."),
    ("eul", "gye"): _rule(["상담", "처세", "심리 조율"], "乙이 癸를 보면 관계를 읽는 지혜가 생깁니다. 상담, 처세, 심리적 조율의 성향입니다."),
    ("byeong", "gap"): _rule(["표현 재료", "이력", "사회적 실력"], "丙이 甲을 보면 드러낼 인재와 성장 재료를 얻습니다. 사회적 실력 입증의 성향입니다."),
    ("byeong", "eul"): _rule(["팀", "관계망", "설득"], "丙이 乙을 보면 팀과 관계망을 얻습니다. 사람을 모으고 설득하려 합니다."),
    ("byeong", "byeong"): _rule(["노출 확대", "인정 욕구", "대외성"], "丙이 丙을 보면 노출과 인정 욕구가 확대됩니다. 대외성이 강해집니다."),
    ("byeong", "jeong"): _rule(["목적과 실행", "표현", "전문성"], "丙이 丁을 보면 큰 목적과 세부 실행이 함께 생깁니다. 표현과 전문성이 결합됩니다."),
    ("byeong", "mu"): _rule(["강연", "운영", "대외 설득"], "丙이 戊를 보면 말이 장소와 청중을 얻습니다. 강연, 운영, 대외 설득의 성향입니다."),
    ("byeong", "gi"): _rule(["자기 점검", "논리 보완", "영역 구축"], "丙이 己를 보면 표현을 내부적으로 점검합니다. 자기 영역 구축과 논리 보완이 중요한 기준입니다."),
    ("byeong", "gyeong"): _rule(["실행", "결단", "성과 압박"], "丙이 庚을 보면 목적을 결과로 만들 재료를 다룹니다. 실행, 결단, 성과 압박의 성향입니다."),
    ("byeong", "sin"): _rule(["브랜딩", "인정", "집중 효과"], "丙이 辛을 보면 완성된 대상을 조명합니다. 브랜딩, 인정, 집중 효과가 강해집니다."),
    ("byeong", "im"): _rule(["큰 기획", "시비 판단", "실리와 명분"], "丙이 壬을 보면 실리와 명분을 함께 판단합니다. 큰 기획과 시비 판단의 성향입니다."),
    ("byeong", "gye"): _rule(["관찰", "설명", "감성 표현"], "丙이 癸를 보면 현상을 섬세하게 해석합니다. 관찰, 설명, 감성 표현에 강합니다."),
    ("jeong", "gap"): _rule(["전문 실력", "자격", "훈련"], "丁이 甲을 보면 절대적 지식과 기술을 고도화합니다. 자격, 훈련, 전문 실력으로 이어집니다."),
    ("jeong", "eul"): _rule(["심층 전공", "개별 경험", "세밀한 연구"], "丁이 乙을 보면 특수하고 세밀한 분야를 연구합니다. 심층 전공과 개별 경험이 강해집니다."),
    ("jeong", "byeong"): _rule(["대중성", "확대", "표현 강화"], "丁이 丙을 보면 전문성이 대중성을 만납니다. 더 넓게 보이려는 성향입니다."),
    ("jeong", "jeong"): _rule(["전문 몰입", "기술 집중", "예민성"], "丁이 丁을 보면 전문 몰입이 반복됩니다. 기술 집중은 강하지만 예민성도 커질 수 있습니다."),
    ("jeong", "mu"): _rule(["시장 적합성", "재교육", "기술 검토"], "丁이 戊를 보면 기술이 시대에 맞는지 검토됩니다. 재교육, 재활, 시장 적합성의 성향입니다."),
    ("jeong", "gi"): _rule(["실무 현장", "품질", "수준 확인"], "丁이 己를 보면 자기 기술 수준을 확인합니다. 연구소, 공장, 실무 현장의 성향입니다."),
    ("jeong", "gyeong"): _rule(["개발", "생산", "R&D"], "丁이 庚을 보면 기술을 물질적 성과로 만듭니다. 개발, 생산, R&D에 강합니다."),
    ("jeong", "sin"): _rule(["리폼", "A/S", "개선"], "丁이 辛을 보면 완성품을 보완하고 다시 살립니다. 리폼, A/S, 개선의 성향입니다."),
    ("jeong", "im"): _rule(["관리", "계획", "지식 사업"], "丁이 壬을 보면 전문성을 실용 정보로 연결합니다. 관리, 계획, 지식 사업에 적합합니다."),
    ("jeong", "gye"): _rule(["정밀 분석", "창작", "감수성"], "丁이 癸를 보면 섬세한 감수성과 기술이 결합됩니다. 연구, 창작, 정밀 분석의 성향입니다."),
    ("mu", "gap"): _rule(["평가", "자기계발", "적합성 판단"], "戊가 甲을 보면 시대에 필요한 인재인지 봅니다. 평가, 자기계발, 적합성 판단의 성향입니다."),
    ("mu", "eul"): _rule(["민원", "보좌", "대외 조율"], "戊가 乙을 보면 관계적 요청을 사회적으로 처리합니다. 민원, 보좌, 대외 조율에 강합니다."),
    ("mu", "byeong"): _rule(["여론", "강연", "조직 운영"], "戊가 丙을 보면 메시지와 목적을 받아들입니다. 여론, 강연, 조직 운영과 관련됩니다."),
    ("mu", "jeong"): _rule(["시장성", "기술 검토", "재교육"], "戊가 丁을 보면 기술이 시대에 맞는지 봅니다. 시장성, 재교육, 기술 검토의 성향입니다."),
    ("mu", "mu"): _rule(["대외 인식 과중", "객관화", "무거운 판단"], "戊가 戊를 보면 대외 인식이 과중해집니다. 객관화는 강하지만 판단이 무거워질 수 있습니다."),
    ("mu", "gi"): _rule(["외부와 내부 조정", "자기 사정", "객관화"], "戊가 己를 보면 외부 인식과 내부 인식이 만납니다. 객관화와 자기 사정의 조정이 중요합니다."),
    ("mu", "gyeong"): _rule(["법규", "제도", "집행"], "戊가 庚을 보면 규칙을 세우고 집행합니다. 법규, 제도, 모범성의 성향입니다."),
    ("mu", "sin"): _rule(["상품 평가", "객관적 가치", "가격"], "戊가 辛을 보면 완성품의 가격을 봅니다. 객관적 가치와 상품 평가의 성향입니다."),
    ("mu", "im"): _rule(["시장", "투자", "외부 기회"], "戊가 壬을 보면 큰 시장과 돈을 봅니다. 유행, 투자, 외부 기회와 관련됩니다."),
    ("mu", "gye"): _rule(["객관화", "문화 분석", "사회적 언어"], "戊가 癸를 보면 감수성을 사회적 언어로 설명합니다. 객관화와 문화 분석의 성향입니다."),
    ("gi", "gap"): _rule(["채용", "훈련", "용병술"], "己가 甲을 보면 인재를 환경에 맞게 길러 씁니다. 채용, 훈련, 용병술의 성향입니다."),
    ("gi", "eul"): _rule(["서비스", "돌봄", "개별 해결"], "己가 乙을 보면 관계 문제를 세밀하게 처리합니다. 서비스, 돌봄, 개별 해결에 강합니다."),
    ("gi", "byeong"): _rule(["자기완성", "내부 논리", "표현 점검"], "己가 丙을 보면 자기 표현을 점검합니다. 자기완성과 내부 논리 보완의 성향입니다."),
    ("gi", "jeong"): _rule(["품질", "실무", "연구 공간"], "己가 丁을 보면 기술의 실제 수준을 확인합니다. 품질, 실무, 연구 공간과 관련됩니다."),
    ("gi", "mu"): _rule(["자기 객관화", "외부 평가", "내부 사정"], "己가 戊를 보면 내부 사정과 외부 평가를 맞춥니다. 자기 객관화가 중요한 기준입니다."),
    ("gi", "gi"): _rule(["내부 점검 과중", "성찰", "세부 관리"], "己가 己를 보면 내부 점검이 과중해집니다. 성찰과 세부 관리는 강하지만 부담도 커집니다."),
    ("gi", "gyeong"): _rule(["자기 평가", "생산 관리", "기준"], "己가 庚을 보면 자기 상품의 기준과 값을 정합니다. 자기 평가, 생산 관리의 성향입니다."),
    ("gi", "sin"): _rule(["숙성", "전시", "브랜드 이야기"], "己가 辛을 보면 완성품에 서사를 입힙니다. 숙성, 전시, 브랜드 이야기의 성향입니다."),
    ("gi", "im"): _rule(["내부 데이터", "안정 재물", "정보 정리"], "己가 壬을 보면 큰 정보를 자기 방식으로 정리합니다. 내부 데이터와 안정 재물에 관련됩니다."),
    ("gi", "gye"): _rule(["심리", "감성 표현", "세부 기억"], "己가 癸를 보면 감정을 세밀하게 인식합니다. 일기, 심리, 감성 표현의 성향입니다."),
    ("gyeong", "gap"): _rule(["가치 판단", "원인 파악", "검증"], "庚이 甲을 보면 가능성을 검증하고 바로잡습니다. 가치 판단과 원인 파악의 성향입니다."),
    ("gyeong", "eul"): _rule(["명령", "고용", "관리"], "庚이 乙을 보면 관계를 지시 체계에 넣습니다. 명령, 고용, 관리의 성향입니다."),
    ("gyeong", "byeong"): _rule(["성과 지향", "실행 방향", "조명"], "庚이 丙을 보면 목적과 조명을 받아 실행 방향을 얻습니다. 성과 지향이 강해집니다."),
    ("gyeong", "jeong"): _rule(["생산", "개발", "가공"], "庚이 丁을 보면 재료가 기술을 만나 상품화됩니다. 생산, 개발, 가공의 성향입니다."),
    ("gyeong", "mu"): _rule(["법", "제도", "집행 기준"], "庚이 戊를 보면 규범과 근거를 얻습니다. 법, 제도, 집행 기준과 관련됩니다."),
    ("gyeong", "gi"): _rule(["자기 상품 평가", "내부 기준", "가격"], "庚이 己를 보면 내부 기준으로 가치를 책정합니다. 자기 상품 평가의 성향입니다."),
    ("gyeong", "gyeong"): _rule(["기준 과잉", "결단", "경직"], "庚이 庚을 보면 기준과 결단이 반복됩니다. 판단력은 강하지만 경직될 수 있습니다."),
    ("gyeong", "sin"): _rule(["고급화", "정밀 기준", "재분류"], "庚이 辛을 보면 재료와 완성품이 대비됩니다. 고급화와 정밀 기준의 성향입니다."),
    ("gyeong", "im"): _rule(["선별", "보존", "유통"], "庚이 壬을 보면 남길 것을 정해 전달합니다. 선별, 보존, 유통의 성향입니다."),
    ("gyeong", "gye"): _rule(["법 해석", "이론", "분석"], "庚이 癸를 보면 규칙과 경험을 지식화합니다. 법 해석, 이론, 분석에 강합니다."),
    ("sin", "gap"): _rule(["포장", "브랜딩", "특장점 부각"], "辛이 甲을 보면 대상을 보기 좋게 만듭니다. 포장, 브랜딩, 특장점 부각의 성향입니다."),
    ("sin", "eul"): _rule(["절취", "편집", "구조조정"], "辛이 乙을 보면 불필요한 것을 제거합니다. 절취, 편집, 구조조정의 성향입니다."),
    ("sin", "byeong"): _rule(["인정", "노출", "상징성"], "辛이 丙을 보면 조명을 받아 우수성이 확인됩니다. 인정, 노출, 상징성의 성향입니다."),
    ("sin", "jeong"): _rule(["리폼", "수리", "업그레이드"], "辛이 丁을 보면 보완과 재구성을 받습니다. 리폼, 수리, 업그레이드의 성향입니다."),
    ("sin", "mu"): _rule(["시장 평가", "가치 책정", "가격"], "辛이 戊를 보면 객관적 가격을 얻습니다. 시장 평가와 가치 책정의 성향입니다."),
    ("sin", "gi"): _rule(["전시", "큐레이션", "감성 상품화"], "辛이 己를 보면 서사와 숙성을 얻습니다. 전시, 큐레이션, 감성 상품화의 성향입니다."),
    ("sin", "gyeong"): _rule(["순도", "검수", "재분류"], "辛이 庚을 보면 완성품이 강한 기준을 만납니다. 순도, 검수, 재분류의 성향입니다."),
    ("sin", "sin"): _rule(["완성도 집착", "세공", "상품성"], "辛이 辛을 보면 완성도 집착이 강해집니다. 세공과 상품성은 좋지만 예민해질 수 있습니다."),
    ("sin", "im"): _rule(["판매", "유통", "마케팅"], "辛이 壬을 보면 시장에 나갑니다. 판매, 유통, 마케팅의 성향입니다."),
    ("sin", "gye"): _rule(["예술", "평론", "기록"], "辛이 癸를 보면 독자적 감수성으로 해석됩니다. 예술, 평론, 기록에 강합니다."),
    ("im", "gap"): _rule(["고객", "수요", "공급"], "壬이 甲을 보면 고객과 수요를 만납니다. 필요한 물건과 정보를 공급하는 성향입니다."),
    ("im", "eul"): _rule(["스카우트", "제휴", "매니지먼트"], "壬이 乙을 보면 관계와 인재를 거래하고 연결합니다. 스카우트, 제휴, 매니지먼트에 강합니다."),
    ("im", "byeong"): _rule(["전략", "판단", "실리와 명분"], "壬이 丙을 보면 실리와 명분을 비교합니다. 큰 계획, 판단, 전략의 성향입니다."),
    ("im", "jeong"): _rule(["관리", "문서화", "실무 지성"], "壬이 丁을 보면 정보가 전문 기술로 정리됩니다. 관리, 문서화, 실무 지성의 성향입니다."),
    ("im", "mu"): _rule(["트렌드 분석", "유행", "거시 분석"], "壬이 戊를 보면 시장이 대외 조건으로 파악됩니다. 동향, 유행, 거시 분석의 성향입니다."),
    ("im", "gi"): _rule(["정보 관리", "고객 관리", "내부 정리"], "壬이 己를 보면 정보가 자기 영역 안에서 정리됩니다. 정보 관리, 고객 관리의 성향입니다."),
    ("im", "gyeong"): _rule(["출처", "원본성", "보존 가치"], "壬이 庚을 보면 정보의 출처와 기준을 얻습니다. 선별, 원본성, 보존 가치가 중요합니다."),
    ("im", "sin"): _rule(["상품", "판매", "유통 수완"], "壬이 辛을 보면 팔 수 있는 완성품을 만납니다. 상품, 판매, 유통 수완의 성향입니다."),
    ("im", "im"): _rule(["정보 과다", "시장성", "변동성"], "壬이 壬을 보면 정보와 시장성이 과다해집니다. 변동성이 커질 수 있습니다."),
    ("im", "gye"): _rule(["사유", "해석", "과민"], "壬이 癸를 보면 방대한 정보가 감수성으로 깊어집니다. 사유와 해석은 깊지만 과민도 생깁니다."),
    ("gye", "gap"): _rule(["교육", "학습", "기초 실력"], "癸가 甲을 보면 지식이 성장으로 이어집니다. 교육, 학습, 기초 실력의 성향입니다."),
    ("gye", "eul"): _rule(["상담", "처세", "관계 전략"], "癸가 乙을 보면 관계를 섬세하게 읽습니다. 상담, 처세, 관계 전략에 강합니다."),
    ("gye", "byeong"): _rule(["관찰", "표현", "설명"], "癸가 丙을 보면 내면의 해석이 밖으로 확인됩니다. 관찰, 표현, 설명의 성향입니다."),
    ("gye", "jeong"): _rule(["연구", "창작", "진단"], "癸가 丁을 보면 감수성이 전문 분석으로 들어갑니다. 연구, 창작, 진단에 강합니다."),
    ("gye", "mu"): _rule(["묘사", "기사화", "사회적 설명"], "癸가 戊를 보면 감정이 사회적 언어로 객관화됩니다. 묘사, 기사화, 설명의 성향입니다."),
    ("gye", "gi"): _rule(["일기", "심리", "기억"], "癸가 己를 보면 감정이 개인의 세부 체험으로 남습니다. 일기, 심리, 기억의 성향입니다."),
    ("gye", "gyeong"): _rule(["법", "철학", "이론 분석"], "癸가 庚을 보면 감수성이 규칙과 법칙을 해석합니다. 법, 철학, 이론 분석에 강합니다."),
    ("gye", "sin"): _rule(["예술성", "평론", "섬세한 취향"], "癸가 辛을 보면 독특한 경험과 미감을 얻습니다. 예술성, 평론, 섬세한 취향의 성향입니다."),
    ("gye", "im"): _rule(["깊은 이해", "큰 정보", "생각 과다"], "癸가 壬을 보면 개인 감수성이 큰 정보와 만납니다. 깊은 이해가 되지만 생각이 많아질 수 있습니다."),
    ("gye", "gye"): _rule(["감수성 과다", "생각", "내면성"], "癸가 癸를 보면 감수성과 생각이 과다해집니다. 내면성은 깊지만 실행은 늦어질 수 있습니다."),
}


def _birth_time_unknown(chart: BirthChartResult) -> bool:
    return bool(getattr(chart, "calculation_trace", {}).get("birth_time_unknown"))


def _pillars(chart: BirthChartResult):
    pillars = {
        "year": chart.year_pillar,
        "month": chart.month_pillar,
        "day": chart.day_pillar,
    }
    if not _birth_time_unknown(chart):
        pillars["hour"] = chart.hour_pillar
    return pillars


def _position_sort_key(position: str) -> int:
    base = position.split(":", 1)[0]
    return POSITION_ORDER.index(base) if base in POSITION_ORDER else 99


def _direction_type(source_element: str, target_element: str) -> str:
    if source_element == target_element:
        return "same_element"
    if ELEMENT_GENERATES[source_element] == target_element:
        return "source_generates_target"
    if ELEMENT_GENERATES[target_element] == source_element:
        return "target_generates_source"
    if ELEMENT_CONTROLS[source_element] == target_element:
        return "source_controls_target"
    if ELEMENT_CONTROLS[target_element] == source_element:
        return "target_controls_source"
    return "mixed"


def element_direction_rule(source_element: str, target_element: str) -> dict[str, Any]:
    return ELEMENT_DIRECTION_RULES[(source_element, target_element)]


def stem_direction_rule(source_stem: str, target_stem: str) -> dict[str, Any]:
    return STEM_DIRECTION_RULES[(source_stem, target_stem)]


def _strength_from_entries(source_entry: dict[str, Any], target_entry: dict[str, Any]) -> str:
    if source_entry["source"] == "visible" and target_entry["source"] == "visible":
        return "high"
    if source_entry["source"] == "visible" or target_entry["source"] == "visible":
        return "moderate"
    weight = float(source_entry.get("weight", 0.0)) + float(target_entry.get("weight", 0.0))
    return "moderate" if weight >= 1.1 else "low"


def _domain_links(source_position: str, target_position: str) -> list[str]:
    position_domains = {
        "year": ["career", "love"],
        "month": ["career", "money"],
        "day": ["love", "marriage"],
        "hour": ["career", "money", "marriage"],
    }
    domains: list[str] = []
    for position in (source_position, target_position):
        base = position.split(":", 1)[0]
        domains.extend(position_domains.get(base, []))
    return [domain for domain in SERVICE_DOMAINS if domain in set(domains)]


def _entry_sort_key(entry: dict[str, Any]) -> tuple[int, str, str]:
    return (_position_sort_key(str(entry["position"])), str(entry["source"]), str(entry["stem"]))


def _signal(
    *,
    layer: str,
    source_entry: dict[str, Any],
    target_entry: dict[str, Any],
    signal_suffix: str,
) -> DirectionalInteractionSignal:
    source_stem = str(source_entry["stem"])
    target_stem = str(target_entry["stem"])
    source_element = str(STEM_METADATA[source_stem]["element"])
    target_element = str(STEM_METADATA[target_stem]["element"])
    direction_key = f"{source_stem}->{target_stem}"
    element_direction_key = f"{source_element}->{target_element}"
    stem_rule = stem_direction_rule(source_stem, target_stem)
    element_rule = element_direction_rule(source_element, target_element)
    direction_type = _direction_type(source_element, target_element)
    source_position = str(source_entry["position"])
    target_position = str(target_entry["position"])
    basis_codes = [
        f"directional_{layer}_{source_stem}_{target_stem}",
        f"directional_element_{source_element}_{target_element}",
        f"directional_type_{direction_type}",
    ]
    return DirectionalInteractionSignal(
        signal_id=f"directional_{layer}_{signal_suffix}_{source_stem}_to_{target_stem}",
        layer=layer,
        direction_key=direction_key,
        element_direction_key=element_direction_key,
        direction_type=direction_type,
        source_position=source_position,
        target_position=target_position,
        source_stem=source_stem,
        target_stem=target_stem,
        source_branch=str(source_entry.get("branch", "")),
        target_branch=str(target_entry.get("branch", "")),
        source_element=source_element,
        target_element=target_element,
        source_rule="directional_stem_base_v1",
        strength=_strength_from_entries(source_entry, target_entry),
        domain_links=_domain_links(source_position, target_position),
        basis_codes=basis_codes,
        counter_signals=[],
        trait_keywords=list(stem_rule["trait_keywords"]),
        interpretation=str(stem_rule["interpretation"]),
        element_interpretation=str(element_rule["interpretation"]),
    )


def _visible_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        entries.append(
            {
                "position": f"{position}:stem",
                "source": "visible",
                "stem": pillar.stem_key,
                "branch": pillar.branch_key,
                "weight": POSITION_STEM_WEIGHTS[position],
            }
        )
    return entries


def _hidden_entries(chart: BirthChartResult) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for position, pillar in _pillars(chart).items():
        for index, (stem_key, hidden_weight) in enumerate(BRANCH_HIDDEN_STEMS[pillar.branch_key]):
            entries.append(
                {
                    "position": f"{position}:hidden:{index}",
                    "source": "hidden",
                    "stem": stem_key,
                    "branch": pillar.branch_key,
                    "weight": POSITION_BRANCH_WEIGHTS[position] * hidden_weight,
                }
            )
    return entries


def _directional_pair_signals(
    *,
    layer: str,
    entries: list[dict[str, Any]],
    limit: int | None = None,
) -> list[DirectionalInteractionSignal]:
    signals: list[DirectionalInteractionSignal] = []
    ordered_entries = sorted(entries, key=_entry_sort_key)
    for index, (source_entry, target_entry) in enumerate(permutations(ordered_entries, 2), start=1):
        signals.append(
            _signal(
                layer=layer,
                source_entry=source_entry,
                target_entry=target_entry,
                signal_suffix=f"2_{index}",
            )
        )
    return _dedupe_signals(signals, limit=limit)


def _stem_branch_signals(chart: BirthChartResult) -> list[DirectionalInteractionSignal]:
    signals: list[DirectionalInteractionSignal] = []
    for position, pillar in _pillars(chart).items():
        hidden_stem_key = BRANCH_HIDDEN_STEMS[pillar.branch_key][0][0]
        stem_entry = {
            "position": f"{position}:stem",
            "source": "visible",
            "stem": pillar.stem_key,
            "branch": pillar.branch_key,
            "weight": POSITION_STEM_WEIGHTS[position],
        }
        branch_entry = {
            "position": f"{position}:branch_main",
            "source": "hidden",
            "stem": hidden_stem_key,
            "branch": pillar.branch_key,
            "weight": POSITION_BRANCH_WEIGHTS[position],
        }
        signals.append(_signal(layer="stem_branch", source_entry=stem_entry, target_entry=branch_entry, signal_suffix=f"{position}_stem_to_branch"))
        signals.append(_signal(layer="stem_branch", source_entry=branch_entry, target_entry=stem_entry, signal_suffix=f"{position}_branch_to_stem"))
    return _dedupe_signals(signals)


def _signal_rank(signal: DirectionalInteractionSignal) -> tuple[int, int, int, int]:
    layer_rank = {"heavenly_stem": 0, "stem_branch": 1, "hidden_stem": 2}.get(signal.layer, 3)
    strength_rank = {"high": 0, "moderate": 1, "low": 2}.get(signal.strength, 3)
    position_rank = min(_position_sort_key(signal.source_position), _position_sort_key(signal.target_position))
    domain_rank = -len(signal.domain_links)
    return (layer_rank, strength_rank, position_rank, domain_rank)


def _dedupe_signals(
    signals: list[DirectionalInteractionSignal],
    limit: int | None = None,
) -> list[DirectionalInteractionSignal]:
    deduped: list[DirectionalInteractionSignal] = []
    seen: set[tuple[str, str, str, str]] = set()
    for signal in sorted(signals, key=_signal_rank):
        key = (signal.layer, signal.direction_key, signal.source_position, signal.target_position)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(signal)
        if limit is not None and len(deduped) >= limit:
            break
    return deduped


def _summary_sentences(signals: list[DirectionalInteractionSignal]) -> list[str]:
    selected = sorted(signals, key=_signal_rank)[:5]
    sentences: list[str] = []
    for signal in selected:
        source = STEM_HANJA[signal.source_stem]
        target = STEM_HANJA[signal.target_stem]
        keywords = ", ".join(signal.trait_keywords[:3])
        sentences.append(f"당신의 원국에서 {source}이 {target}을 보는 기본값은 다음과 같습니다. {signal.interpretation} 핵심 특성은 {keywords}입니다.")
    return sentences


def iter_directional_interaction_signals(profile: DirectionalInteractionProfile) -> list[DirectionalInteractionSignal]:
    return (
        list(profile.heavenly_stem_signals)
        + list(profile.stem_branch_signals)
        + list(profile.hidden_stem_signals)
    )


def build_directional_interaction_profile(chart: BirthChartResult) -> DirectionalInteractionProfile:
    visible_entries = _visible_entries(chart)
    hidden_entries = _hidden_entries(chart)
    heavenly_stem_signals = _directional_pair_signals(layer="heavenly_stem", entries=visible_entries)
    stem_branch_signals = _stem_branch_signals(chart)
    hidden_stem_signals = _directional_pair_signals(layer="hidden_stem", entries=hidden_entries, limit=36)
    all_signals = _dedupe_signals(heavenly_stem_signals + stem_branch_signals + hidden_stem_signals)
    top_signal_ids = [signal.signal_id for signal in sorted(all_signals, key=_signal_rank)[:12]]
    return DirectionalInteractionProfile(
        heavenly_stem_signals=heavenly_stem_signals,
        hidden_stem_signals=hidden_stem_signals,
        stem_branch_signals=stem_branch_signals,
        top_signal_ids=top_signal_ids,
        summary_sentences=_summary_sentences(all_signals),
    )
