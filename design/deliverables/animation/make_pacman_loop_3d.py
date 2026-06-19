#!/usr/bin/env python3
# === 유로그 마스코트 추격 애니메이션 3D (ㅁ자 무한 루프) ===
# numpy 소프트웨어 레이마칭(SDF) 렌더러. 외부 3D 툴 불필요.
# - 바닥 + 파란 이중 미로 벽: 정적이므로 한 번만 레이마칭해 color/depth 버퍼 캐시
# - 팩맨(구 - 원뿔 입), 유로그 마스코트(스피어/실린더 smin), 점: 매 프레임
#   화면 바운딩박스 안에서만 렌더 + 깊이 테스트로 합성
# - 캐릭터 아래 블롭 그림자, 방향광 램버트 + 스페큘러 셰이딩
# - 한 바퀴 = GIF 1루프 (입/바운스 사이클 정수배 → 이음새 없는 무한 반복)
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ---- 출력/내부 해상도 ----
OUT_W = OUT_H = 540
SS = 2
RW, RH = OUT_W * SS, OUT_H * SS
F32 = np.float32

# ---- 월드 지오메트리 ----
A = 170.0          # 경로(복도 중심선) 정사각형 반변
HALF = 36.0        # 복도 반폭
WALL_T = 4.0       # 벽 반두께
WALL_H = 26.0      # 벽 높이
ROUND = 3.0

# ---- 색 ----
COL_FLOOR  = np.array([10, 12, 34], dtype=F32)
COL_FLOOR2 = np.array([16, 18, 46], dtype=F32)
COL_WALL   = np.array([60, 60, 245], dtype=F32)
COL_PAC    = np.array([255, 220, 30], dtype=F32)
COL_PAC_IN = np.array([120, 70, 8], dtype=F32)
COL_EYE    = np.array([45, 28, 10], dtype=F32)
COL_DOT    = np.array([255, 190, 180], dtype=F32)
COL_TEXT   = np.array([255, 230, 40], dtype=F32)

LIGHT = np.array([-0.42, 0.78, 0.34], dtype=F32)
LIGHT /= np.linalg.norm(LIGHT)

# ---- 카메라 ----
EYE = np.array([0.0, 330.0, 660.0], dtype=F32)
TGT = np.array([0.0, 10.0, -5.0], dtype=F32)
FOV = math.radians(42)

fwd = TGT - EYE; fwd /= np.linalg.norm(fwd)
right = np.cross(fwd, np.array([0.0, 1.0, 0.0])); right /= np.linalg.norm(right)
upv = np.cross(right, fwd)
TANF = math.tan(FOV / 2)

jy, jx = np.mgrid[0:RH, 0:RW].astype(F32)
ndx = (jx + 0.5) / RW * 2 - 1
ndy = 1 - (jy + 0.5) / RH * 2
RDX = fwd[0] + ndx * TANF * right[0] + ndy * TANF * upv[0]
RDY = fwd[1] + ndx * TANF * right[1] + ndy * TANF * upv[1]
RDZ = fwd[2] + ndx * TANF * right[2] + ndy * TANF * upv[2]
_n = np.sqrt(RDX**2 + RDY**2 + RDZ**2)
RDX /= _n; RDY /= _n; RDZ /= _n


# ---- SDF 프리미티브 ----
def sd_ring_wall(x, y, z, a):
    """반변 a 인 정사각 외곽선을 두께/높이로 돌출시킨 벽 SDF."""
    qx = np.abs(x) - a
    qz = np.abs(z) - a
    box2 = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qz, 0) ** 2) + np.minimum(np.maximum(qx, qz), 0)
    ring = np.abs(box2) - WALL_T
    dy = np.abs(y - WALL_H / 2) - WALL_H / 2
    return (np.sqrt(np.maximum(ring, 0) ** 2 + np.maximum(dy, 0) ** 2)
            + np.minimum(np.maximum(ring, dy), 0) - ROUND)


def scene_bg(x, y, z):
    floor = y
    wo = sd_ring_wall(x, y, z, A + HALF)
    wi = sd_ring_wall(x, y, z, A - HALF)
    return np.minimum(floor, np.minimum(wo, wi))


# ---- READY! 바닥 텍스트 마스크 ----
def make_text_mask():
    size = 512
    img = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(img)
    font = None
    for cand in ("/System/Library/Fonts/Supplemental/Courier New Bold.ttf",
                 "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        try:
            font = ImageFont.truetype(cand, 96)
            break
        except OSError:
            continue
    bb = d.textbbox((0, 0), "READY!", font=font)
    d.text(((size - bb[2] + bb[0]) / 2 - bb[0], (size - bb[3] + bb[1]) / 2 - bb[1]),
           "READY!", font=font, fill=255)
    return np.asarray(img, dtype=F32) / 255.0


TEXT_MASK = make_text_mask()
TEXT_EXT = 115.0   # 텍스트가 차지하는 월드 반변 (가운데 블록 안)


# ---- 배경 1회 렌더 (color, depth, world pos) ----
def render_background():
    t = np.full((RH, RW), 1.0, dtype=F32)
    for _ in range(160):
        px = EYE[0] + RDX * t
        py = EYE[1] + RDY * t
        pz = EYE[2] + RDZ * t
        d = scene_bg(px, py, pz)
        t = np.minimum(t + d * 0.9, 3000.0)
    px = EYE[0] + RDX * t; py = EYE[1] + RDY * t; pz = EYE[2] + RDZ * t
    hit = t < 2900.0

    # 노멀 (중심차분)
    e = 0.2
    nx = scene_bg(px + e, py, pz) - scene_bg(px - e, py, pz)
    ny = scene_bg(px, py + e, pz) - scene_bg(px, py - e, pz)
    nz = scene_bg(px, py, pz + e) - scene_bg(px, py, pz - e)
    nn = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-6
    nx /= nn; ny /= nn; nz /= nn
    lam = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)

    wo = sd_ring_wall(px, py, pz, A + HALF)
    wi = sd_ring_wall(px, py, pz, A - HALF)
    is_wall = np.minimum(wo, wi) < py  # 벽이 바닥보다 가까움

    col = np.zeros((RH, RW, 3), dtype=F32)
    # 바닥: 미세 체커
    check = ((np.floor(px / 42) + np.floor(pz / 42)) % 2)
    fcol = COL_FLOOR[None, None, :] * (1 - check[..., None]) + COL_FLOOR2[None, None, :] * check[..., None]
    # READY! 텍스트 (가운데 블록 바닥)
    inside = (np.abs(px) < TEXT_EXT) & (np.abs(pz) < TEXT_EXT * 0.45) & ~is_wall
    u = np.clip(((px / TEXT_EXT) * 0.5 + 0.5) * 511, 0, 511).astype(np.int32)
    v = np.clip(((pz / (TEXT_EXT * 0.45)) * 0.5 + 0.5) * 0.28 * 511 + 0.36 * 511, 0, 511).astype(np.int32)
    tmask = TEXT_MASK[v, u] * inside
    fcol = fcol * (1 - tmask[..., None]) + COL_TEXT[None, None, :] * tmask[..., None]

    shade = (0.5 + 0.5 * lam)[..., None]
    wcol = COL_WALL[None, None, :] * (0.45 + 0.65 * lam)[..., None]
    col = np.where(is_wall[..., None], wcol, fcol * shade)
    col = np.where(hit[..., None], col, 0.0)

    wpx = np.where(hit, px, 1e9); wpz = np.where(hit, pz, 1e9)
    is_floor = hit & ~is_wall
    return col, np.where(hit, t, 1e9), wpx, wpz, is_floor


print("rendering background ...")
BG_COL, BG_DEPTH, BG_PX, BG_PZ, BG_FLOOR = render_background()


# ---- 경로 ----
SEGS = [((-A, -A), (A, -A)), ((A, -A), (A, A)), ((A, A), (-A, A)), ((-A, A), (-A, -A))]
SEG_LEN = [math.dist(a, b) for a, b in SEGS]
PATH_LEN = sum(SEG_LEN)


def pos_at(dist):
    d = dist % PATH_LEN
    for (a, b), L in zip(SEGS, SEG_LEN):
        if d <= L:
            t = d / L
            x = a[0] + (b[0] - a[0]) * t
            z = a[1] + (b[1] - a[1]) * t
            hx, hz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
            return x, z, hx, hz
        d -= L
    (bx, bz) = SEGS[-1][1]
    return bx, bz, 0.0, -1.0


DOT_COUNT = 44
dots = [(*pos_at(i * PATH_LEN / DOT_COUNT)[:2], i * PATH_LEN / DOT_COUNT) for i in range(DOT_COUNT)]

N = 96
SPEED = PATH_LEN / N
LAG = PATH_LEN * 0.16
EATEN = PATH_LEN * 0.55
MOUTH_CYCLES = 24
BOB_CYCLES = 12

PAC_R = 26.0
DOT_R = 6.5


# ---- 투영/윈도우 ----
def project(p):
    v = p - EYE
    zc = float(v @ fwd)
    xs = float(v @ right) / (zc * TANF)
    ys = float(v @ upv) / (zc * TANF)
    px = (xs + 1) / 2 * RW
    py = (1 - ys) / 2 * RH
    return px, py, zc


def window(center, radius, margin=1.45):
    px, py, zc = project(center)
    r = radius / (zc * TANF) * RW / 2 * margin
    x0 = max(0, int(px - r)); x1 = min(RW, int(px + r) + 1)
    y0 = max(0, int(py - r)); y1 = min(RH, int(py + r) + 1)
    return x0, x1, y0, y1


def march_object(sdf_fn, color_fn, center, radius, col, depth):
    x0, x1, y0, y1 = window(center, radius)
    if x0 >= x1 or y0 >= y1:
        return
    rdx = RDX[y0:y1, x0:x1]; rdy = RDY[y0:y1, x0:x1]; rdz = RDZ[y0:y1, x0:x1]
    t = np.full(rdx.shape, max(1.0, np.linalg.norm(center - EYE) - radius * 2.5), dtype=F32)
    for _ in range(72):
        px = EYE[0] + rdx * t; py = EYE[1] + rdy * t; pz = EYE[2] + rdz * t
        d = sdf_fn(px, py, pz)
        t = t + d * 0.95
        if np.all((d < 0.03) | (t > 2000)):
            break
    px = EYE[0] + rdx * t; py = EYE[1] + rdy * t; pz = EYE[2] + rdz * t
    hit = (sdf_fn(px, py, pz) < 0.6) & (t < depth[y0:y1, x0:x1])
    if not hit.any():
        return
    e = 0.25
    nx = sdf_fn(px + e, py, pz) - sdf_fn(px - e, py, pz)
    ny = sdf_fn(px, py + e, pz) - sdf_fn(px, py - e, pz)
    nz = sdf_fn(px, py, pz + e) - sdf_fn(px, py, pz - e)
    nn = np.sqrt(nx**2 + ny**2 + nz**2) + 1e-6
    nx /= nn; ny /= nn; nz /= nn
    base = color_fn(px, py, pz)   # (h,w,3) 베이스 색
    lam = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    don = rdx * nx + rdy * ny + rdz * nz
    rx = rdx - 2 * don * nx; ry = rdy - 2 * don * ny; rz = rdz - 2 * don * nz
    spec = np.clip(rx * LIGHT[0] + ry * LIGHT[1] + rz * LIGHT[2], 0, 1) ** 24
    c = base * (0.34 + 0.72 * lam)[..., None] + 255 * 0.3 * spec[..., None]
    sub_c = col[y0:y1, x0:x1]
    sub_d = depth[y0:y1, x0:x1]
    sub_c[hit] = c[hit]
    sub_d[hit] = t[hit]


# ---- 팩맨 ----
def make_pacman(cx, cz, hx, hz, mouth_deg):
    cy = PAC_R + 1.5
    sin_m = math.sin(math.radians(mouth_deg))
    cos_m = math.cos(math.radians(mouth_deg))
    side = (-hz, hx)
    # 눈 방향 (위 + 약간 앞 + 좌우)
    eyes = []
    for s in (-1, 1):
        d = np.array([hx * 0.35 + side[0] * 0.42 * s, 0.82, hz * 0.35 + side[1] * 0.42 * s])
        d /= np.linalg.norm(d)
        eyes.append((cx + d[0] * PAC_R * 0.92, cy + d[1] * PAC_R * 0.92, cz + d[2] * PAC_R * 0.92))

    def sdf(x, y, z):
        qx = x - cx; qy = y - cy; qz = z - cz
        sph = np.sqrt(qx**2 + qy**2 + qz**2) - PAC_R
        par = qx * hx + qz * hz
        perp = np.sqrt(np.maximum(qx**2 + qy**2 + qz**2 - par**2, 0))
        cone = cos_m * perp - sin_m * par          # 입 원뿔 (내부 음수)
        body = np.maximum(sph, -cone)
        d = body
        for ex, ey, ez in eyes:
            d = np.minimum(d, np.sqrt((x - ex)**2 + (y - ey)**2 + (z - ez)**2) - 3.4)
        return d

    def color(x, y, z):
        qx = x - cx; qy = y - cy; qz = z - cz
        sph = np.sqrt(qx**2 + qy**2 + qz**2) - PAC_R
        c = np.empty(x.shape + (3,), dtype=F32)
        c[:] = COL_PAC
        c[np.abs(sph) > 0.8] = COL_PAC_IN          # 입 안쪽 단면
        for ex, ey, ez in eyes:
            m = np.sqrt((x - ex)**2 + (y - ey)**2 + (z - ez)**2) - 3.4 < 0.8
            c[m] = COL_EYE
        return c

    return sdf, color, np.array([cx, cy, cz]), PAC_R + 4


# ---- 유로그 마스코트 (로기): 실제 스프라이트를 빌보드로 합성 ----
ROGI_IMG = Image.open("design/deliverables/animation/assets/rogi.png").convert("RGBA")
ROGI_FLIP_IMG = ROGI_IMG.transpose(Image.FLIP_LEFT_RIGHT)
ROGI_WORLD_H = 62.0
ROGI_ASPECT = ROGI_IMG.width / ROGI_IMG.height


def draw_rogi(col, depth, cx, cz, hx, bob):
    center = np.array([cx, ROGI_WORLD_H / 2 + 1.5 + bob, cz], dtype=F32)
    v = center - EYE
    zc = float(v @ fwd)
    dist = float(np.linalg.norm(v))
    px, py, _ = project(center)
    ph = round(ROGI_WORLD_H / (zc * TANF) * RH / 2)
    pw = round(ph * ROGI_ASPECT)
    if ph < 2:
        return
    # 수직 구간(hx==0)에서는 직전 수평 방향 유지: 우측 변(x>0)이면 반전
    flip = hx > 0 or (hx == 0 and cx > 0)
    spr = (ROGI_FLIP_IMG if flip else ROGI_IMG).resize((pw, ph), Image.LANCZOS)
    arr = np.asarray(spr, dtype=F32)
    x0 = round(px - pw / 2); y0 = round(py - ph / 2)
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0, y0 = max(0, x0), max(0, y0)
    x1 = min(RW, x0 + pw - sx0); y1 = min(RH, y0 + ph - sy0)
    if x0 >= x1 or y0 >= y1:
        return
    sub = arr[sy0:sy0 + (y1 - y0), sx0:sx0 + (x1 - x0)]
    a = (sub[..., 3:4] / 255.0) * (depth[y0:y1, x0:x1] > dist)[..., None]
    col[y0:y1, x0:x1] = col[y0:y1, x0:x1] * (1 - a) + sub[..., :3] * a
    upd = a[..., 0] > 0.5
    depth[y0:y1, x0:x1][upd] = dist


# ---- 점: 해석적 구 교차 ----
def draw_dot(cx, cz, col, depth):
    cy = DOT_R + 0.5
    c = np.array([cx, cy, cz], dtype=F32)
    x0, x1, y0, y1 = window(c, DOT_R, margin=1.6)
    if x0 >= x1 or y0 >= y1:
        return
    rdx = RDX[y0:y1, x0:x1]; rdy = RDY[y0:y1, x0:x1]; rdz = RDZ[y0:y1, x0:x1]
    ox, oy, oz = EYE[0] - cx, EYE[1] - cy, EYE[2] - cz
    b = ox * rdx + oy * rdy + oz * rdz
    disc = b**2 - (ox**2 + oy**2 + oz**2 - DOT_R**2)
    hit = disc > 0
    t = -b - np.sqrt(np.maximum(disc, 0))
    hit &= (t > 0) & (t < depth[y0:y1, x0:x1])
    if not hit.any():
        return
    nx = (EYE[0] + rdx * t - cx) / DOT_R
    ny = (EYE[1] + rdy * t - cy) / DOT_R
    nz = (EYE[2] + rdz * t - cz) / DOT_R
    lam = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
    c3 = COL_DOT[None, None, :] * (0.45 + 0.6 * lam)[..., None]
    sub_c = col[y0:y1, x0:x1]; sub_d = depth[y0:y1, x0:x1]
    sub_c[hit] = c3[hit]
    sub_d[hit] = t[hit]


# ---- 블롭 그림자 ----
def blob_shadow(col, cx, cz, radius, strength=0.55):
    ox = cx + LIGHT[0] / LIGHT[1] * -10
    oz = cz + LIGHT[2] / LIGHT[1] * -10
    d2 = (BG_PX - ox)**2 + (BG_PZ - oz)**2
    s = np.clip(1 - d2 / (radius * radius), 0, 1) * strength
    s = np.where(BG_FLOOR, s, 0)
    col *= (1 - s)[..., None]


# ---- 메인 루프 ----
frames = []
for f in range(N):
    pac_d = f * SPEED
    pcx, pcz, phx, phz = pos_at(pac_d)
    gcx, gcz, ghx, ghz = pos_at(pac_d - LAG)
    bob = 3.0 * math.sin(2 * math.pi * BOB_CYCLES * f / N)
    mouth = 10 + 26 * abs(math.sin(math.pi * MOUTH_CYCLES * f / N))

    col = BG_COL.copy()
    depth = BG_DEPTH.copy()

    blob_shadow(col, pcx, pcz, PAC_R * 1.5)
    blob_shadow(col, gcx, gcz, 34.0, 0.45)

    for (dx, dz, darc) in dots:
        rel = (pac_d - darc) % PATH_LEN
        if not (rel < EATEN or rel > PATH_LEN - 10):
            draw_dot(dx, dz, col, depth)

    draw_rogi(col, depth, gcx, gcz, ghx, bob)

    p_sdf, p_col, p_c, p_r = make_pacman(pcx, pcz, phx, phz, mouth)
    march_object(p_sdf, p_col, p_c, p_r, col, depth)

    img = Image.fromarray(np.clip(col, 0, 255).astype(np.uint8))
    img = img.resize((OUT_W, OUT_H), Image.LANCZOS)
    frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=192))
    if f % 12 == 0:
        print(f"frame {f}/{N}")

OUT = "design/deliverables/animation/pacman_ulog_loop_3d.gif"
frames[0].save(
    OUT, save_all=True, append_images=frames[1:],
    duration=45, loop=0, optimize=True, disposal=2,
)
print(f"saved {OUT}  frames={N} size={OUT_W}x{OUT_H}")
