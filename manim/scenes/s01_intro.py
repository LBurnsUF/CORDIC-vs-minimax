import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from manim import *
import numpy as np
from utils.theme import (
    apply_theme, section_title, label_text, dim_text,
    BG, TX, TX2, GRID_COLOR, CORDIC_COLOR, TAYLOR_COLOR,
    MINIMAX_COLOR, REF_COLOR, ACCENT_COLOR,
)


class Intro(Scene):
    def construct(self):
        apply_theme(self)

        # --- Title card ---
        title = section_title(
            "Computing Sin/Cos with No FPU",
            "ATxmega128A1U — 8-bit AVR"
        )
        self.play(FadeIn(title, shift=UP * 0.3), run_time=1.5)
        self.wait(2)
        self.play(FadeOut(title))
        self.wait(0.5)

        # --- Layout constants ---
        circle_center = LEFT * 3
        R = 2.0
        wave_origin = np.array([0.0, 0.0, 0.0])
        wave_length = 5.5
        wave_height = 2.0

        # --- Static axes ---
        circle = Circle(radius=R, color=GRID_COLOR, stroke_width=2).move_to(circle_center)

        x_axis_circ = Line(
            circle_center + LEFT * (R + 0.3),
            circle_center + RIGHT * (R + 0.3),
            color=GRID_COLOR, stroke_width=1,
        )
        y_axis_circ = Line(
            circle_center + DOWN * (R + 0.3),
            circle_center + UP * (R + 0.3),
            color=GRID_COLOR, stroke_width=1,
        )
        wave_baseline = Line(
            wave_origin + LEFT * 0.2,
            wave_origin + RIGHT * (wave_length + 0.3),
            color=GRID_COLOR, stroke_width=1,
        )
        wave_y_axis = Line(
            wave_origin + DOWN * (wave_height + 0.3),
            wave_origin + UP * (wave_height + 0.3),
            color=GRID_COLOR, stroke_width=1,
        )

        lbl_sin = label_text("sin θ", size=20).next_to(wave_y_axis, UP, buff=0.1)
        lbl_theta = label_text("θ", size=20).next_to(wave_baseline, RIGHT, buff=0.1)
        lbl_unit = dim_text("unit circle", size=16).next_to(circle, DOWN, buff=0.3)

        self.play(
            Create(circle), Create(x_axis_circ), Create(y_axis_circ),
            Create(wave_baseline), Create(wave_y_axis),
            FadeIn(lbl_sin), FadeIn(lbl_theta), FadeIn(lbl_unit),
            run_time=1.5,
        )

        # --- Animated elements ---
        theta = ValueTracker(0.001)

        def get_tip():
            t = theta.get_value()
            return circle_center + R * np.array([np.cos(t), np.sin(t), 0])

        radius_line = always_redraw(lambda: Line(
            circle_center, get_tip(), color=REF_COLOR, stroke_width=3,
        ))

        dot_circ = always_redraw(lambda: Dot(get_tip(), color=REF_COLOR, radius=0.06))

        # Projection: use Line instead of DashedLine to avoid zero-length crash
        proj_line = always_redraw(lambda: Line(
            get_tip(),
            circle_center + R * np.array([np.cos(theta.get_value()), 0, 0]),
            color=CORDIC_COLOR, stroke_width=2, stroke_opacity=0.6,
        ))

        dot_wave = always_redraw(lambda: Dot(
            wave_origin + np.array([
                (theta.get_value() / (2 * PI)) * wave_length,
                wave_height * np.sin(theta.get_value()),
                0,
            ]),
            color=CORDIC_COLOR, radius=0.05,
        ))

        # Connector: plain Line avoids DashedLine zero-length issue
        connector = always_redraw(lambda: Line(
            get_tip(),
            wave_origin + np.array([0, wave_height * np.sin(theta.get_value()), 0]),
            color=CORDIC_COLOR, stroke_width=1, stroke_opacity=0.4,
        ))

        angle_arc = always_redraw(lambda: Arc(
            radius=0.5,
            start_angle=0,
            angle=max(theta.get_value(), 0.001),
            arc_center=circle_center,
            color=ACCENT_COLOR, stroke_width=2,
        ))

        angle_label = always_redraw(lambda: Text(
            "θ", font_size=22, color=ACCENT_COLOR, font="Consolas",
        ).move_to(
            circle_center + 0.75 * np.array([
                np.cos(theta.get_value() / 2),
                np.sin(theta.get_value() / 2),
                0,
            ])
        ))

        # Sine trace: use TracedPath to avoid become() point-alignment issues
        wave_dot_invisible = Dot(
            wave_origin + np.array([0, 0, 0]), radius=0.001, fill_opacity=0,
        )
        wave_dot_invisible.add_updater(lambda m: m.move_to(
            wave_origin + np.array([
                (theta.get_value() / (2 * PI)) * wave_length,
                wave_height * np.sin(theta.get_value()),
                0,
            ])
        ))
        sine_trace = TracedPath(
            wave_dot_invisible.get_center,
            stroke_color=CORDIC_COLOR,
            stroke_width=2.5,
        )

        self.add(wave_dot_invisible, sine_trace)
        self.play(Create(radius_line), FadeIn(dot_circ), run_time=0.8)
        self.add(proj_line, connector, dot_wave, angle_arc, angle_label)
        self.wait(0.3)

        # Full rotation
        self.play(
            theta.animate.set_value(2 * PI),
            run_time=8,
            rate_func=linear,
        )
        self.wait(1)

        # --- Closing question ---
        question = label_text(
            "How do you compute these projections\nusing only integer arithmetic?",
            size=24,
        ).move_to(DOWN * 3.2)
        self.play(FadeIn(question, shift=UP * 0.2))
        self.wait(3)
