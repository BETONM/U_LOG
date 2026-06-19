# 01 · Kakao Developers 앱 셋업

- **날짜**: 2026-04-17
- **파트**: Backend (선행 작업)
- **상태**: 완료
- **산출물**: REST API 키, Client Secret, Redirect URI (`http://localhost:3000/auth/kakao/callback`) 등록

## 목표

`GET /auth/kakao/callback` 백엔드 라우트가 동작하기 위한 Kakao 측 사전 조건(키·동의항목·Redirect URI) 확보.

## 핵심 결정

| 결정 | 내용 | 이유 |
|---|---|---|
| OAuth 플로우 | 백엔드 주도 redirect (Authorization Code Grant) | `client_secret` 을 서버 전용으로. 프론트는 `window.location.href` 로 카카오 authorize URL 리다이렉트 후 콜백은 백엔드로. |
| JS SDK 미사용 | JavaScript 키 발급 스킵 | 공유하기·카카오맵 등 JS SDK 전용 기능 PRD 범위 외. 필요해지면 그때 추가. |
| 비즈니스 인증 미연동 | 사업자 심사 대기 없이 개인 개발자 계정으로 진행 | MVP 기간 내 사업자 심사 어려움. 이메일·전화번호 동의항목 포기, `kakao_id` + 닉네임 + 프로필 사진만 사용. |
| 채널 연결 스킵 | `제품 설정 → 카카오톡 채널` 연결 안 함 | `plusfriends` 동의·대표채널 등 옵션 기능 전용. OAuth 로그인과 무관. 웹훅 수신은 `center-pf.kakao.com` 에서 별도 설정. |

## 수행 단계

1. **앱 생성** — developers.kakao.com → 내 애플리케이션 → 앱 이름 "아보하"
   - App ID 1434352, 표시명 "닥토"
2. **REST API 키 발급** — 앱 설정 → 플랫폼 키 → 키 이름 "아보하"
   - 신규 UI 기준 Client Secret 자동 발급·활성화
   - 복사 후 `.env` 저장 (`KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`)
3. **Redirect URI 등록** — 같은 키의 수정 화면
   - `http://localhost:3000/auth/kakao/callback` 한 줄
   - 프로덕션 URL 은 Railway 배포 후 추가 예정
4. **카카오 로그인 활성화** — 제품 설정 → 카카오 로그인 → 일반 → 활성화 **ON**
5. **동의항목** — 제품 설정 → 카카오 로그인 → 동의항목
   - 닉네임 (`profile_nickname`): **필수 동의** / 목적: "카카오 계정 기반 회원 식별 및 아보하 서비스 내 사용자명 표시"
   - 프로필 사진 (`profile_image`): **선택 동의** / 목적: "아보하 마이페이지 및 아바타 UI 내 프로필 이미지 표시"
   - 나머지 전부 OFF/사용 안 함

## `.env` 반영

```env
KAKAO_REST_API_KEY=<발급값>
KAKAO_CLIENT_SECRET=<발급값>
KAKAO_REDIRECT_URI=http://localhost:3000/auth/kakao/callback
```

## 아직 안 한 것 (후속 트랙)

- [ ] 프로덕션 Redirect URI 추가 (`https://api.avoha.today/auth/kakao/callback`) — Railway 배포 + 도메인 연결 후
- [ ] "닥토 공방" 채널 관리자 권한 확보 — 채널 owner(PM)에게 공동 관리자 초대 요청. BE-4(웹훅) 전까지 필요
- [ ] `center-pf.kakao.com` 에서 웹훅 URL 등록 — BE-4 + 공개 HTTPS URL(ngrok/Railway) 확보 후
- [ ] 카카오 비즈메시지 API 승인 — 사업자 심사 선행. 지연되면 PRD 리스크 섹션대로 일반 채널 메시지로 폴백

## 삽질·메모

### 카카오 Developers UI 업데이트 (2025~)

예전 가이드에서 "앱 설정 → 보안 → Client Secret" 메뉴였는데, 현재 UI는 **REST API 키 생성 시 Client Secret 자동 발급 + 활성화**로 단순화됨. Client Secret 값은 "[REST API 키 수정]" 페이지에서 확인·복사.

### "카카오톡 채널" vs "Kakao Developers 앱"

별개 제품. 혼동 주의:

- **카카오톡 채널** (center-pf.kakao.com): 프로필·메시지 수신 주체. 사업자성 강함
- **Kakao Developers 앱** (developers.kakao.com): OAuth 인증 + REST API 키. 개인 개발자도 생성 가능

둘의 연결은 `제품 설정 → 카카오톡 채널` 메뉴에서 하되, 아보하는 옵션 기능 안 써서 스킵.

### `client_id` 파라미터가 무엇인지 헷갈림

OAuth authorize URL 의 `client_id` 파라미터에 들어가는 건 **REST API 키** (JavaScript 키 아님). 카카오 공식 문서 기준. `client_secret` 은 토큰 교환 단계에서만 사용.

### 키 유출 리스크 재평가 (localhost 한정)

localhost 만 Redirect URI 로 등록된 REST API 키가 유출돼도:

- OAuth 토큰 탈취는 ❌ (공격자가 자기 서버로 `code` 받아갈 수 없음)
- Client Secret 이 유출되지 않은 한 토큰 교환 불가
- 남은 리스크: Kakao API 쿼터 소진(미미)

단, **프로덕션 도메인을 Redirect URI 로 추가하는 시점부턴 유출된 키 즉시 재발급**.
