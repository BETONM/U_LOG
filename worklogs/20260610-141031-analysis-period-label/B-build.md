# B - Build

Status: completed

## Implemented changes
- `frontend/src/routes/Analysis.tsx`
  - `formatAnalysisPeriodLabel(period, today, customRange?)` 순수 헬퍼 신규 export.
    - monthly → `${month}월`
    - custom → `${start} ~ ${end}` (customRange 없으면 빈 문자열)
    - weekly → `${month}월 ${weekOfMonth}째주`, `weekOfMonth = ceil((today.getDate() + firstWeekday)/7)`, `firstWeekday = new Date(y,m,1).getDay()` (일요일 시작).
  - `periodLabel` 을 삼항 인라인에서 `formatAnalysisPeriodLabel(period, today, period==='custom' ? customRange : undefined)` 호출로 교체.

## Tests added/updated
- `frontend/src/routes/Analysis.test.ts`
  - `formatAnalysisPeriodLabel` import 추가.
  - 신규 describe 3종:
    - weekly → "6월 2째주"(2026-06-10), "6월 1째주"(2026-06-01)
    - monthly → "6월", "1월"
    - custom → "2026-05-28 ~ 2026-06-10"

## Commit
- `e95bc32` feat(analysis): 기간 라벨을 "6월 2째주"/"6월" 형식으로 표시
- 2 files changed, +35 / -1.
