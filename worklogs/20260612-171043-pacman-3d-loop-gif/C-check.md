# C — Check

Status: completed

## 자동 검증
- `make_pacman_loop.py` 실행: pass (104 frames, 600x600, exit 0)
- `make_pacman_loop_3d.py` 실행: pass (96 frames, 540x540, exit 0, 4.4MB)
- 팩맨 입 SDF 수치 검증: 입 내부 점 sdf=+11.76 (제거됨), 입 방향 레이 통과 확인 — pass

## 시각 검수 (프레임 추출)
- 2D: READY! 중앙 노랑 + 1UP/HIGH SCORE 상단 헤더 확인 — pass
- 3D: 4개 구간(상/우/하/좌) 프레임 추출 검수 — 입 벌림/눈, 마스코트 추격, 점 먹힘/재생성, 그림자, 벽 입체감 확인 — pass
- 검수 중 수정 2건: 카메라 프레이밍(벽 잘림 → EYE 후퇴), 카메라 고도(입이 절단면만 보임 → y 460→330 으로 낮춤 + 입 안쪽 어둡게)

## 로기 스프라이트 교체 검증 (후속)
- 알파 추출 품질: 파란 배경 합성 검수 — 팻말 흰색 보존, 흰 헤일로 없음 — pass
- 2D 재렌더: pass (104 frames), 좌우 반전 방향 확인
- 3D 재렌더: pass (96 frames), 빌보드 원근 스케일/가림 확인
- 프레임 상단 "거대 로기" 의심 → 픽셀 검사로 반증 (top rows cream pixels = 0, 디스플레이 착시)

## Known verification limits
- GIF 루프 이음새(프레임 95→0)는 수학적으로 보장(정수 사이클)했으나 실재생 육안 확인은 사용자 몫
- 3D 4.4MB — 웹 임베드 기준으로는 무거울 수 있음 (프레임 수/해상도/색수 조정으로 감량 가능)
