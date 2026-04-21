import json
import sys
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
        self.current_file = None
        self.is_dirty = False

        self.current_figure = tk.StringVar(value="line")
        self.line_color = "#000000"
        self.fill_color = ""
        self.line_width = 2

        self._dragging = False
        self._start = None
        self._preview_item = None

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
        edit_menu.add_command(label="Cut", command=self.notdone)
        edit_menu.add_command(label="Copy", command=self.notdone)
        edit_menu.add_command(label="Paste", command=self.notdone)
        edit_menu.add_command(label="Delete selected", command=self.notdone)
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.notdone)
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
        self.protocol("WM_DELETE_WINDOW", self.exit_app)

    def _update_window_title(self):
        file_name = self.current_file.name if self.current_file else "Untitled"
        dirty = " *" if self.is_dirty else ""
        self.title(f"Lab8 Graphical Editor - {file_name}{dirty}")

    def _update_status(self):
        fill_repr = self.fill_color if self.fill_color else "none"
        self.status_var.set(
            f"Figure: {self.current_figure.get()} | "
            f"Line: {self.line_color}, width={self.line_width} | "
            f"Fill: {fill_repr}"
        )

    def _set_dirty(self, value=True):
        self.is_dirty = value
        self._update_window_title()

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
        self._dragging = True
        self._start = (event.x, event.y)

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
        if not self._dragging or self._preview_item is None or self._start is None:
            return

        x1, y1 = self._start
        self.canvas.coords(self._preview_item, x1, y1, event.x, event.y)

    def on_mouse_up(self, event):
        if not self._dragging or self._preview_item is None or self._start is None:
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

        self.shapes.append(shape)
        # Keep the preview item as the final item to avoid flicker and event-coordinate issues.
        self._preview_item = None
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
        self.shapes.clear()
        self.canvas.delete("all")
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
            data = json.loads(path.read_text(encoding="utf-8"))
            shapes = self._validate_shapes(data.get("shapes", []))

            self.shapes = shapes
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
