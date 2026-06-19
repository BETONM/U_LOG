# P - Plan: Calendar 팝업 헤더 깨짐 + Analysis 직접모드 노치 가림 수정

Status: completed

## Goal
유로그(avoha) 프론트의 두 가지 UI 결함을 수정한다.
1. Calendar 날짜 클릭 시 뜨는 기록 팝업에서, 스크롤할 때 날짜 헤더 위쪽이 살짝 깨지는 현상 제거.
2. Analysis(감정 분석) "직접" 기간 모드에서, 맨 위 날짜 범위 텍스트가 데스크탑 미리보기 목업의 노치에 가려지는 현상 제거.

## Source requirements
- 사용자 리포트 1: "캘린더 페이지에서 날짜 클릭하면 뜨는 팝업이 날짜는 항상 맨 위에 오게 의도했는데, 스크롤할 때 날짜 위에 부분이 살짝 깨지는 현상."
- 사용자 리포트 2: "감정 분석 페이지에서 주간/월간은 상관없는데, 직접으로 들어가면 내용이 너무 길어서 맨 위 날짜 부분이 목업에 가려져. 아예 한칸씩 내리는 느낌이 좋을까?"

## Approach
1. A 단계에서 `frontend/src/routes/Calendar.tsx`, `frontend/src/routes/Analysis.tsx`, `frontend/src/App.tsx`, `frontend/src/styles/theme.css` 를 읽어 sticky 헤더 구조와 phone-frame 노치 구조를 매핑한다.
2. Calendar: sticky 헤더 위에 따로 흐르는 grip/패딩과 둥근 모서리 클립 이음새를 원인으로 보고, grip 을 헤더에 통합 + panel top padding 제거 + 헤더 모서리 radius 정렬로 수정.
3. Analysis: 헤더 top 패딩이 노치(콘텐츠 상단 ~36px)보다 작아 생기는 문제로 보고, Calendar 와 동일하게 상단 패딩으로 노치를 피운다(사용자가 제안한 "한칸 내리기").
4. 기존 export 헬퍼/테스트를 깨지 않도록 `Calendar.test.ts` 의 sticky 헤더 기대값을 먼저 확인.
5. 변경 후 vitest + tsc + 프로덕션 build 로 검증, dev 서버 스모크.

## Non-goals
- Calendar/Analysis 외 화면 리팩터링.
- 노치 클리어 수치의 픽셀 단위 디자인 합의 (40px 기본값으로 두되 추후 미세조정 여지 남김).
- 사용자가 요청하지 않은 push/deploy — (단, 본 작업은 이후 사용자가 명시적으로 "배포 가자" 요청하여 배포 수행됨. D 참고)
