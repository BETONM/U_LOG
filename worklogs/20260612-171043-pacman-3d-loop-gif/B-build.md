# B — Build

Status: completed

## 변경 파일
1. `design/deliverables/animation/make_pacman_loop.py` (수정)
   - 중앙 문구 `U-LOG` → `READY!` (노랑)
   - `HIGH SCORE` 서브텍스트 → 상단 `1UP   HIGH SCORE` 헤더로 이동 (아케이드 원작 레이아웃)
   - 재렌더: `pacman_ulog_loop.gif` (600x600, 104f)

2. `design/deliverables/animation/make_pacman_loop_3d.py` (신규)
   - numpy SDF 레이마칭 렌더러 (외부 3D 툴 의존 없음, Pillow+numpy)
   - 지오메트리: 바닥 평면(체커) + 파란 이중 미로 벽(라운드 박스 링 SDF) + 중앙 바닥 READY! 텍스처
   - 팩맨 = 구 − 원뿔(입, 각도 애니메이션) + 눈 스피어 / 마스코트 = 머리 구 + 몸통 실린더 + 바닥 범프 smin 블렌딩 + 눈/볼터치
   - 성능: 정적 배경은 1회만 풀 레이마칭(color/depth/worldpos 캐시), 동적 객체는 투영 bbox 내에서만 마칭, 점은 해석적 구-광선 교차
   - 셰이딩: 방향광 램버트 + 스페큘러, 캐릭터 블롭 그림자
   - 카메라: 측면 3/4 뷰 (EYE y=330 — 너무 높으면 입이 안 보여서 낮춤)
   - 루프: N=96 = 정확히 한 바퀴, 입 24사이클/바운스 12사이클 정수배 → 이음새 없음
   - 출력: `pacman_ulog_loop_3d.gif` (540x540, 96f, 3x→2x SS)

## 추가 변경 (후속 요청: 마스코트를 실제 로기 이미지로 교체)
3. `design/deliverables/animation/assets/rogi.png` (신규)
   - 원본 `/Users/chan/Desktop/로기.png` (흰 배경 RGBA) → 가장자리 플러드필로 바깥 배경만 투명화
     (팻말 내부 흰색 보존), 1px 침식 + 블러로 흰 헤일로 제거, bbox 트림 (181x157)
4. `make_pacman_loop.py` — 벡터 유령 드로잉(`draw_ghost`) 제거, 로기 스프라이트 합성(`draw_rogi`)으로 교체
   - 이동 방향에 따라 좌우 반전 (팻말이 진행 방향 뒤로), 수직 구간은 직전 수평 방향 유지
5. `make_pacman_loop_3d.py` — SDF 유령(`make_ghost`) 제거, 로기 스프라이트 빌보드 합성으로 교체
   - 거리(zc)에 따른 스케일 + depth 버퍼 비교로 벽/팩맨과의 가림 처리, 블롭 그림자 유지

## 테스트
- 일회성 그래픽 산출물이라 자동 테스트 없음. 프레임 추출 후 시각 검수로 대체 (C-check 참고)
