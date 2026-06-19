# A - Audit

Status: completed

## Requirement-to-code mapping
- 파일: `frontend/src/routes/Analysis.tsx`
  - L377(수정 전): `const periodLabel = period === 'weekly' ? '이번 주' : period === 'monthly' ? '이번 달' : \`${customRange.start} ~ ${customRange.end}\`;`
  - L440: `<p style={styles.eyebrow}>{periodLabel}</p>` — **유일한 사용처**. 다른 곳에서 참조 없음 → 단일 지점 수정으로 충분.
- 주차 계산 근거: `Calendar.tsx buildCalendarCells` 가 **일요일 시작** 달력(`firstDay = new Date(y,m,1).getDay()`). 동일 규칙으로 주차를 매기면 사용자가 보는 달력 행 번호와 일치.
  - 공식: `weekOfMonth = ceil((today.getDate() + firstWeekday) / 7)`.
  - 검증(2026-06-10): 6월 1일 = 월요일(getDay 1) → ceil((10+1)/7)=2 → "6월 2째주". 사용자 예시와 일치.

## 가능 여부
- **가능.** 단일 파생 값이라 부작용 없음. 순수 함수로 분리해 테스트 가능.

## 검증 한계
- 기존 `Analysis.test.ts` 의 `today` 는 UTC 문자열(`2026-05-19T12:00:00Z`)이라 로컬 타임존에서 일자가 흔들릴 수 있음 → 신규 테스트는 로컬 생성자 `new Date(2026, 5, 10)` 로 명시해 타임존 비의존.
