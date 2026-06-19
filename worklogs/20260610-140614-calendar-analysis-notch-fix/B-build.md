# B - Build

Status: completed

## Implemented changes

### Calendar 날짜 팝업 헤더 깨짐 수정
- `frontend/src/routes/Calendar.tsx`
  - `buildCalendarSheetHeaderStyle()`: 헤더를 `flexDirection: 'column'` + `gap: 10` 으로 바꿔 grip 을 헤더 안에 품고, `borderRadius: '22px 22px 0 0'` 추가로 panel 둥근 모서리와 정렬, padding `'12px 18px 12px'` 로 조정. (테스트가 검증하는 `position:'sticky', top:0, zIndex:3, background` 는 유지)
  - `DatePanel` JSX: 기존 standalone `<span panelGrip>` + `<header>` 구조를 → `<header>` 안에 `panelGrip` + `sheetHeaderRow`(날짜 + 닫기 버튼) 로 재구성. grip 이 헤더와 한 덩어리로 sticky.
  - `styles.panel`: `padding` top `14px → 0` 으로 sticky 헤더를 최상단 flush.
  - `styles.panelGrip`: `margin '0 auto 12px' → '0 auto'` (헤더 column gap 이 간격 처리).
  - `styles.sheetHeaderRow` 신규 추가 (flex row, space-between, 날짜/닫기 정렬).

### Analysis 직접모드 노치 가림 수정
- `frontend/src/routes/Analysis.tsx`
  - `styles.header.padding`: `'16px 20px 6px' → 'calc(40px + env(safe-area-inset-top)) 20px 6px'`. 데스크탑 가짜 노치(상단 ~36px) 클리어 + 모바일 safe-area 반영. Calendar 와 동일 접근. 사용자가 제안한 "한칸 내리기".

## Tests added/updated
- 신규 테스트 없음 (순수 CSS/JSX visual polish). 기존 `Calendar.test.ts` 의 sticky 헤더 계약(`position/top/zIndex/background`)은 그대로 통과하도록 헬퍼 키 보존.

## Commit
- `268c784` fix(frontend): 캘린더 팝업 헤더 깨짐 + 분석 직접모드 날짜 노치 가림 수정
- 2 files changed, +26 / -12.
