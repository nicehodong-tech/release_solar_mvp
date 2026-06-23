# Saju Birth Engine

명식 산출 엔진은 운세 분석 엔진보다 먼저 안정화해야 하는 선행 모듈이다.

## 역할

```text
출생정보
-> 양력/음력 정규화
-> 출생지와 시간대 처리
-> 진태양시 보정
-> 연월일시주 산출
-> 대운 산출
-> 경계 민감도와 계산 추적값 반환
```

## 현재 구현 범위

- 대한민국 주요 도시 좌표 기본 제공
- 한국 표준시와 1987/1988년 DST 처리
- 1954~1961년 UTC+08:30 처리
- Windows/.NET `KoreanLunisolarCalendar` 기반 한국 음력 변환 어댑터
- Meeus 기반 태양 황경 계산으로 입춘/절기 경계 산출
- 진태양시 보정
- 연주, 월주, 일주, 시주 산출
- 대운 순역과 시작 나이 산출
- 지장간과 십신 기본 산출
- 계산 추적값 `calculation_trace` 반환

## 검증

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest discover -s tests
$env:PYTHONIOENCODING='utf-8'; python scripts/verify_birth_engine.py
```

첫 기준 케이스는 다음이며, `scripts/verify_birth_engine.py`는 이 값이 어긋나면 실패한다.

```text
남자, 1999-12-12 양력, 07:10, 대한민국 춘천
명식: 己卯년 丙子월 戊戌일 乙卯시
진태양시: 1999-12-12T06:46
경계 민감도: hour
```

현재 경계 검증은 입춘, 12개 월주 절입 전체, 진태양시 자정, 시지 전환, 한국 음력 윤달, 대운 순역, 절기 직후 빠른 대운 시작, 대운 시작 나이 환산, 대운 간지 진행 방향을 포함한다.

외부 만세력 대조는 `tests/external_manse_reference.json`과 `tests/test_external_manse_reference.py`에 고정했다. 현재 날짜별 연월일주와 음력/윤달 변환은 외부 표와 일치하며, 절입 시각은 최대 약 11.133분 차이로 15분 허용 범위 안에서 관리한다.
