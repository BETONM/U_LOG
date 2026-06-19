# A - Audit

Status: completed

## Requirement-to-code mapping

### Calendar 날짜 팝업 헤더 깨짐
- 파일: `frontend/src/routes/Calendar.tsx`
  - `DatePanel` (≈L551~): `panel` → `panelGrip`(일반 흐름) → `sheetHeader`(sticky) → content 순.
  - `styles.panel`: `padding: '14px 18px ...'` (top 14px), `borderRadius: '22px 22px 0 0'`, `overflow: 'auto'`.
  - `buildCalendarSheetHeaderStyle()`: `position: sticky; top: 0; zIndex: 3; margin: '0 -18px 14px'`(full-bleed 음수 마진), `background: DETAIL_PANEL`, 하단 box-shadow.
  - `styles.panelGrip`: 헤더와 별개로 `margin: '0 auto 12px'` 로 헤더 위에 위치.
- 현재 동작/원인:
  - 스크롤 시 grip + panel top padding 14px 가 sticky 헤더 위에서 따로 스크롤 → 헤더 상단에 틈/이음새.
  - sticky 헤더가 음수 마진으로 full-bleed 인데 panel 의 둥근 모서리(22px) + `overflow:auto` 에 클립되며 상단 모서리에 1px 이음새가 보이는, sticky+overflow+border-radius 전형 렌더 버그.
- 제약: `Calendar.test.ts` L229~ 가 `buildCalendarSheetHeaderStyle()` 의 `position:'sticky', top:0, zIndex:3, background:'#A0BCA8'` 를 `toMatchObject` 로 검증 → 이 4개 키는 유지해야 함.

### Analysis 직접모드 날짜 노치 가림
- 파일: `frontend/src/routes/Analysis.tsx`, `frontend/src/App.tsx`, `frontend/src/styles/theme.css`
  - `App.tsx`: 모든 모바일 라우트는 `phone-frame-bezel` > `phone-frame` 안에 렌더.
  - `theme.css` L185 `.phone-frame-bezel::before`: 데스크탑(min-width 481px) 가짜 노치. `top:14px; height:34px; width:120px; z-index:9999`.
    - bezel padding 12px 기준, phone-frame 콘텐츠 좌표로 환산하면 노치는 **상단 y ≈ 2~36px, 가로 가운데 120px** 를 덮음.
  - `Analysis.tsx` `styles.header`: `padding: '16px 20px 6px'` (top 16px) → eyebrow 가 노치 y범위(2~36px) 안.
  - `styles.eyebrow`: `periodLabel` 출력. weekly="이번 주" / monthly="이번 달"(짧음, 좌측 머묾) vs custom=`${start} ~ ${end}` (긴 날짜 범위, 가로로 노치 밑까지 뻗음).
  - 대조군: `Calendar.tsx` `styles.screen` 은 `padding-top: calc(42px + env(safe-area-inset-top))` 라 노치를 이미 회피 중.
- 현재 동작/원인:
  - Analysis 헤더 top 패딩(16px) < 노치 하단(36px) → eyebrow 가 노치 영역에 들어감.
  - weekly/monthly 는 텍스트가 짧아 가운데 노치에 가로로 안 닿아 무사, custom 의 긴 날짜 범위만 가려짐.

## 검증 한계
- 노치는 데스크탑 미리보기(≥481px)의 가짜 노치. 실제 모바일은 `env(safe-area-inset-top)` 로 처리되며 본 수정은 두 경우 모두 커버하도록 `calc(40px + env(safe-area-inset-top))` 사용.
