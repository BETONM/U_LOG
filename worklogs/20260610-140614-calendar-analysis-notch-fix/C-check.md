# C - Check

Status: completed

## Automated checks
- `npx vitest run src/routes/Calendar.test.ts src/routes/Analysis.test.ts`
  - Pass: 2 files, 45/45 tests. (Calendar 26, Analysis 19)
  - sticky 헤더 계약 테스트("keeps the date popup header sticky while records scroll") 통과 유지.
- `npx tsc --noEmit`
  - Pass: exit 0, 타입 에러 없음.
- `npm run build` (= `tsc -b && vite build`, Railway 빌드와 동일)
  - Pass: 699 modules, built in ~1.2s.
  - 경고 2건은 본 변경과 무관한 기존 항목: (1) analytics.ts 동적/정적 동시 import 안내, (2) index 청크 500kB 초과 안내.

## Browser smoke
- Dev 서버: `http://localhost:5173/` (vite v6.4.2 ready, HTTP 200 on `/` 및 `/analysis`).
- 코드/빌드 레벨 검증 완료. 실제 시각 확인은 사용자가 로컬에서 직접 수행(캘린더 팝업 스크롤, 분석 직접모드 노치).

## Known verification limits
- 노치 클리어 수치(40px)는 데스크탑 가짜 노치 기준 계산값. 실제 디바이스/목업에서 살짝 과하거나 부족하면 `Analysis.tsx styles.header` 의 40px 만 미세조정 필요.
- 캘린더 팝업의 "깨짐"은 sticky+overflow+border-radius 렌더 이슈로, 브라우저/플랫폼별 잔여 1px 이음새 가능성은 실기기 확인 권장.
