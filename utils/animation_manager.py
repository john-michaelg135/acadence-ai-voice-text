"""
Animation Manager for Acadence AI
Provides lightweight animation primitives using Tkinter's after() scheduler.
"""


def _hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def _rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"


def _lerp_color(color_a, color_b, t):
    r1, g1, b1 = _hex_to_rgb(color_a)
    r2, g2, b2 = _hex_to_rgb(color_b)
    return _rgb_to_hex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def _resolve_color(color_tuple_or_str, mode="Light"):
    if isinstance(color_tuple_or_str, tuple):
        return color_tuple_or_str[0] if mode == "Light" else color_tuple_or_str[1]
    return color_tuple_or_str


def animate_slide(widget, prop, from_val, to_val, duration_ms=250, steps=14, on_complete=None, _step=0):
    """Animates a place() property (x, y, relx, rely) from one value to another with ease-out."""
    if _step > steps:
        if on_complete:
            on_complete()
        return
    try:
        if not widget.winfo_exists():
            return
    except Exception:
        return

    if _step == 0:
        steps = max(1, duration_ms // 11)
        
    t = _step / steps
    t = 1 - (1 - t) ** 2.5  # ease-out
    val = from_val + (to_val - from_val) * t

    try:
        widget.place_configure(**{prop: val})
    except Exception:
        return

    interval = 11
    widget.after(interval, lambda: animate_slide(widget, prop, from_val, to_val, duration_ms, steps, on_complete, _step + 1))


def animate_slide_in(widget, overlay_class, bg_color, duration_ms=250, steps=10, _step=0, _overlay=None):
    """Page transition: overlay slides from left to right, revealing content underneath."""
    if _step == 0:
        _overlay = overlay_class(widget, fg_color=bg_color, corner_radius=0)
        _overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        _overlay.lift()

    if _step > steps:
        if _overlay and _overlay.winfo_exists():
            _overlay.destroy()
        return

    try:
        if not widget.winfo_exists():
            if _overlay and _overlay.winfo_exists():
                _overlay.destroy()
            return
    except Exception:
        return

    if _step == 0:
        steps = max(1, duration_ms // 11)
        
    t = _step / steps
    t = 1 - (1 - t) ** 2  # ease-out

    if _overlay and _overlay.winfo_exists():
        try:
            _overlay.place_configure(relx=t)
        except Exception:
            return

    interval = 11
    widget.after(interval, lambda: animate_slide_in(widget, overlay_class, bg_color, duration_ms, steps, _step + 1, _overlay))


def animate_bar_grow(canvas, window_id, bar_frame, bottom_square, count_text_id,
                     x0, bottom_y, target_height, bar_width, r,
                     duration_ms=400, steps=16, _step=0):
    """Grows a bar chart bar from height=0 upward to target height."""
    if _step > steps:
        try:
            canvas.itemconfigure(count_text_id, state="normal")
        except Exception:
            pass
        return
    try:
        if not canvas.winfo_exists():
            return
    except Exception:
        return

    if _step == 0:
        steps = max(1, duration_ms // 11)
        
    t = _step / steps
    t = 1 - (1 - t) ** 3  # ease-out cubic

    current_height = max(1, target_height * t)
    y0 = bottom_y - current_height

    try:
        canvas.coords(window_id, x0, y0)
        canvas.itemconfigure(window_id, height=current_height)
        if bottom_square is not None and current_height > r:
            for item in canvas.find_all():
                try:
                    w = canvas.itemcget(item, 'window')
                    if w and canvas.nametowidget(w) == bottom_square:
                        canvas.coords(item, x0, y0 + r)
                        canvas.itemconfigure(item, height=current_height - r)
                        break
                except Exception:
                    continue
        canvas.coords(count_text_id, x0 + (bar_width / 2), y0 - 12)
    except Exception:
        return

    interval = 11
    canvas.after(interval, lambda: animate_bar_grow(canvas, window_id, bar_frame, bottom_square, count_text_id,
                                                     x0, bottom_y, target_height, bar_width, r,
                                                     duration_ms, steps, _step + 1))
