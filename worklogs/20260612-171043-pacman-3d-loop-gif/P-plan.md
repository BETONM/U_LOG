# P — Plan

Status: completed

## Goal
유로그 팩맨 추격 GIF 업그레이드 2건:
1. 2D 버전(`pacman_ulog_loop.gif`) 가운데 문구를 아케이드 원작처럼 `READY!` 로 교체
2. 3D 버전 신규 제작 — ㅁ자 무한 순환, 입체 팩맨/마스코트/미로

## Source requirements (사용자 요청)
- "3D 버전도 하나 만들어줘"
- "2D 버전도 아까 레퍼런스 이미지(나무위키 아케이드 스크린샷)처럼 READY! 로 중간 문구 바꿔주고"
- (이전 턴) ㄷ자 → ㅁ자 무한 순환, 아케이드 스타일 고화질

## Approach
- 2D: `make_pacman_loop.py` 의 배경 텍스트만 수정 (READY! 중앙 + 1UP/HIGH SCORE 상단 헤더)
- 3D: Blender 미설치 → numpy 기반 SDF 레이마칭 소프트웨어 렌더러 자작
  - 정적 배경(바닥+벽) 1회 렌더 후 color/depth 캐시, 동적 객체는 화면 bbox 안에서만 렌더
  - 한 바퀴 = GIF 1루프(입/바운스 사이클 정수배)로 이음새 없는 무한 반복

## Non-goals
- Blender 등 외부 3D 툴 설치
- frontend 반영(기존 `pacman_ulog_follow.gif` 교체) — 사용자 승인 전 보류
- push/deploy — 사용자가 명시 요청하기 전엔 하지 않음
