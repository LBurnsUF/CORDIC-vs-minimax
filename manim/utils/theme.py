from manim import *

BG = "#000000"
BG2 = "#0a0a0a"
BG3 = "#181818"
BG4 = "#222222"
TX = "#e0e0e0"
TX2 = "#888888"
BD = "#2a2a2a"
GRID_COLOR = "#333333"

CORDIC_COLOR = "#58c4dd"
TAYLOR_COLOR = "#fc6255"
MINIMAX_COLOR = "#83c167"
REF_COLOR = "#e8c547"
ACCENT_COLOR = "#b4a7d6"

ALGO_COLORS = {
    "cordic": CORDIC_COLOR,
    "taylor": TAYLOR_COLOR,
    "minimax": MINIMAX_COLOR,
}

def apply_theme(scene):
    scene.camera.background_color = BG

def section_title(text, subtitle=None):
    title = Text(text, font_size=48, color=TX, font="Consolas")
    if subtitle:
        sub = Text(subtitle, font_size=28, color=TX2, font="Consolas")
        group = VGroup(title, sub).arrange(DOWN, buff=0.4)
        return group
    return title

def label_text(text, size=24):
    return Text(text, font_size=size, color=TX, font="Consolas")

def dim_text(text, size=20):
    return Text(text, font_size=size, color=TX2, font="Consolas")
