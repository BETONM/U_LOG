# A — Audit

Status: completed

## 기존 산출물 매핑
- `design/deliverables/animation/make_pacman_follow.py` — ㄷ자 추격 v1 (640x360)
- `design/deliverables/animation/make_pacman_loop.py` — ㅁ자 루프 v2 (600x600, 아케이드 스타일, 직전 턴 제작)
- `design/deliverables/animation/pacman_ulog_loop.gif` — v2 출력 (가운데 "U-LOG" 문구였음)
- `frontend/public/images/pacman_ulog_follow.gif` — 프론트에서 사용 중인 v1 (이번 작업에서 건드리지 않음)

## 요구사항 → 코드 위치
- READY! 문구: `make_pacman_loop.py` > `make_background()` 의 텍스트 블록
- 3D 버전: 신규 파일 필요 (`make_pacman_loop_3d.py`)

## 환경 확인
- Blender 미설치 (`which blender` 없음), numpy 2.4.4 사용 가능 → 순수 numpy 레이마칭 채택
