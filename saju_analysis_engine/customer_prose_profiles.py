"""Customer-facing prose profiles for report rendering.

This module keeps prose that product editors are likely to patch away from the
report renderer. The analysis engine should not depend on these sentences.
"""

from __future__ import annotations


DOMAIN_READING_WRITING = {
    "money": {
        "lead_tail": "보상과 정산에서 받을 돈이 보입니다.",
        "main_conclusion": "이 시기에는 대가가 정해집니다. 받을 돈도 보입니다. 지급 시점이 정해질수록 손에 남는 돈이 커집니다.",
        "action_opening": "이 시기에는",
        "action_result": "들어오는 돈은 흩어지지 않고 자산으로 남습니다.",
        "risk_opening": "반대로",
        "risk_result": "그럴수록 실제로 손에 쥐는 금액이 줄어듭니다.",
        "axis_opening": "당신의 선천적인 재물운에서는",
        "axis_result": "재물운은 들어온 돈을 남기는 방식에서 강합니다. 받을 돈과 남길 돈이 구분될수록 자산이 쌓입니다.",
        "timing_result": "이 기간에는 받을 돈이 먼저 정리됩니다. 나갈 돈도 따로 계산됩니다. 남길 돈은 처음부터 분리됩니다.",
        "closing": "이 해의 재물운은 수입이 손에 남는 운입니다. 돈을 받는 방식이 정해지고, 들어온 돈을 지켜내는 절차가 세워지면서 손에 남는 금액이 커집니다.",
    },
    "career": {
        "lead_tail": "인정받을 자리도 생깁니다.",
        "main_conclusion": "이 시기에는 책임 범위가 커지며 직업운의 부담도 함께 커집니다. 평가 방식도 새로 잡습니다. 권한이 분명한 자리에서 인정받습니다.",
        "action_opening": "이 시기에는",
        "action_result": "맡은 일은 좋은 평가로 이어집니다.",
        "risk_opening": "반대로",
        "risk_result": "그럴수록 일을 해내고도 부담이 먼저 남습니다.",
        "axis_opening": "당신의 선천적인 직업운에서는",
        "axis_result": "직업운은 결과가 확인되는 자리에서 강합니다. 맡은 역할이 분명할수록 인정도 빨라집니다.",
        "timing_result": "이 기간에는 업무 범위가 먼저 넓어집니다. 결정권도 분명해집니다. 결정권이 분명할수록 성취도 커집니다.",
        "closing": "이 해의 직업운은 해낸 일로 평가를 받는 운입니다. 책임만 커지는 자리는 부담으로 남고, 권한과 보상이 분명한 자리에서는 맡는 역할도 커집니다.",
    },
    "love": {
        "lead_tail": "마음의 거리와 연락 태도가 달라집니다.",
        "main_conclusion": "이 시기에는 연락 방식에 따라 연애운이 달라집니다. 말투도 관계의 분위기를 바꿉니다. 만남의 속도가 맞을 때 관계가 오래 갑니다.",
        "action_opening": "이 시기에는",
        "action_result": "마음은 상대에게 부담이 아니라 호감으로 전달됩니다.",
        "risk_opening": "반대로",
        "risk_result": "그럴수록 마음이 깊어도 불편함이 반복됩니다.",
        "axis_opening": "당신의 관계 성향을 함께 보면",
        "axis_result": "편안한 거리와 대화의 속도가 맞춰지면서 관계가 오래 안정됩니다.",
        "timing_result": "이 기간에는 연락 간격을 말로 정리하게 됩니다. 만남의 빈도도 맞춰집니다. 초기에 서로 원하는 속도가 보입니다.",
        "closing": "이 해의 연애운은 관계를 정리하고 앞으로 나아가는 운입니다. 마음만 앞서면 불편함이 생기고, 연락 방식과 기대치가 맞아 가면 관계가 가까워집니다.",
    },
    "marriage": {
        "lead_tail": "결혼과 생활 방식을 두고 현실적인 이야기가 시작됩니다.",
        "main_conclusion": "이 시기에는 돈의 기준이 결혼 생활을 바로 안정시킵니다. 주거 문제도 결혼 이야기의 핵심이 됩니다. 가족과의 거리는 따로 정리됩니다.",
        "action_opening": "이 시기에는",
        "action_result": "약속은 말로 끝나지 않고 생활의 약속으로 굳어집니다.",
        "risk_opening": "반대로",
        "risk_result": "그럴수록 사랑의 깊이와 별개로 생활의 안정이 늦어집니다.",
        "axis_opening": "당신의 결혼과 가정 성향을 함께 보면",
        "axis_result": "감정의 확신이 생활의 약속으로 옮겨질 때 결혼운이 안정됩니다.",
        "timing_result": "이 기간에는 생활비 이야기가 본격적으로 오갑니다. 주거 계획도 따로 세워집니다. 가족과의 거리는 늦게 정리하면 부담이 커집니다.",
        "closing": "이 해의 결혼운은 생활비와 책임 분담이 정리되면서 안정됩니다. 결혼을 미루거나 당기는 문제보다, 두 사람이 생활 방식을 맞춰 가는 과정에서 결혼 생활이 오래 갑니다.",
    },
}
