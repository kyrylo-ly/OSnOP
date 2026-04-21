import json
import sys
from copy import deepcopy
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import colorchooser, filedialog, messagebox, simpledialog
except ModuleNotFoundError as exc:
    if exc.name == "_tkinter":
        print("Tkinter is not available in this Python build.")
        print("Use a Python interpreter with Tk support, for example:")
        print("  /usr/bin/python3 lab8/graphical_editor.py")
        sys.exit(1)
    raise


class GraphicalEditor(tk.Tk):
    """Simple vector graphics editor for lab work."""

    SUPPORTED_FIGURES = ("line", "rectangle", "ellipse")

    def __init__(self):
        super().__init__()
        self.geometry("1100x720")
        self.minsize(800, 500)

        # Vector model: all figures are stored as records and re-rendered on demand.
        self.shapes = []
        self.history = []
        self.current_file = None
        self.is_dirty = False

        self.current_figure = tk.StringVar(value="line")
        self.line_color = "#000000"
        self.fill_color = ""
        self.line_width = 2

        self._dragging = False
        self._start = None
        self._preview_item = None

        self.selected_indices = []
        self._selection_rect = None
        self._selection_bbox = None
        self.clipboard_shapes = None
        self._paste_preview_items = []
        self._pasting = False
        self._moving = False
        self._move_start = None
        self._move_origin_shapes = None

        self.status_var = tk.StringVar(value="Ready")

        self._build_ui()
        self._bind_events()
        self._update_window_title()
        self._update_status()

    def _build_ui(self):
        self._build_menu()

        self.canvas = tk.Canvas(self, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        status = tk.Label(
            self,
            textvariable=self.status_var,
            anchor="w",
            relief=tk.SUNKEN,
            bd=1,
            padx=8,
            pady=4,
        )
        status.pack(fill=tk.X, side=tk.BOTTOM)

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New file", command=self.new_file)
        file_menu.add_command(label="Open...", command=self.open_file)
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_command(label="Save As...", command=self.save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo_last_operation, accelerator="Ctrl+Z")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut_selected)
        edit_menu.add_command(label="Copy", command=self.copy_selected)
        edit_menu.add_command(label="Paste", command=self.start_paste_mode)
        edit_menu.add_command(label="Delete selected", command=self.delete_selected)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all)
        edit_menu.add_command(label="Paste from File", command=self.notdone)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        figures_menu = tk.Menu(menubar, tearoff=0)
        figures_menu.add_radiobutton(
            label="Line",
            variable=self.current_figure,
            value="line",
            command=self._update_status,
        )
        figures_menu.add_radiobutton(
            label="Rectangle",
            variable=self.current_figure,
            value="rectangle",
            command=self._update_status,
        )
        figures_menu.add_radiobutton(
            label="Ellipse",
            variable=self.current_figure,
            value="ellipse",
            command=self._update_status,
        )
        figures_menu.add_separator()
        figures_menu.add_radiobutton(
            label="Select",
            variable=self.current_figure,
            value="select",
            command=self._update_status,
        )
        menubar.add_cascade(label="Figures", menu=figures_menu)

        props_menu = tk.Menu(menubar, tearoff=0)
        props_menu.add_command(label="Line color", command=self.choose_line_color)
        props_menu.add_command(label="Fill color", command=self.choose_fill_color)
        props_menu.add_command(label="Line thickness", command=self.choose_line_thickness)
        props_menu.add_separator()
        props_menu.add_command(label="Clear fill", command=self.clear_fill_color)
        menubar.add_cascade(label="Properties", menu=props_menu)

        self.config(menu=menubar)

    def _bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_hover)
        self.bind("<Escape>", self.cancel_current_operation)
        self.bind("<Control-z>", self.undo_last_operation)
        self.bind("<Command-z>", self.undo_last_operation)
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def _update_window_title(self):
        file_name = self.current_file.name if self.current_file else "Untitled"
        dirty = " *" if self.is_dirty else ""
        self.title(f"Lab8 Graphical Editor - {file_name}{dirty}")

    def _update_status(self):
        fill_repr = self.fill_color if self.fill_color else "none"
        selected = f" | Selected: {len(self.selected_indices)}" if self.selected_indices else ""
        suffix = " | Paste mode" if self._pasting else ""
        self.status_var.set(
            f"Figure: {self.current_figure.get()} | "
            f"Line: {self.line_color}, width={self.line_width} | "
            f"Fill: {fill_repr}{selected}{suffix}"
        )

    def _set_dirty(self, value=True):
        self.is_dirty = value
        self._update_window_title()

    def _push_history(self):
        self.history.append(deepcopy(self.shapes))

    @staticmethod
    def _normalize_rect(x1, y1, x2, y2):
        return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    @staticmethod
    def _rects_intersect(a, b):
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)

    def _shape_bbox(self, shape):
        return self._normalize_rect(shape["x1"], shape["y1"], shape["x2"], shape["y2"])

    def _point_in_bbox(self, x, y, bbox):
        if not bbox:
            return False
        x1, y1, x2, y2 = bbox
        return x1 <= x <= x2 and y1 <= y <= y2

    def _clear_selection_overlay(self):
        self.canvas.delete("selection_overlay")

    def _draw_selection_overlay(self):
        self._clear_selection_overlay()
        if self._selection_bbox is None:
            return
        x1, y1, x2, y2 = self._selection_bbox
        self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline="#0b5fff",
            width=1,
            dash=(5, 3),
            tags=("selection_overlay",),
        )

    def _recompute_selection_bbox(self):
        if not self.selected_indices:
            self._selection_bbox = None
            return
        boxes = [self._shape_bbox(self.shapes[idx]) for idx in self.selected_indices if 0 <= idx < len(self.shapes)]
        if not boxes:
            self._selection_bbox = None
            return
        x1 = min(b[0] for b in boxes)
        y1 = min(b[1] for b in boxes)
        x2 = max(b[2] for b in boxes)
        y2 = max(b[3] for b in boxes)
        self._selection_bbox = (x1, y1, x2, y2)

    def _clear_selection(self):
        self.selected_indices = []
        self._selection_bbox = None
        self._clear_selection_overlay()
        self._update_status()

    def _update_selection(self, selection_rect):
        self.selected_indices = []
        for idx, shape in enumerate(self.shapes):
            if self._rects_intersect(selection_rect, self._shape_bbox(shape)):
                self.selected_indices.append(idx)
        self._recompute_selection_bbox()
        self._draw_selection_overlay()
        self._update_status()

    def _cancel_paste_preview(self):
        for item in self._paste_preview_items:
            self.canvas.delete(item)
        self._paste_preview_items.clear()

    def _reset_interaction_state(self):
        if self._preview_item is not None:
            self.canvas.delete(self._preview_item)
        self._preview_item = None
        if self._selection_rect is not None:
            self.canvas.delete(self._selection_rect)
        self._selection_rect = None
        self._dragging = False
        self._moving = False
        self._start = None
        self._move_start = None
        self._move_origin_shapes = None
        self._cancel_paste_preview()
        self._pasting = False
        self._update_status()

    @staticmethod
    def notdone():
        messagebox.showerror("Not implemented", "Not yet available")

    @staticmethod
    def _color_to_fill(color):
        return color if color else ""

    @staticmethod
    def _shape_to_canvas_fill(shape):
        return shape.get("fill") or ""

    def choose_line_color(self):
        color = colorchooser.askcolor(color=self.line_color, title="Choose line color")[1]
        if color:
            self.line_color = color
            self._update_status()

    def choose_fill_color(self):
        color = colorchooser.askcolor(
            color=self.fill_color if self.fill_color else "#ffffff",
            title="Choose fill color",
        )[1]
        if color:
            self.fill_color = color
            self._update_status()

    def clear_fill_color(self):
        self.fill_color = ""
        self._update_status()

    def choose_line_thickness(self):
        value = simpledialog.askinteger(
            "Line thickness",
            "Enter line thickness (1..30):",
            minvalue=1,
            maxvalue=30,
            initialvalue=self.line_width,
        )
        if value:
            self.line_width = value
            self._update_status()

    def on_mouse_down(self, event):
        if self._pasting:
            self._place_paste(event.x, event.y)
            return

        self._dragging = True
        self._start = (event.x, event.y)

        if self.current_figure.get() == "select":
            if self.selected_indices and self._point_in_bbox(event.x, event.y, self._selection_bbox):
                self._moving = True
                self._move_start = (event.x, event.y)
                self._move_origin_shapes = deepcopy(self.shapes)
                return

            self._moving = False
            self._clear_selection()
            self._selection_rect = self.canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="#0b5fff",
                width=1,
                dash=(5, 3),
                tags=("selection_overlay",),
            )
            return

        x1, y1 = self._start
        style = self._current_style()
        figure = self.current_figure.get()

        if figure == "line":
            self._preview_item = self.canvas.create_line(
                x1, y1, x1, y1, fill=style["outline"], width=style["width"]
            )
        elif figure == "rectangle":
            self._preview_item = self.canvas.create_rectangle(
                x1,
                y1,
                x1,
                y1,
                outline=style["outline"],
                width=style["width"],
                fill=self._color_to_fill(style["fill"]),
            )
        elif figure == "ellipse":
            self._preview_item = self.canvas.create_oval(
                x1,
                y1,
                x1,
                y1,
                outline=style["outline"],
                width=style["width"],
                fill=self._color_to_fill(style["fill"]),
            )

    def on_mouse_move(self, event):
        if self._pasting:
            self._update_paste_preview(event.x, event.y)
            return

        if not self._dragging or self._start is None:
            return

        if self.current_figure.get() == "select":
            if self._moving and self._move_start and self._move_origin_shapes is not None:
                dx = event.x - self._move_start[0]
                dy = event.y - self._move_start[1]
                self.shapes = deepcopy(self._move_origin_shapes)
                for idx in self.selected_indices:
                    if 0 <= idx < len(self.shapes):
                        self.shapes[idx]["x1"] += dx
                        self.shapes[idx]["y1"] += dy
                        self.shapes[idx]["x2"] += dx
                        self.shapes[idx]["y2"] += dy
                self._redraw_all()
                return

            if self._selection_rect is not None:
                x1, y1 = self._start
                self.canvas.coords(self._selection_rect, x1, y1, event.x, event.y)
            return

        if self._preview_item is None:
            return

        x1, y1 = self._start
        self.canvas.coords(self._preview_item, x1, y1, event.x, event.y)

    def on_mouse_up(self, event):
        if self._pasting:
            return

        if not self._dragging or self._start is None:
            return

        if self.current_figure.get() == "select":
            if self._moving and self._move_origin_shapes is not None:
                moved = self.shapes != self._move_origin_shapes
                self._moving = False
                self._move_start = None
                if moved:
                    self.history.append(self._move_origin_shapes)
                    self._set_dirty(True)
                self._move_origin_shapes = None
                self._recompute_selection_bbox()
                self._draw_selection_overlay()
                self._dragging = False
                self._start = None
                return

            if self._selection_rect is not None:
                coords = self.canvas.coords(self._selection_rect)
                self.canvas.delete(self._selection_rect)
                self._selection_rect = None
                if len(coords) >= 4:
                    selection_rect = self._normalize_rect(coords[0], coords[1], coords[2], coords[3])
                    if selection_rect[0] != selection_rect[2] and selection_rect[1] != selection_rect[3]:
                        self._update_selection(selection_rect)
                    else:
                        self._clear_selection()
            self._dragging = False
            self._start = None
            return

        if self._preview_item is None:
            self._dragging = False
            self._start = None
            return

        coords = self.canvas.coords(self._preview_item)
        if len(coords) >= 4:
            x1, y1, x2, y2 = coords[:4]
        else:
            x1, y1 = self._start
            x2, y2 = event.x, event.y

        figure = self.current_figure.get()

        style = self._current_style()
        shape = {
            "type": figure,
            "x1": int(x1),
            "y1": int(y1),
            "x2": int(x2),
            "y2": int(y2),
            "outline": style["outline"],
            "fill": style["fill"],
            "width": int(style["width"]),
        }

        if shape["x1"] == shape["x2"] and shape["y1"] == shape["y2"]:
            self.canvas.delete(self._preview_item)
            self._preview_item = None
            self._dragging = False
            self._start = None
            return

        self._push_history()
        self.shapes.append(shape)
        # Keep the preview item as the final item to avoid flicker and event-coordinate issues.
        self._preview_item = None
        self._clear_selection()
        self._set_dirty(True)

        self._dragging = False
        self._start = None

    def _current_style(self):
        return {
            "outline": self.line_color,
            "fill": self.fill_color,
            "width": self.line_width,
        }

    def _draw_shape(self, shape):
        t = shape["type"]
        coords = (shape["x1"], shape["y1"], shape["x2"], shape["y2"])
        outline = shape["outline"]
        fill = self._shape_to_canvas_fill(shape)
        width = shape["width"]

        if t == "line":
            self.canvas.create_line(*coords, fill=outline, width=width)
        elif t == "rectangle":
            self.canvas.create_rectangle(*coords, outline=outline, fill=fill, width=width)
        elif t == "ellipse":
            self.canvas.create_oval(*coords, outline=outline, fill=fill, width=width)

    def _redraw_all(self):
        self.canvas.delete("all")
        for shape in self.shapes:
            self._draw_shape(shape)
        self._draw_selection_overlay()

    def cancel_current_operation(self, _event=None):
        if self._moving and self._move_origin_shapes is not None:
            self.shapes = self._move_origin_shapes
            self._move_origin_shapes = None
            self._redraw_all()

        self._reset_interaction_state()

    def undo_last_operation(self, _event=None):
        if not self.history:
            return
        self.shapes = self.history.pop()
        self._clear_selection()
        self._redraw_all()
        self._set_dirty(True)

    def select_all(self):
        if not self.shapes:
            self._clear_selection()
            return
        self.selected_indices = list(range(len(self.shapes)))
        self._recompute_selection_bbox()
        self._draw_selection_overlay()
        self._update_status()

    def copy_selected(self):
        if not self.selected_indices:
            return
        self._recompute_selection_bbox()
        if self._selection_bbox is None:
            return
        ox, oy = self._selection_bbox[0], self._selection_bbox[1]
        copied = []
        for idx in self.selected_indices:
            if 0 <= idx < len(self.shapes):
                src = deepcopy(self.shapes[idx])
                src["x1"] -= ox
                src["y1"] -= oy
                src["x2"] -= ox
                src["y2"] -= oy
                copied.append(src)
        self.clipboard_shapes = copied if copied else None

    def _make_paste_preview(self, anchor_x, anchor_y):
        self._cancel_paste_preview()
        if not self.clipboard_shapes:
            return
        for shape in self.clipboard_shapes:
            tmp = deepcopy(shape)
            tmp["x1"] += anchor_x
            tmp["y1"] += anchor_y
            tmp["x2"] += anchor_x
            tmp["y2"] += anchor_y
            t = tmp["type"]
            if t == "line":
                item = self.canvas.create_line(
                    tmp["x1"],
                    tmp["y1"],
                    tmp["x2"],
                    tmp["y2"],
                    fill=tmp["outline"],
                    width=tmp["width"],
                    dash=(4, 2),
                )
            elif t == "rectangle":
                item = self.canvas.create_rectangle(
                    tmp["x1"],
                    tmp["y1"],
                    tmp["x2"],
                    tmp["y2"],
                    outline=tmp["outline"],
                    fill=self._shape_to_canvas_fill(tmp),
                    width=tmp["width"],
                    dash=(4, 2),
                )
            else:
                item = self.canvas.create_oval(
                    tmp["x1"],
                    tmp["y1"],
                    tmp["x2"],
                    tmp["y2"],
                    outline=tmp["outline"],
                    fill=self._shape_to_canvas_fill(tmp),
                    width=tmp["width"],
                    dash=(4, 2),
                )
            self._paste_preview_items.append(item)

    def _update_paste_preview(self, x, y):
        if not self.clipboard_shapes:
            return
        if not self._paste_preview_items:
            self._make_paste_preview(x, y)
            return
        for shape, item in zip(self.clipboard_shapes, self._paste_preview_items):
            self.canvas.coords(
                item,
                shape["x1"] + x,
                shape["y1"] + y,
                shape["x2"] + x,
                shape["y2"] + y,
            )

    def start_paste_mode(self):
        if not self.clipboard_shapes:
            messagebox.showinfo("Paste", "Clipboard is empty. Use Select and Copy first.")
            return
        self.cancel_current_operation()
        self._pasting = True
        self._update_status()

    def _place_paste(self, x, y):
        if not self.clipboard_shapes:
            self._pasting = False
            self._update_status()
            return
        self._push_history()
        self._clear_selection()
        start_idx = len(self.shapes)
        for shape in self.clipboard_shapes:
            tmp = deepcopy(shape)
            tmp["x1"] += x
            tmp["y1"] += y
            tmp["x2"] += x
            tmp["y2"] += y
            self.shapes.append(tmp)
        self._cancel_paste_preview()
        self._pasting = False
        self.selected_indices = list(range(start_idx, len(self.shapes)))
        self._recompute_selection_bbox()
        self._redraw_all()
        self._set_dirty(True)
        self._update_status()

    def delete_selected(self):
        if not self.selected_indices:
            return
        self._push_history()
        selected = set(self.selected_indices)
        self.shapes = [s for i, s in enumerate(self.shapes) if i not in selected]
        self._clear_selection()
        self._redraw_all()
        self._set_dirty(True)

    def cut_selected(self):
        self.copy_selected()
        self.delete_selected()

    def on_mouse_hover(self, event):
        if self._pasting:
            self._update_paste_preview(event.x, event.y)

    def _confirm_discard_unsaved(self):
        if not self.is_dirty:
            return True
        choice = messagebox.askyesnocancel(
            "Unsaved changes",
            "You have unsaved changes. Save now?",
        )
        if choice is None:
            return False
        if choice:
            return self.save_file()
        return True

    def new_file(self):
        if not self._confirm_discard_unsaved():
            return
        self.cancel_current_operation()
        self.shapes.clear()
        self.history.clear()
        self.canvas.delete("all")
        self._clear_selection()
        self.current_file = None
        self._set_dirty(False)

    def save_file(self):
        if self.current_file is None:
            return self.save_file_as()
        return self._save_to_path(self.current_file)

    def save_file_as(self):
        path = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return False
        return self._save_to_path(Path(path))

    def _save_to_path(self, path: Path):
        payload = {
            "format": "lab8-vector-drawing",
            "version": 1,
            "shapes": self.shapes,
        }
        try:
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            self.current_file = path
            self._set_dirty(False)
            return True
        except OSError as exc:
            messagebox.showerror("Save error", f"Cannot save file:\n{exc}")
            return False

    def open_file(self):
        if not self._confirm_discard_unsaved():
            return

        path = filedialog.askopenfilename(
            title="Open",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return

        self._load_from_path(Path(path))

    def _validate_shapes(self, shapes):
        if not isinstance(shapes, list):
            raise ValueError("Invalid file: 'shapes' must be a list")

        validated = []
        for s in shapes:
            if not isinstance(s, dict):
                continue
            t = s.get("type")
            if t not in self.SUPPORTED_FIGURES:
                continue
            try:
                validated.append(
                    {
                        "type": t,
                        "x1": int(s.get("x1", 0)),
                        "y1": int(s.get("y1", 0)),
                        "x2": int(s.get("x2", 0)),
                        "y2": int(s.get("y2", 0)),
                        "outline": str(s.get("outline", "#000000")),
                        "fill": str(s.get("fill", "")),
                        "width": max(1, int(s.get("width", 1))),
                    }
                )
            except (TypeError, ValueError):
                continue

        return validated

    def _load_from_path(self, path: Path):
        try:
            self.cancel_current_operation()
            data = json.loads(path.read_text(encoding="utf-8"))
            shapes = self._validate_shapes(data.get("shapes", []))

            self.shapes = shapes
            self.history.clear()
            self._clear_selection()
            self.current_file = path
            self._redraw_all()
            self._set_dirty(False)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            messagebox.showerror("Open error", f"Cannot open file:\n{exc}")

    def exit_app(self):
        if self._confirm_discard_unsaved():
            self.destroy()


def main():
    app = GraphicalEditor()
    app.mainloop()


if __name__ == "__main__":
    main()
