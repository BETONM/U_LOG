# 03 · BE-3 · Fastify 스캐폴드 + Kakao OAuth

- **날짜**: 2026-04-18
- **파트**: Backend (BE-3, PRD §4.4 / 4.5 / 3.4)
- **상태**: 완료 (브라우저 OAuth 왕복 수동 검증 대기)

## 목표

Fastify 5 서버 기동 + Kakao OAuth 왕복 + HttpOnly 쿠키 세션 + `/me` 최소 구현. 프론트엔드(FE-3)가 로그인·세션 확인까지 붙일 수 있는 최소 API 제공.

## 핵심 결정

| 결정 | 내용 | 이유 |
|---|---|---|
| 세션 저장소 | `@fastify/secure-session` (쿠키 내 암호화) | Redis 세션 스토어 복잡도 회피. 쿠키 용량(≤4KB)이 `{userId, kakaoId, oauthState}` 에 충분. 7일 TTL. |
| OAuth 플로우 | 백엔드 주도 redirect | `client_secret` 서버 전용. FE는 `window.location.href` 한 줄. 로그 01 결정과 일관. |
| 카카오 REST 클라이언트 | native `fetch` 직접 구현 (~70 LOC) | kakao-sdk 공식 SDK 없음. axios 의존 회피. 우리가 쓰는 엔드포인트 2개 뿐. |
| CSRF 대책 | `state` 파라미터 포함 | 비용 ~8줄 (randomBytes→set→get→compare→clear). 세션 쿠키와 이중 방어. Kakao 공식 예제 패턴. |
| 쿠키 `sameSite` | `lax` (prod만 `secure=true`) | OAuth redirect 는 top-level GET 이라 lax 허용. strict 면 콜백에서 쿠키 드롭 → state mismatch. |
| 채집권 초기화 | `/me` 첫 호출 시 lazy insert (remaining=5) | 배치 cron(PRD §8.1)은 BE-11로 미룸. KST 경계는 `Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Seoul" })` 로 YYYY-MM-DD 문자열 계산 (Railway UTC 회피). |
| env 검증 | Zod 스키마 `src/env.ts`, 부팅 1회 | 오탈자·누락 조기 발견. `drizzle-kit` CLI 에는 주입 안 함 (`process.env` 직접 읽음, zod 중복 실행 방지). |
| 서버 엔트리 | `src/server.ts` 단일 파일 (`buildServer()` 팩토리 + `import.meta.url` 가드 bootstrap) | 향후 테스트·워커에서 `buildServer()` 재사용 가능. `src/index.ts` 분리는 불필요. |

## 파일 트리

```
2_avoha/backend/
├── src/
│   ├── env.ts                  # Zod env 검증, 모듈 로드 시 실행
│   ├── logger.ts               # Pino loggerOptions (dev: pino-pretty, prod: JSON, 헤더 redact)
│   ├── server.ts               # buildServer() 팩토리 + listen bootstrap
│   ├── types/
│   │   └── session.ts          # @fastify/secure-session SessionData 모듈 augmentation
│   ├── lib/
│   │   ├── kakao.ts            # OAuth REST 클라이언트 (authorize URL, token, user info)
│   │   ├── users.ts            # kakao_id 기준 users upsert (onConflictDoUpdate)
│   │   └── tickets.ts          # 오늘 collection_tickets lazy insert
│   └── routes/
│       ├── health.ts           # GET /health
│       ├── auth.ts             # GET /auth/kakao/login, /callback
│       └── me.ts               # GET /me
└── (기존 db/ 유지, 변경 없음)
```

## API

| 메서드 | 경로 | 설명 | 응답 |
|---|---|---|---|
| GET | `/health` | 헬스체크 | 200 `{ status: "ok" }` |
| GET | `/auth/kakao/login` | Kakao authorize URL 로 302 (state 쿠키 저장) | 302 |
| GET | `/auth/kakao/callback?code&state` | 토큰 교환 → 사용자 정보 → `users` upsert → 세션 쿠키 → FE 리다이렉트 | 302 to `FRONTEND_URL/login/callback` (성공) / `FRONTEND_URL/login?error=...` (실패) |
| GET | `/me` | 현재 사용자 + 오늘 채집권 (lazy insert) | 200 `{ user, tickets }` / 401 무인증 |

**에러 응답 공통 포맷**: `{ "error": { "message": string, "code"?: string } }`

## 완료 상태 (자동 검증됨)

```
curl -is http://localhost:3000/health           # 200 {"status":"ok"}
curl -is http://localhost:3000/me               # 401 UNAUTHENTICATED
curl -is http://localhost:3000/auth/kakao/login # 302 kauth.kakao.com
#   Location: https://kauth.kakao.com/oauth/authorize?
#     response_type=code&client_id=...&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fkakao%2Fcallback&state=<32hex>&scope=profile_nickname%2Cprofile_image
#   Set-Cookie: avoha_sid=...; Path=/; HttpOnly; SameSite=Lax
```

**수동 검증 대기 항목** (브라우저 필요):
- [ ] 실제 카카오 계정으로 로그인 → `users` 행 1건 INSERT 확인
- [ ] `avoha_sid` 쿠키로 `/me` 호출 → user + tickets 반환
- [ ] 카카오 동의 화면에서 "취소" → `/login?error=access_denied`

## Part A 리뷰 반영 (5건)

| # | 파일 | 변경 |
|---|---|---|
| A-1 | `docker-compose.yml` | 최상단 `name: avoha` + 볼륨 `avoha_pgdata`/`avoha_redisdata` 리네임. 프로젝트명/볼륨명 전역 유니크화. |
| A-2 | `drizzle.config.ts` | 하드코딩 fallback URL 제거 (IIFE throw 로 fail-fast). |
| A-3 | `.env`·`.env.example` | `JWT_SECRET` 삭제. `SESSION_SECRET`(hex 64자) + `FRONTEND_URL` 추가. |
| A-4 | `package.json` | `fastify`, `@fastify/cookie`, `@fastify/secure-session`, `pino`, `pino-pretty`, `zod` 추가. 스크립트 `dev`/`build`/`start`/`typecheck` 추가. |
| A-5 | `src/env.ts` (신규) | Zod 스키마, `safeParse` 후 이슈 리스트 출력 + `process.exit(1)`. |

## 재현 절차

```bash
cd 2_avoha/backend

# 1. SESSION_SECRET 생성 & .env 에 추가 (최초 1회)
openssl rand -hex 32    # 64자 hex를 .env 의 SESSION_SECRET= 뒷값에

# 2. 의존성 + 컨테이너
npm install
docker compose up -d
docker compose ps       # 둘 다 (healthy) 확인

# 3. DB 스키마 + 시드
docker compose exec -T postgres psql -U avoha -d avoha \
  < src/db/migrations/0000_amused_nighthawk.sql
npm run db:seed

# 4. 서버 기동
npm run dev             # http://localhost:3000

# 5. 스모크
curl -is http://localhost:3000/health
curl -is http://localhost:3000/me
curl -is http://localhost:3000/auth/kakao/login

# 6. 브라우저에서 OAuth 왕복 (선택)
open http://localhost:3000/auth/kakao/login
```

## 삽질 로그

### 1. `tsconfig.json` 의 `rootDir` 와 `include` 충돌

**증상**:
```
error TS6059: File '.../drizzle.config.ts' is not under 'rootDir' '.../src'.
```

**원인**: `tsconfig.json` 에서 `rootDir: "src"` 지정 + `include: ["src", "drizzle.config.ts"]` 로 루트의 drizzle 설정도 포함시켰더니 TS 가 "rootDir 밖의 파일 포함 불가" 에러. drizzle-kit 은 자체 TS 컴파일러를 써서 `drizzle.config.ts` 를 처리하므로 tsconfig include 에 넣을 필요 없음.

**해결**: `include: ["src"]` 로 축소.

**교훈**: `rootDir` 를 지정하면 `include` 의 모든 파일이 그 아래 있어야 함. 루트의 설정 파일(drizzle/vite/eslint config)은 별도 스코프로 취급.

### 2. `setErrorHandler` 의 `err: unknown` 타입 에러

**증상**:
```
src/server.ts(33,20): error TS18046: 'err' is of type 'unknown'.
```

**원인**: Fastify 5 의 `setErrorHandler` 핸들러 첫 인자가 콜백 내 추론에서 `unknown` 으로 좁혀짐 (버전/strict 조합 차이). `err.statusCode`, `err.message`, `err.code` 접근 시 전부 에러.

**해결**: `FastifyError` 타입을 명시 — `(err: FastifyError, req, reply) => { ... }`.

**교훈**: Fastify 5 의 콜백 인자는 제네릭 추론에 의존하지 말고 명시. `FastifyError` 는 `Error` + `{ statusCode, code, validation }` 을 포함.

### 3. Docker 컨테이너 이름 충돌 (볼륨 리네임 직후)

**증상**:
```
Error: Conflict. The container name "/avoha-redis" is already in use by container "<hash>".
You have to remove (or rename) that container to be able to reuse that name.
```

**원인**: `docker compose down -v` 후 즉시 `up -d` 했는데, 이전 `container_name: avoha-redis` 를 가진 컨테이너가 완전 삭제되지 않고 remnant 로 남음. 볼륨 리네임 작업과 타이밍이 꼬였을 가능성.

**해결**: `docker rm -f avoha-postgres avoha-redis` 로 명시 삭제 후 `up -d`.

**교훈**: `container_name` 을 명시했을 때 삭제 경합 가능. 애매하면 `docker rm -f` 또는 `container_name` 빼고 compose 자동 명명(project-service-N) 사용.

### 4. 포트 3000 점유 (다른 프로젝트)

**증상**: `npm run dev` 시 `EADDRINUSE: address already in use 0.0.0.0:3000`.

**원인**: 다른 로컬 Next.js 프로젝트의 dev 서버(`next-server v16.2.1`)가 포트 3000 점유.

**해결**: `lsof -i :3000` 으로 PID 특정 → 해당 프로젝트 서버 종료. 아보하 OAuth 는 Redirect URI 가 `http://localhost:3000/...` 로 카카오에 고정 등록돼 있어서 포트 변경 불가.

**교훈**: Kakao Developers 에 등록된 Redirect URI 가 개발 환경의 하드 제약. 멀티프로젝트 로컬 dev 시 포트 충돌 주의.

## 다음 단계

- **BE-4**: `POST /webhook/kakao` + Redis `emotion-queue` publish. 공개 HTTPS URL 필요 (ngrok 또는 Railway). Kakao 채널 관리자센터에서 웹훅 URL 등록 선행.
- **BE-7 준비**: `/me` 의 `requireSession` 가드를 `src/lib/auth-guard.ts` 로 추출 (라우트 늘어나면 중복 제거).
- **배포 전 보완**: 알림톡 발송(BE-10), 헬스체크 (BE-12), Metabase (BE-8). 기간 내 여유 보면서.
