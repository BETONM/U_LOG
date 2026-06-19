# P - Plan: Analysis 기간 라벨을 "6월 2째주"/"6월" 형식으로

Status: completed

## Goal
감정 분석 탭 상단 기간 라벨(eyebrow)을 주간/월간 선택 시 "이번 주"/"이번 달" 대신
"6월 2째주"/"6월" 처럼 실제 달·주차로 표시한다.

## Source requirements
- 사용자 요청: "주간/월간을 하면 이번주/이번달으로 뜨는데 6월 2째주, 6월 이런식으로 수정 가능할까? 가능하면 수정+배포, 불가능하면 이유만."

## Approach
1. A 단계에서 `periodLabel` 생성/사용 위치 매핑 (단일 지점인지 확인).
2. 가능하면 순수 헬퍼 `formatAnalysisPeriodLabel` 로 분리하고 테스트(RED-GREEN) 추가.
3. 주차 계산은 Calendar 의 일요일 시작 달력과 동일하게 `ceil((날짜 + 그달 1일의 요일)/7)`.
4. vitest + tsc + build 검증 후 사용자 요청대로 main 푸시 배포.

## Non-goals
- custom(직접) 라벨 포맷 변경 (기존 날짜 범위 유지).
- 주차 한국어 표기 컨벤션 논쟁 — 사용자가 제시한 "N째주" 표기를 그대로 따른다.
