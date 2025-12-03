import json
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# ================== MindCraft – Minimal Mind Map Builder ================== #

class MindCraftApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        # ----- Window Basic Setup -----
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.title("MindCraft – Mind Map Builder")
        self.geometry("1100x700")
        self.minsize(900, 550)

        # ----- Data Structures -----
        self.nodes = {}  # node_id -> dict
        self.connections = []  # list of dict {from, to, line_id}
        self.node_counter = 0

        self.item_to_node = {}  # canvas item id -> node_id
        self.line_to_connection = {}  # line item id -> connection dict

        self.dragging_node_id = None
        self.drag_start_offset = (0, 0)

        self.connect_mode = False
        self.delete_mode = False
        self.first_connect_node = None

        # ----- UI Layout -----
        self._build_ui()

    # ---------------------------------------------------------------------
    # UI
    # ---------------------------------------------------------------------

    def _build_ui(self):
        # Top bar
        top_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        top_bar.pack(side="top", fill="x")

        title_label = ctk.CTkLabel(
            top_bar,
            text="MindCraft",
            font=ctk.CTkFont("SF Pro Display", 20, weight="bold"),
        )
        title_label.pack(side="left", padx=16, pady=10)

        subtitle_label = ctk.CTkLabel(
            top_bar,
            text="Minimal Mind Map Builder",
            font=ctk.CTkFont(size=13),
            text_color="#6b7280",
        )
        subtitle_label.pack(side="left", pady=10)

        # Main frame
        main_frame = ctk.CTkFrame(self, corner_radius=0)
        main_frame.pack(side="top", fill="both", expand=True)

        # Left toolbar
        left_frame = ctk.CTkFrame(main_frame, width=220, corner_radius=0)
        left_frame.pack(side="left", fill="y")
        left_frame.pack_propagate(False)

        # Right canvas container
        canvas_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        canvas_frame.pack(side="right", fill="both", expand=True, padx=8, pady=8)

        # ------------- Left Panel Contents -------------

        ctk.CTkLabel(
            left_frame,
            text="Tools",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            left_frame,
            text="Double-click on the canvas to create a node.\nDrag to move. Connect or delete using modes.",
            font=ctk.CTkFont(size=11),
            text_color="#6b7280",
            justify="left",
            wraplength=190,
        ).pack(anchor="w", padx=15, pady=(0, 15))

        # Connect mode toggle
        self.connect_button = ctk.CTkButton(
            left_frame,
            text="Connect Mode: OFF",
            command=self.toggle_connect_mode,
            fg_color="#e5e7eb",
            text_color="#111827",
            hover_color="#d1d5db",
        )
        self.connect_button.pack(fill="x", padx=15, pady=4)

        # Delete mode toggle
        self.delete_button = ctk.CTkButton(
            left_frame,
            text="Delete Mode: OFF",
            command=self.toggle_delete_mode,
            fg_color="#fee2e2",
            text_color="#991b1b",
            hover_color="#fecaca",
        )
        self.delete_button.pack(fill="x", padx=15, pady=4)

        # Separator
        ctk.CTkLabel(
            left_frame,
            text="",
            height=2,
            fg_color="#e5e7eb",
        ).pack(fill="x", padx=15, pady=(12, 8))

        # Save/Load buttons
        ctk.CTkLabel(
            left_frame,
            text="Mind Map",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(anchor="w", padx=15)

        save_btn = ctk.CTkButton(
            left_frame,
            text="💾 Save Map",
            command=self.save_map_dialog,
        )
        save_btn.pack(fill="x", padx=15, pady=(6, 4))

        load_btn = ctk.CTkButton(
            left_frame,
            text="📂 Load Map",
            command=self.load_map_dialog,
        )
        load_btn.pack(fill="x", padx=15, pady=4)

        clear_btn = ctk.CTkButton(
            left_frame,
            text="🧹 Clear Canvas",
            fg_color="#f97316",
            hover_color="#ea580c",
            command=self.clear_canvas,
        )
        clear_btn.pack(fill="x", padx=15, pady=(12, 4))

        # Status
        self.status_label = ctk.CTkLabel(
            left_frame,
            text="Ready",
            font=ctk.CTkFont(size=11),
            text_color="#6b7280",
            wraplength=190,
            justify="left",
        )
        self.status_label.pack(anchor="w", padx=15, pady=(18, 4))

        ctk.CTkLabel(
            left_frame,
            text="Shortcuts:\n• Double-click: New node\n• Drag: Move node\n• Toggle modes on left",
            font=ctk.CTkFont(size=10),
            text_color="#9ca3af",
            justify="left",
            wraplength=190,
        ).pack(anchor="w", padx=15, pady=(4, 16))

        # ------------- Canvas -------------

        # Canvas with white background for Apple-style flat look
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#f9fafb",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        # Canvas bindings
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        self.canvas.bind("<Button-1>", self.on_canvas_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_canvas_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_mouse_up)

    # ---------------------------------------------------------------------
    # Node Helpers
    # ---------------------------------------------------------------------

    def create_node(self, x, y, text):
        """Create a flat, minimal node at position."""
        self.node_counter += 1
        node_id = self.node_counter

        # Approx width based on text length
        text_len = max(4, len(text))
        width = min(220, 70 + text_len * 7)
        height = 40

        x1 = x - width / 2
        y1 = y - height / 2
        x2 = x + width / 2
        y2 = y + height / 2

        rect_id = self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill="#ffffff",
            outline="#d1d5db",
            width=1,
        )
        text_id = self.canvas.create_text(
            x,
            y,
            text=text,
            font=("SF Pro Text", 11),
            fill="#111827",
        )

        self.nodes[node_id] = {
            "id": node_id,
            "x": x,
            "y": y,
            "w": width,
            "h": height,
            "text": text,
            "rect_id": rect_id,
            "text_id": text_id,
        }

        self.item_to_node[rect_id] = node_id
        self.item_to_node[text_id] = node_id

        return node_id

    def get_node_at(self, x, y):
        """Return node_id at given canvas coords, or None."""
        items = self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2)
        for item in items:
            node_id = self.item_to_node.get(item)
            if node_id is not None:
                return node_id
        return None

    def get_connection_at(self, x, y):
        """Return line_id at given point, or None."""
        # Use find_closest and check if it's a line we know
        items = self.canvas.find_overlapping(x - 2, y - 2, x + 2, y + 2)
        for item in items:
            if item in self.line_to_connection:
                return item
        return None

    def move_node(self, node_id, dx, dy):
        node = self.nodes[node_id]
        node["x"] += dx
        node["y"] += dy

        self.canvas.move(node["rect_id"], dx, dy)
        self.canvas.move(node["text_id"], dx, dy)

        self.update_node_connections(node_id)

    def update_node_connections(self, node_id):
        """Update all lines attached to this node."""
        node = self.nodes[node_id]
        x, y = node["x"], node["y"]
        for conn in self.connections:
            if conn["from"] == node_id or conn["to"] == node_id:
                other_id = conn["to"] if conn["from"] == node_id else conn["from"]
                other = self.nodes.get(other_id)
                if not other:
                    continue
                x2, y2 = other["x"], other["y"]
                if conn["from"] == node_id:
                    self.canvas.coords(conn["line_id"], x, y, x2, y2)
                else:
                    self.canvas.coords(conn["line_id"], x2, y2, x, y)

    # ---------------------------------------------------------------------
    # Modes
    # ---------------------------------------------------------------------

    def toggle_connect_mode(self):
        self.connect_mode = not self.connect_mode
        if self.connect_mode:
            self.delete_mode = False
            self.first_connect_node = None
            self.connect_button.configure(
                text="Connect Mode: ON",
                fg_color="#dbeafe",
                text_color="#1d4ed8",
            )
            self.delete_button.configure(
                text="Delete Mode: OFF",
                fg_color="#fee2e2",
                text_color="#991b1b",
            )
            self.status_label.configure(
                text="Connect Mode: Click first node, then second node to create a connection."
            )
        else:
            self.first_connect_node = None
            self.connect_button.configure(
                text="Connect Mode: OFF",
                fg_color="#e5e7eb",
                text_color="#111827",
            )
            self.status_label.configure(text="Ready")

    def toggle_delete_mode(self):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.connect_mode = False
            self.first_connect_node = None
            self.delete_button.configure(
                text="Delete Mode: ON",
                fg_color="#fecaca",
                text_color="#7f1d1d",
            )
            self.connect_button.configure(
                text="Connect Mode: OFF",
                fg_color="#e5e7eb",
                text_color="#111827",
            )
            self.status_label.configure(
                text="Delete Mode: Click a node to delete it, or a line to remove connection."
            )
        else:
            self.delete_button.configure(
                text="Delete Mode: OFF",
                fg_color="#fee2e2",
                text_color="#991b1b",
            )
            self.status_label.configure(text="Ready")

    # ---------------------------------------------------------------------
    # Canvas Event Handlers
    # ---------------------------------------------------------------------

    def on_canvas_double_click(self, event):
        # Try to avoid creating node on top of existing one
        if self.get_node_at(event.x, event.y) is not None:
            return

        # Ask for text
        dialog = ctk.CTkInputDialog(
            text="Enter node text:", title="New Node"
        )
        text = dialog.get_input()
        if text is None:
            return
        text = text.strip()
        if not text:
            return

        self.create_node(event.x, event.y, text)

    def on_canvas_mouse_down(self, event):
        # For click, decide whether we are selecting a node or line
        node_id = self.get_node_at(event.x, event.y)
        conn_line_id = self.get_connection_at(event.x, event.y)

        if self.delete_mode:
            # Delete node or line
            if node_id is not None:
                self.delete_node(node_id)
            elif conn_line_id is not None:
                self.delete_connection_line(conn_line_id)
            return

        if self.connect_mode:
            if node_id is not None:
                self.handle_connect_click(node_id)
            return

        # Normal mode -> drag node if any
        if node_id is not None:
            self.dragging_node_id = node_id
            node = self.nodes[node_id]
            self.drag_start_offset = (event.x - node["x"], event.y - node["y"])
        else:
            self.dragging_node_id = None

    def on_canvas_mouse_drag(self, event):
        if self.dragging_node_id is None:
            return
        node = self.nodes[self.dragging_node_id]
        new_x = event.x - self.drag_start_offset[0]
        new_y = event.y - self.drag_start_offset[1]
        dx = new_x - node["x"]
        dy = new_y - node["y"]
        self.move_node(self.dragging_node_id, dx, dy)

    def on_canvas_mouse_up(self, event):
        self.dragging_node_id = None

    def handle_connect_click(self, node_id):
        if self.first_connect_node is None:
            self.first_connect_node = node_id
            self.status_label.configure(
                text="Connect Mode: Now click the second node to connect."
            )
            # Optional: highlight node
            self.highlight_node(node_id, highlight=True)
        else:
            if node_id != self.first_connect_node:
                self.create_connection(self.first_connect_node, node_id)
            # remove highlight
            self.highlight_node(self.first_connect_node, highlight=False)
            self.first_connect_node = None
            self.status_label.configure(
                text="Connect Mode: Click first node, then second node."
            )

    def highlight_node(self, node_id, highlight=True):
        node = self.nodes[node_id]
        self.canvas.itemconfig(
            node["rect_id"],
            outline="#3b82f6" if highlight else "#d1d5db",
            width=2 if highlight else 1,
        )

    # ---------------------------------------------------------------------
    # Connections & Deletion
    # ---------------------------------------------------------------------

    def create_connection(self, from_id, to_id):
        # Avoid duplicate connections
        for c in self.connections:
            if (c["from"] == from_id and c["to"] == to_id) or (
                c["from"] == to_id and c["to"] == from_id
            ):
                return

        n1 = self.nodes[from_id]
        n2 = self.nodes[to_id]
        line_id = self.canvas.create_line(
            n1["x"],
            n1["y"],
            n2["x"],
            n2["y"],
            fill="#9ca3af",
            width=2,
        )
        conn = {"from": from_id, "to": to_id, "line_id": line_id}
        self.connections.append(conn)
        self.line_to_connection[line_id] = conn

    def delete_node(self, node_id):
        node = self.nodes.pop(node_id, None)
        if not node:
            return

        # delete canvas items
        self.canvas.delete(node["rect_id"])
        self.canvas.delete(node["text_id"])

        self.item_to_node.pop(node["rect_id"], None)
        self.item_to_node.pop(node["text_id"], None)

        # delete any associated connections
        for conn in self.connections[:]:
            if conn["from"] == node_id or conn["to"] == node_id:
                self.canvas.delete(conn["line_id"])
                self.line_to_connection.pop(conn["line_id"], None)
                self.connections.remove(conn)

    def delete_connection_line(self, line_id):
        conn = self.line_to_connection.pop(line_id, None)
        if conn:
            self.connections.remove(conn)
            self.canvas.delete(line_id)

    # ---------------------------------------------------------------------
    # Save / Load / Clear
    # ---------------------------------------------------------------------

    def clear_canvas(self):
        if not messagebox.askyesno(
            "Clear Mind Map",
            "This will remove all nodes and connections. Continue?",
        ):
            return
        self.canvas.delete("all")
        self.nodes.clear()
        self.connections.clear()
        self.item_to_node.clear()
        self.line_to_connection.clear()
        self.node_counter = 0
        self.status_label.configure(text="Canvas cleared.")

    def save_map_dialog(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Mind Map JSON", "*.json"), ("All Files", "*.*")],
            title="Save Mind Map",
        )
        if not path:
            return
        self.save_map(path)

    def load_map_dialog(self):
        path = filedialog.askopenfilename(
            defaultextension=".json",
            filetypes=[("Mind Map JSON", "*.json"), ("All Files", "*.*")],
            title="Load Mind Map",
        )
        if not path:
            return
        self.load_map(path)

    def save_map(self, path):
        data = {
            "nodes": [
                {
                    "id": node_id,
                    "x": n["x"],
                    "y": n["y"],
                    "text": n["text"],
                }
                for node_id, n in self.nodes.items()
            ],
            "connections": [
                {"from": c["from"], "to": c["to"]} for c in self.connections
            ],
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.status_label.configure(text=f"Saved map to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save map:\n{e}")

    def load_map(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load map:\n{e}")
            return

        # clear existing
        self.canvas.delete("all")
        self.nodes.clear()
        self.connections.clear()
        self.item_to_node.clear()
        self.line_to_connection.clear()

        # recreate nodes
        max_id = 0
        for n in data.get("nodes", []):
            nid = n["id"]
            text = n.get("text", "")
            x = n.get("x", WIDTH / 2)
            y = n.get("y", HEIGHT / 2)
            node_id = self.create_node(x, y, text)
            # preserve original id mapping if we want
            self.nodes[node_id]["id"] = nid
            if nid > max_id:
                max_id = nid

        # fix node_counter to not clash
        self.node_counter = max_id

        # rebuild a mapping old_id -> new_id (in case order changed)
        # here ids are kept in same order so we map by text+coords as fallback
        # for simplicity: assume ids loaded sequentially (works if saved from this app)
        id_map = {}
        # match by text & nearest position
        for saved in data.get("nodes", []):
            sid = saved["id"]
            sx, sy = saved["x"], saved["y"]
            st = saved["text"]
            best_id = None
            best_dist = 1e9
            for nid, nd in self.nodes.items():
                if nd.get("_mapped"):
                    continue
                if nd["text"] == st:
                    d = (nd["x"] - sx) ** 2 + (nd["y"] - sy) ** 2
                    if d < best_dist:
                        best_dist = d
                        best_id = nid
            if best_id is not None:
                id_map[sid] = best_id
                self.nodes[best_id]["_mapped"] = True

        # cleanup helper field
        for nd in self.nodes.values():
            nd.pop("_mapped", None)

        # recreate connections
        for c in data.get("connections", []):
            old_from = c["from"]
            old_to = c["to"]
            if old_from in id_map and old_to in id_map:
                self.create_connection(id_map[old_from], id_map[old_to])

        self.status_label.configure(text=f"Loaded map from {path}")


if __name__ == "__main__":
    app = MindCraftApp()
    app.mainloop()
