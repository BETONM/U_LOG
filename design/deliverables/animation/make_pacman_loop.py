#!/usr/bin/env python3
# === 유로그 마스코트 추격 애니메이션 v2 (ㅁ자 무한 루프) ===
# 오리지널 아케이드 화면(파란 이중선 미로) 스타일.
# Pac-Man 이 ㅁ자 복도를 시계방향으로 돌며 점을 먹고,
# 유로그 마스코트(유령)가 일정 거리 뒤를 계속 따라간다.
# 한 바퀴 = GIF 1루프가 되도록 프레임 수를 맞춰 끊김 없이 무한 반복.
# 먹힌 점은 일정 호길이 뒤에서 다시 자라나 루프 경계가 보이지 않는다.
# Pillow 로 3x 슈퍼샘플 렌더 후 GIF 인코딩.
import math
from PIL import Image, ImageDraw, ImageFont

# ---- 캔버스/스케일 ----
W, H = 600, 600
S = 3                      # 슈퍼샘플 배수
IW, IH = W * S, H * S

# ---- 색 (아케이드 팔레트) ----
BG        = (0, 0, 0)
WALL      = (33, 33, 222)        # 미로 벽 파랑
WALL_GLOW = (70, 70, 255)
PAC       = (255, 255, 0)
DOT       = (255, 184, 174)      # 아케이드 점(살구빛)
TEXT_YEL  = (255, 255, 0)

# ---- ㅁ 경로 (시계방향: 상→우→하→좌) ----
L, T, R, B = 120, 120, 480, 480   # 복도 중심선 사각형
SEGS = [
    ((L, T), (R, T)),   # 상단 →
    ((R, T), (R, B)),   # 우측 ↓
    ((R, B), (L, B)),   # 하단 ←
    ((L, B), (L, T)),   # 좌측 ↑
]
SEG_LEN = [math.dist(a, b) for a, b in SEGS]
PATH_LEN = sum(SEG_LEN)            # 1440


def pos_at(d):
    """경로 시작에서 호길이 d(랩어라운드)의 점과 진행각(도, y-down) 반환."""
    d = d % PATH_LEN
    for (a, b), Lseg in zip(SEGS, SEG_LEN):
        if d <= Lseg:
            t = d / Lseg
            x = a[0] + (b[0] - a[0]) * t
            y = a[1] + (b[1] - a[1]) * t
            ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])) % 360
            return x, y, ang
        d -= Lseg
    bx, by = SEGS[-1][1]
    return bx, by, 270.0


# ---- 점(dot) 배치: 한 바퀴에 정확히 등간격 ----
DOT_COUNT = 48
dots = [(*pos_at(i * PATH_LEN / DOT_COUNT)[:2], i * PATH_LEN / DOT_COUNT) for i in range(DOT_COUNT)]

# ---- 모션 파라미터 (완전 루프: N 프레임 = 정확히 한 바퀴) ----
N = 104
SPEED = PATH_LEN / N               # px/frame
LAG = PATH_LEN * 0.16              # 마스코트가 뒤따르는 호길이 거리
EATEN = PATH_LEN * 0.55            # 먹힌 점이 다시 자라기까지의 호길이
MOUTH_CYCLES = 26                  # 한 바퀴 동안 입 벌렸다 닫는 횟수 (정수 → 루프 이음새 없음)
BOB_CYCLES = 13


def sc(*vals):
    return tuple(v * S for v in vals)


def load_font(size):
    for cand in (
        "/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        try:
            return ImageFont.truetype(cand, size * S)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_pacman(dr, cx, cy, ang, mouth_half):
    r = 22
    bb = sc(cx - r, cy - r, cx + r, cy + r)
    dr.pieslice(bb, ang + mouth_half, ang + 360 - mouth_half, fill=PAC)


# ---- 로기 스프라이트 (실제 마스코트 이미지) ----
ROGI_H = 62
_rogi = Image.open("design/deliverables/animation/assets/rogi.png").convert("RGBA")
_rh = ROGI_H * S
_rw = round(_rogi.width * _rh / _rogi.height)
ROGI = _rogi.resize((_rw, _rh), Image.LANCZOS)          # 원본: 팻말이 오른쪽 (왼쪽 이동용)
ROGI_FLIP = ROGI.transpose(Image.FLIP_LEFT_RIGHT)       # 좌우반전 (오른쪽 이동용, 팻말이 뒤로)


def draw_rogi(base, cx, cy, dirx, bob):
    # 수직 구간(dirx==0)에서는 직전 수평 방향 유지: 우측 변이면 반전, 좌측 변이면 원본
    flip = dirx > 0 or (dirx == 0 and cx > (L + R) / 2)
    spr = ROGI_FLIP if flip else ROGI
    base.alpha_composite(spr, (round(cx * S - spr.width / 2), round((cy + bob) * S - spr.height / 2)))


def double_rounded(d, x0, y0, x1, y1, gap, radius, width):
    """아케이드식 이중선 둥근 사각형 벽."""
    d.rounded_rectangle(sc(x0, y0, x1, y1), radius=radius * S, outline=WALL, width=width * S)
    d.rounded_rectangle(
        sc(x0 + gap, y0 + gap, x1 - gap, y1 - gap),
        radius=max(2, radius - gap) * S, outline=WALL, width=width * S,
    )


def make_background():
    img = Image.new("RGBA", (IW, IH), BG + (255,))
    d = ImageDraw.Draw(img)
    HALF = 34            # 복도 반폭
    # 바깥 벽 (복도 바깥쪽)
    double_rounded(d, L - HALF, T - HALF, R + HALF, B + HALF, gap=7, radius=18, width=2)
    # 안쪽 벽 (가운데 블록)
    double_rounded(d, L + HALF, T + HALF, R - HALF, B - HALF, gap=7, radius=14, width=2)

    # 가운데 블록: 아케이드 READY! 레터링
    font = load_font(44)
    text = "READY!"
    bb = d.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    cx, cy = (L + R) / 2 * S, (T + B) / 2 * S
    d.text((cx - tw / 2 - bb[0], cy - th / 2 - bb[1]), text, font=font, fill=TEXT_YEL)
    # 상단 헤더: 아케이드 스코어 라인
    sub = load_font(18)
    header = "1UP      HIGH SCORE"
    sb = d.textbbox((0, 0), header, font=sub)
    d.text((cx - (sb[2] - sb[0]) / 2, 30 * S), header, font=sub, fill=(255, 255, 255))
    return img


background = make_background()
frames = []
for t in range(N):
    pac_d = t * SPEED
    px, py, pang = pos_at(pac_d)
    ghost_d = pac_d - LAG
    gx, gy, gang = pos_at(ghost_d)
    gdx, gdy = math.cos(math.radians(gang)), math.sin(math.radians(gang))

    frame = background.copy()
    dr = ImageDraw.Draw(frame)

    # 점 — pac 바로 앞~뒤 EATEN 구간은 사라졌다가 다시 자란다 (루프 이음새 없음)
    for (dx, dy, darc) in dots:
        rel = (pac_d - darc) % PATH_LEN
        eaten = rel < EATEN or rel > PATH_LEN - 10
        if not eaten:
            dr.ellipse(sc(dx - 4.5, dy - 4.5, dx + 4.5, dy + 4.5), fill=DOT)

    bob = 2.6 * math.sin(2 * math.pi * BOB_CYCLES * t / N)
    draw_rogi(frame, gx, gy, gdx, bob)

    mouth = 6 + 26 * abs(math.sin(math.pi * MOUTH_CYCLES * t / N))
    draw_pacman(dr, px, py, pang, mouth)

    small = frame.convert("RGB").resize((W, H), Image.LANCZOS)
    frames.append(small.convert("P", palette=Image.ADAPTIVE, colors=192))

OUT = "design/deliverables/animation/pacman_ulog_loop.gif"
frames[0].save(
    OUT, save_all=True, append_images=frames[1:],
    duration=40, loop=0, optimize=True, disposal=2,
)
print(f"saved {OUT}  frames={N} size={W}x{H} pathlen={PATH_LEN:.0f} dots={len(dots)}")
