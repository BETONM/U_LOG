# D — Done

Status: completed

## 요약
- 2D ㅁ자 루프 GIF 중앙 문구를 아케이드 원작처럼 `READY!` 로 교체, 상단에 1UP/HIGH SCORE 헤더 추가
- numpy SDF 레이마칭 렌더러를 자작해 3D 버전 신규 제작 (입체 팩맨/유로그 마스코트/미로, ㅁ자 무한 순환)

## 변경 파일
- M `design/deliverables/animation/make_pacman_loop.py`
- M `design/deliverables/animation/pacman_ulog_loop.gif` (재렌더)
- A `design/deliverables/animation/make_pacman_loop_3d.py`
- A `design/deliverables/animation/pacman_ulog_loop_3d.gif`
- A `design/deliverables/animation/assets/rogi.png` (로기 투명배경 스프라이트, 후속 요청)

## 완료 체크리스트
- [x] 2D READY! 문구 교체 + 재렌더
- [x] 3D 렌더러 작성 + 96프레임 렌더
- [x] 프레임 시각 검수 (입/추격/점/그림자)
- [ ] frontend 반영 — 사용자 결정 대기

## Remaining risks
- 3D GIF 4.4MB — 웹 사용 시 감량 필요 가능
- push/deploy 미수행 (사용자 미요청, 기본 원칙)
