#!/usr/bin/env python3
# === 유로그 마스코트 추격 애니메이션 ===
# Pac-Man 이 우상단에서 시작해 ㄷ자(좌→하→우)로 점을 먹으며 이동하고,
# 유로그 마스코트(벡터 유령)가 천천히 뒤를 따라간다.
# 다크 그리드 배경. Pillow 로 2x 슈퍼샘플 렌더 후 GIF 인코딩.
import math
from PIL import Image, ImageDraw

# ---- 캔버스/스케일 ----
W, H = 640, 360
S = 2                      # 슈퍼샘플 배수
IW, IH = W * S, H * S

# ---- 색 ----
BG       = (10, 11, 20)
GRID     = (34, 36, 64)
PAC      = (255, 205, 30)
DOT      = (242, 228, 193)
BODY     = (242, 228, 193, 236)
BODY_EDGE= (190, 150, 98, 220)
EYE      = (58, 32, 8)
CHEEK    = (216, 138, 122)
SMILE    = (122, 64, 24)
WHITE    = (255, 255, 255)

# ---- ㄷ 경로 (우상단 시작 → 좌 → 하 → 우) ----
TY, BY, LX, RX = 96, 300, 120, 540
SEGS = [
    ((RX, TY), (LX, TY)),   # 상단 가로 (왼쪽으로)
    ((LX, TY), (LX, BY)),   # 좌측 세로 (아래로)
    ((LX, BY), (RX, BY)),   # 하단 가로 (오른쪽으로)
]
SEG_LEN = [math.dist(a, b) for a, b in SEGS]
PATH_LEN = sum(SEG_LEN)


def pos_at(d):
    """경로 시작에서 호길이 d 만큼 떨어진 점과 진행각(도, y-down) 반환."""
    d = max(0.0, min(d, PATH_LEN))
    for (a, b), L in zip(SEGS, SEG_LEN):
        if d <= L:
            t = d / L
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360
            return x, y, ang
        d -= L
    bx, by = SEGS[-1][1]
    return bx, by, 0.0


# ---- 점(dot) 배치 ----
DOT_SPACING = 42
dots = []  # (x, y, arc_d)
dd = 24
while dd < PATH_LEN - 16:
    x, y, _ = pos_at(dd)
    dots.append((x, y, dd))
    dd += DOT_SPACING

# ---- 모션 파라미터 ----
SPEED = 16.5          # px/frame (final 좌표)
LAG = 178             # 마스코트가 뒤따르는 호길이 거리
HOLD = 6             # 끝에서 잠깐 멈춤(루프 완충)
N = math.ceil((PATH_LEN + LAG) / SPEED) + HOLD


def sc(*vals):
    return tuple(v * S for v in vals)


def draw_pacman(dr, cx, cy, ang, mouth_half):
    r = 22
    bb = sc(cx - r, cy - r, cx + r, cy + r)
    start = ang + mouth_half
    end = ang + 360 - mouth_half
    dr.pieslice(bb, start, end, fill=PAC)
    # 눈
    ex = cx + 4 * math.cos(math.radians(ang - 90))
    ey = cy + 4 * math.sin(math.radians(ang - 90)) - 8
    dr.ellipse(sc(ex - 2.4, ey - 2.4, ex + 2.4, ey + 2.4), fill=(40, 30, 6))


def draw_ghost(base, cx, cy, dirx, bob):
    """투명 레이어에 유령을 그려 base(RGBA)에 합성. ChibiAvatar 느낌의 단순화 버전."""
    cy += bob
    hw = 16          # 반폭
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    top = cy - 22
    base_y = cy + 14
    # 몸통 실루엣: 머리 돔 + 토르소 + 바닥 물결
    d.ellipse(sc(cx - hw, top, cx + hw, top + 2 * hw), fill=BODY)
    d.rectangle(sc(cx - hw, top + hw, cx + hw, base_y), fill=BODY)
    bump = hw * 0.62
    for bx in (cx - hw + bump * 0.55, cx, cx + hw - bump * 0.55):
        d.ellipse(sc(bx - bump, base_y - bump, bx + bump, base_y + bump), fill=BODY)
    # 가장자리 살짝 강조 (돔만)
    d.arc(sc(cx - hw, top, cx + hw, top + 2 * hw), 180, 360, fill=BODY_EDGE, width=max(1, S))

    # 하이라이트
    d.ellipse(sc(cx - hw * 0.5, top + 4, cx - hw * 0.5 + 9, top + 11), fill=(255, 255, 255, 90))

    # 눈 (진행 방향으로 살짝 이동)
    ox = 3.0 * (1 if dirx > 0 else (-1 if dirx < 0 else 0))
    for sx in (-6.5, 6.5):
        d.ellipse(sc(cx + sx + ox - 3, cy - 6, cx + sx + ox + 3, cy + 1), fill=EYE)
        d.ellipse(sc(cx + sx + ox - 2.2, cy - 6, cx + sx + ox - 0.4, cy - 4), fill=(255, 255, 255, 220))
    # 볼터치
    for sx in (-11, 11):
        d.ellipse(sc(cx + sx - 4, cy - 1, cx + sx + 4, cy + 4), fill=CHEEK + (90,))
    # 미소
    d.arc(sc(cx - 5 + ox, cy - 1, cx + 5 + ox, cy + 7), 20, 160, fill=SMILE, width=max(1, S))

    base.alpha_composite(layer)


def make_grid():
    img = Image.new("RGBA", (IW, IH), BG + (255,))
    d = ImageDraw.Draw(img)
    step = 40
    for x in range(0, W + 1, step):
        d.line(sc(x, 0) + sc(x, H), fill=GRID, width=1)
    for y in range(0, H + 1, step):
        d.line(sc(0, y) + sc(W, y), fill=GRID, width=1)
    return img


grid = make_grid()
frames = []
for t in range(N):
    pac_d = min(t * SPEED, PATH_LEN)
    px, py, pang = pos_at(pac_d)
    ghost_d = max(0.0, min(t * SPEED - LAG, PATH_LEN))
    gx, gy, gang = pos_at(ghost_d)
    gdirx = math.cos(math.radians(gang))

    frame = grid.copy()
    dr = ImageDraw.Draw(frame)

    # 점 — pac 이 지나간 점은 사라짐
    for (dx, dy, darc) in dots:
        if darc > pac_d + 10:
            dr.ellipse(sc(dx - 4, dy - 4, dx + 4, dy + 4), fill=DOT)

    # 마스코트(뒤) → Pac-Man(앞) 순으로 겹침
    bob = 2.6 * math.sin(t * 0.6)
    draw_ghost(frame, gx, gy, gdirx, bob)

    mouth = 6 + 24 * abs(math.sin(t * 0.5))
    draw_pacman(dr, px, py, pang, mouth)

    small = frame.convert("RGB").resize((W, H), Image.LANCZOS)
    frames.append(small.convert("P", palette=Image.ADAPTIVE, colors=128))

OUT = "design/deliverables/animation/pacman_ulog_follow.gif"
frames[0].save(
    OUT, save_all=True, append_images=frames[1:],
    duration=45, loop=0, optimize=True, disposal=2,
)
print(f"saved {OUT}  frames={len(frames)} size={W}x{H} pathlen={PATH_LEN:.0f} dots={len(dots)}")
