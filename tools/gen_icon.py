"""
Generate assets/ICON_atw.ico and assets/ICON_atw_source.png.

Composites the TW base icon with two ATW-specific additions:
  1. Audio waveform bars replace the avatar circle at the top of the document
  2. Teal speaker badge in the lower-left corner (left-facing, waves left)

Edit assets/ICON_atw_source.png in GIMP to refine, then run:
    python tools/gen_icon.py --from-source
to regenerate the .ico from your edited PNG without re-compositing.

Default (no flag): re-composite from the TW base icon.
"""

import os
import sys
from PIL import Image, ImageDraw

_TW_ICO = r'C:\Users\juren\Projects\tag-writer\ICON_tw.ico'
_ASSETS = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'assets'))
_SOURCE = os.path.join(_ASSETS, 'ICON_atw_source.png')
_OUT    = os.path.join(_ASSETS, 'ICON_atw.ico')
_SIZES  = [16, 24, 32, 48, 64, 128, 256]

TEAL  = (30, 120, 120, 255)
WHITE = (255, 255, 255, 255)

# Avatar position in the 256 px TW frame (measured visually)
_AV_CX_FRAC = 87  / 256
_AV_CY_FRAC = 83  / 256
_AV_R_FRAC  = 43  / 256

# Waveform bar heights (normalised 0–1), symmetric, peak in centre
_BAR_PATTERN = [0.28, 0.52, 0.78, 0.58, 1.0, 0.58, 0.78, 0.52, 0.28]


def draw_waveform_in_circle(draw, cx, cy, radius):
    """Teal audio-waveform bars centred at (cx, cy) inside a circle of given radius."""
    n       = len(_BAR_PATTERN)
    usable  = radius * 1.55
    bar_w   = usable / (n * 1.35)
    gap     = bar_w * 0.35
    total_w = n * bar_w + (n - 1) * gap
    x0      = cx - total_w / 2
    max_h   = radius * 1.35
    rr      = max(1, bar_w / 2)

    for i, h_frac in enumerate(_BAR_PATTERN):
        bh   = max_h * h_frac
        bx   = x0 + i * (bar_w + gap)
        by_t = cy - bh / 2
        by_b = cy + bh / 2
        draw.rounded_rectangle([bx, by_t, bx + bar_w, by_b], radius=rr, fill=TEAL)


def draw_speaker(draw, cx, cy, s):
    """Left-facing speaker: body right-of-centre, cone opens left, waves left."""
    bw = s * 0.18
    bh = s * 0.20

    # Body
    body_x0 = cx + s * 0.02
    draw.rectangle(
        [body_x0, cy - bh / 2, body_x0 + bw, cy + bh / 2],
        fill=WHITE,
    )

    # Cone (flares LEFT from body_x0)
    cone_reach = s * 0.19
    draw.polygon([
        (body_x0,              cy - bh / 2),
        (body_x0,              cy + bh / 2),
        (body_x0 - cone_reach, cy + bh * 0.88),
        (body_x0 - cone_reach, cy - bh * 0.88),
    ], fill=WHITE)

    # Sound-wave arcs (LEFT of the cone tip)
    lw    = max(1, int(s * 0.055))
    tip_x = body_x0 - cone_reach
    span  = 62
    for r in [s * 0.20, s * 0.33]:
        draw.arc(
            [tip_x - r, cy - r, tip_x + r, cy + r],
            start=180 - span, end=180 + span,
            fill=WHITE, width=lw,
        )


def make_frame(tw_ico, size):
    tw_ico.size = (size, size)
    base    = tw_ico.convert('RGBA')
    overlay = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw    = ImageDraw.Draw(overlay)

    # ── 1. Replace avatar with waveform (skip for tiny sizes) ─────────
    if size >= 48:
        av_cx = _AV_CX_FRAC * size
        av_cy = _AV_CY_FRAC * size
        av_r  = _AV_R_FRAC  * size
        # Cover the avatar
        draw.ellipse(
            [av_cx - av_r, av_cy - av_r, av_cx + av_r, av_cy + av_r],
            fill=WHITE,
        )
        draw_waveform_in_circle(draw, av_cx, av_cy, av_r)

    # ── 2. Speaker badge — lower-left ─────────────────────────────────
    br     = int(size * 0.19)
    margin = int(size * 0.03)
    bx     = margin + br
    by     = size - margin - br

    # Drop-shadow
    shadow = max(1, size // 64)
    draw.ellipse(
        [bx - br + shadow, by - br + shadow, bx + br + shadow, by + br + shadow],
        fill=(0, 0, 0, 80),
    )
    # Teal disc
    draw.ellipse([bx - br, by - br, bx + br, by + br], fill=TEAL)

    if size > 24:
        draw_speaker(draw, bx, by, br * 1.5)

    return Image.alpha_composite(base, overlay)


def build_from_tw():
    """Composite TW base + ATW additions → source PNG + ICO."""
    tw_ico = Image.open(_TW_ICO)
    frames = []
    for s in _SIZES:
        try:
            frames.append(make_frame(tw_ico, s))
        except Exception as e:
            print(f'  skipping {s}px: {e}')

    # Save the 256 px frame as the GIMP-editable source
    for f in frames:
        if f.size == (256, 256):
            f.save(_SOURCE)
            print(f'Source PNG: {_SOURCE}')
            break

    _write_ico(frames)


def build_from_source():
    """Downscale ICON_atw_source.png → ICO (use after GIMP edits)."""
    if not os.path.isfile(_SOURCE):
        raise FileNotFoundError(f'Source not found: {_SOURCE}\nRun without --from-source first.')
    src    = Image.open(_SOURCE).convert('RGBA')
    frames = [src.resize((s, s), Image.LANCZOS) for s in _SIZES]
    _write_ico(frames)


def _write_ico(frames):
    os.makedirs(_ASSETS, exist_ok=True)
    # PIL uses the first frame as the base source, so put the largest first
    frames_desc = sorted(frames, key=lambda f: f.size[0], reverse=True)
    frames_desc[0].save(
        _OUT,
        format='ICO',
        sizes=[f.size for f in frames_desc],
        append_images=frames_desc[1:],
    )
    print(f'ICO written: {_OUT}  ({len(frames_desc)} sizes)')


if __name__ == '__main__':
    if '--from-source' in sys.argv:
        build_from_source()
    else:
        build_from_tw()
