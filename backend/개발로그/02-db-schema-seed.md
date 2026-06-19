# 02 · BE-2 · DB 스키마 + emotions 시드

- **날짜**: 2026-04-17
- **파트**: Backend (BE-2, PRD 4.6)
- **상태**: 완료
- **PRD 참조**: [4.3 데이터 모델](../../../docs/avoha/2026-04-17-avoha-prd.md), backend [README](../README.md)

## 목표

PRD 4.3 의 9개 테이블을 Drizzle ORM 스키마로 정의하고, PRD v1.1 의 10종 감정 카탈로그를 시드.

## 핵심 결정

| 결정 | 내용 | 이유 |
|---|---|---|
| ORM | **Drizzle** | PRD 스택 고정. 타입 안전 + Zod 연동 + SQL 가시성 |
| DB 드라이버 | `postgres` (postgres-js) | Drizzle 공식 권장, 가볍고 스트리밍 지원 |
| 로컬 인프라 | **docker-compose** (postgres:17 + redis:7-alpine) | Day 1-2 반복 속도 우선. Railway 는 배포 단계(BE-1)에서 `DATABASE_URL` 교체. |
| 스키마 적용 방식 | `drizzle-kit generate` → `psql < SQL` | `drizzle-kit push` 의 인터랙티브 메뉴가 CI·스크립트 환경에서 hang. PRD 에서 "스키마 마이그레이션" 명시했으므로 파일 기반이 정도. |
| `kakao_id` 표현 모드 | `bigint({ mode: "number" })` | JS Number 안전 범위(2^53) 내 카카오 ID 10자리대. BigInt 연산 번거로움 회피. |

## 파일 트리

```
2_avoha/backend/
├── .env                          # KAKAO_*, DATABASE_URL, REDIS_URL
├── .env.example                  # 커밋 가능한 템플릿
├── docker-compose.yml            # postgres:17 + redis:7-alpine + healthcheck
├── drizzle.config.ts
├── package.json                  # drizzle-orm, postgres, drizzle-kit, tsx, typescript
├── tsconfig.json                 # NodeNext, ES2022, strict
└── src/db/
    ├── client.ts                 # postgres-js client + drizzle instance
    ├── schema.ts                 # 9 tables (PRD 4.3 + v1.1 컬럼)
    ├── seed.ts                   # emotions upsert 러너
    ├── reset.ts                  # 개발용 public 스키마 drop/create
    ├── seeds/
    │   └── emotions.ts           # 10행 시드 데이터 (3 카테고리)
    └── migrations/
        └── 0000_amused_nighthawk.sql   # drizzle-kit generate 산출물
```

## 완료 상태

### 9 테이블

`users`, `collection_tickets`, `kakao_messages`, `emotions`, `gems`, `stickers`, `recipes`, `crafting_events`, `events`

**PRD v1.1 대응 컬럼**:
- `kakao_messages.content_type` ∈ `{text, image, mixed}` (v1.0 은 mixed 없었음)
- `emotions.category` ∈ `{calm, happy, negative}` (v1.0 엔 없던 컬럼)
- `gems.source` ∈ `{text, photo}` (사진·혼합 메시지 유래 보석 태깅)

### 인덱스 2

- `events(event_type, occurred_at)` — KPI 시간별 집계 쿼리
- `events USING gin (props)` — JSONB ad-hoc 조회

### 10 emotions (PRD v1.1)

| 카테고리 | code | 한글 | 임시 광물명 | HEX |
|---|---|---|---|---|
| calm | untroubled | 무탈 | 일상석 | `#CDD5D8` |
| calm | serenity | 평온 | 청옥 | `#3AAFA9` |
| happy | pride | 뿌듯 | 황금석 | `#F5D76E` |
| happy | joy | 기쁨 | 홍옥 | `#E8614D` |
| happy | satisfaction | 만족 | 호박석 | `#E8A838` |
| happy | flutter | 설렘 | 분홍석영 | `#F6A5B5` |
| negative | sadness | 슬픔 | 흑요석 | `#4A6B8A` |
| negative | annoyance | 짜증 | 적철석 | `#C7502D` |
| negative | regret | 후회 | 재석 | `#8B7355` |
| negative | solace | 위로 | 월장석 | `#A8B5D1` |

> 광물명·HEX 는 디자이너 확정 전 **임시안**. 확정 후 `seeds/emotions.ts` 수정 → `npm run db:seed` 재실행으로 일괄 업데이트.

### 재설계 대기

- **`recipes` 테이블**: PRD v1.1 감정 재정의로 기존 6 레시피(저녁 식탁의 별 등) 무효화. 확정 전까진 **동종 합성만 지원** (동일 감정 tier N × 2 → tier N+1). 이종 합성은 recipes 시드 후 활성화.

## 재현 절차

```bash
cd 2_avoha/backend

# 1. 컨테이너 기동
docker compose up -d
# ~10초 기다린 후 둘 다 (healthy) 확인
docker compose ps

# 2. 의존성
npm install

# 3. 스키마 적용 — 두 경로 중 선택
#   (A) 인터랙티브 (터미널 직접 조작, ↓ + Enter)
npm run db:push
#   (B) 논-인터랙티브 (자동화 권장)
npx drizzle-kit generate
docker compose exec -T postgres psql -U avoha -d avoha \
  < src/db/migrations/0000_amused_nighthawk.sql

# 4. 시드
npm run db:seed
```

### 검증 쿼리

```bash
# 테이블 9개
docker compose exec -T postgres psql -U avoha -d avoha -c "\dt"

# emotions 카테고리별
docker compose exec -T postgres psql -U avoha -d avoha \
  -c "SELECT category, count(*) FROM emotions GROUP BY category;"
# 기대: calm 2, happy 4, negative 4
```

### 초기화 (개발 중 schema 재설계 시)

```bash
npm run db:reset     # public 스키마 drop/create
npx drizzle-kit generate   # SQL 재생성
docker compose exec -T postgres psql -U avoha -d avoha \
  < src/db/migrations/0000_*.sql
npm run db:seed
```

## 삽질 로그

### 1. 이전 프로젝트의 Postgres 16 볼륨 재사용 → 크래시 루프

**증상**:
```
FATAL: database files are incompatible with server
DETAIL: The data directory was initialized by PostgreSQL version 16,
        which is not compatible with this version 17.9
```
Postgres 컨테이너가 1분 간격으로 재시작 반복.

**원인**: 같은 머신의 과거 docker-compose 프로젝트가 `backend_pgdata` 라는 동일 이름의 볼륨을 남겨둠. Docker Compose 프로젝트명이 디렉터리명(`backend`)에서 자동 생성돼 이름 충돌. 그 볼륨엔 Postgres 16 데이터가 있어 v17 이미지와 불호환.

추가 복잡성: 그 이전 프로젝트의 orphan 컨테이너(`backend-db-1`, `backend-api-1`, `backend-nginx-1`)가 볼륨을 점유 중이라 `docker compose down -v` 가 `Resource is still in use` 로 볼륨 삭제 실패.

**해결**:
```bash
docker compose down --remove-orphans -v
docker volume rm -f backend_pgdata
docker compose up -d
```

**교훈**:
- Compose 프로젝트명이 디렉터리명에서 자동 도출되므로 충돌 가능성 있음
- 추후: `docker-compose.yml` 최상단 `name: avoha` 명시 또는 볼륨명 전역 유니크화(`avoha_pgdata`) 고려
- `--remove-orphans` 는 안전 장치로 항상 포함하는 것도 방법

### 2. `drizzle-kit push` 의 인터랙티브 메뉴 → 자동화 불가

**증상**: `npm run db:push` 가 다음 출력에서 멈춤:
```
❯ No, abort
  Yes, I want to execute all statements
```
화살표 키로 "Yes" 이동 후 Enter 가 필요한 메뉴. stdin 이 TTY 가 아닐 경우 입력 수단 없음. `yes ""` 파이프도 화살표 메뉴에는 무의미.

**해결**: `drizzle-kit generate` 로 SQL 파일만 뽑은 뒤 `psql` 로 직접 주입.

**교훈**:
- 자동화 컨텍스트(CI, 스크립트, 에이전트)에선 `push` 회피
- `generate` + migrator 또는 `psql < file` 패턴이 PRD "스키마 마이그레이션" 정신에도 부합
- 개발자 로컬에서 빠른 iteration 원하면 터미널에서 직접 `npm run db:push` 여전히 유효

### 3. Drizzle v0.36 의 table extras 문법

과거 `(t) => ({ pk: primaryKey(...) })` 객체 형식이었는데, 최신 버전은 `(t) => [primaryKey(...)]` 배열 형식 권장. 혼용 가능하지만 문서와 일관되게 배열 사용.

## 다음 단계

- **BE-3**: Fastify 스캐폴드 + Kakao OAuth
  - `GET /health` — healthcheck
  - `GET /auth/kakao/login` — 카카오 authorize URL 로 302
  - `GET /auth/kakao/callback` — 토큰 교환 → 사용자 정보 조회 → `users` upsert → HttpOnly 세션 쿠키 발급 → 프론트로 302
  - `GET /me` — 현재 세션 사용자 + 오늘 채집권
  - 세션 미들웨어 (쿠키 서명 + 검증)

- **BE-4** (이후): `POST /webhook/kakao` + Redis 큐 publish. 공개 URL(ngrok 또는 Railway) 확보 선행.
