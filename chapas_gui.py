# chapas_gui.py — versión optimizada con scroll limitado arriba/abajo

import threading
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
import funciones as fn
import theme_dark as theme

# Inicializar base de datos
fn.crear_bd()
fn.ensure_embedding_column()

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("CapCollection — Dark Mode Pro")
        self.root.geometry("980x700")
        self.root.minsize(900, 600)
        theme.style_root(self.root)

        # Layout: sidebar + main area
        self.left = Frame(root, bg=theme.PANEL, width=220)
        self.left.pack(side=LEFT, fill=Y)
        self.left.pack_propagate(False)

        self.main = Frame(root, bg=theme.BG)
        self.main.pack(side=LEFT, fill=BOTH, expand=True)

        self._build_sidebar()
        self._build_main_area()

        # Status bar
        self.status_var = StringVar(value="Ready")
        Label(root, textvariable=self.status_var, bg=theme.BG, fg=theme.MUTED, anchor="w").pack(side=BOTTOM, fill=X)

    # ---------------- Sidebar ----------------
    def _build_sidebar(self):
        pad = 12
        Label(self.left, text="CapCollection", bg=theme.PANEL, fg=theme.TEXT,
              font=("Segoe UI", 14, "bold")).pack(pady=(20, 8))
        Label(self.left, text="Manage your bottle-cap collection", bg=theme.PANEL,
              fg=theme.MUTED, wraplength=180).pack(pady=(0, 16))

        theme.AccentButton(self.left, text="Search by Image", command=self._trigger_image_search, width=18).pack(pady=6, padx=pad)
        theme.GhostButton(self.left, text="Show All", command=self._show_all).pack(pady=6, padx=pad, fill=X)
        theme.GhostButton(self.left, text="Export to Excel", command=self._export).pack(pady=6, padx=pad, fill=X)
        theme.GhostButton(self.left, text="Clear Selection", command=self._clear_selection).pack(pady=6, padx=pad, fill=X)

    # ---------------- Main area ----------------
    def _build_main_area(self):
        # Search by Brand
        top = Frame(self.main, bg=theme.BG, pady=10)
        top.pack(fill=X, padx=16)

        Label(top, text="Search by Brand:", bg=theme.BG, fg=theme.TEXT).pack(side=LEFT, padx=(4, 6))
        self.brand_var = StringVar()
        self.brand_entry = Entry(top, textvariable=self.brand_var, bg=theme.PANEL, fg=theme.TEXT,
                                 insertbackground=theme.TEXT, relief=FLAT, width=30)
        self.brand_entry.pack(side=LEFT, padx=(0, 6))
        theme.GhostButton(top, text="Search", command=self.search_brand).pack(side=LEFT, padx=(6, 6))
        self.brand_entry.bind("<Return>", lambda e: self.search_brand())

        # Canvas con scroll
        container = Frame(self.main, bg=theme.BG)
        container.pack(fill=BOTH, expand=True, padx=16, pady=(8, 16))

        self.canvas = Canvas(container, bg=theme.BG, highlightthickness=0)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # Scrollbar opcional
        self.scrollbar = Scrollbar(container, orient=VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self._create_cards_frame()

        self._show_all()

    def _create_cards_frame(self):
        # Creamos el frame de cards desde cero para evitar espacio fantasma
        self.canvas.delete("all")
        self.cards_frame = Frame(self.canvas, bg=theme.BG)
        self.cards_window = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.cards_frame.bind("<Configure>", lambda e: self._update_scrollregion())

    def _update_scrollregion(self):
        # Limitamos scroll para que no deje espacio vacío arriba/abajo
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox("all")
        if bbox:
            x1, y1, x2, y2 = bbox
            canvas_height = self.canvas.winfo_height()
            scroll_height = max(y2, canvas_height)
            self.canvas.configure(scrollregion=(x1, y1, x2, scroll_height))

    def _on_mousewheel(self, event):
        # Scroll limitado arriba/abajo
        y1, y2 = self.canvas.yview()
        if (y1 <= 0 and event.delta > 0) or (y2 >= 1 and event.delta < 0):
            return
        self.canvas.yview_scroll(-int(event.delta / 120), "units")

    # ---------------- Actions ----------------
    def _clear_selection(self):
        self.brand_var.set("")
        self._create_cards_frame()
        Label(self.cards_frame, text="No results found.", bg=theme.BG, fg=theme.MUTED).pack(pady=24)
        self.canvas.yview_moveto(0)

    def _export(self):
        try:
            archivo = fn.exportar_a_excel_version()
            messagebox.showinfo("Export", f"Export saved to:\n{archivo}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not export: {e}")

    def _trigger_image_search(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg")])
        if path:
            self._search_by_image(path)

    def _show_all(self):
        rows = fn.obtener_todas_chapas()
        self._display_cards(rows)

    def search_brand(self):
        text = self.brand_var.get().strip()
        if not text:
            self._show_all()
            return
        rows = fn.buscar_por_marca(text)
        self._display_cards(rows)

    # ---------------- Image search ----------------
    def _search_by_image(self, path):
        self.status_var.set("Searching by image...")
        self.root.update_idletasks()
        threading.Thread(target=self._do_search_image, args=(path,), daemon=True).start()

    def _do_search_image(self, path):
        try:
            results = fn.buscar_por_imagen(path, top_k=5)
            self.status_var.set(f"Found {len(results)} results")
            self.root.after(50, lambda: [self._display_cards(results), self.canvas.yview_moveto(0)])
        except Exception as e:
            self.status_var.set("Error searching image")
            messagebox.showerror("Error", str(e))

    # ---------------- Display cards ----------------
    def _display_cards(self, items):
        self._create_cards_frame()  # recrea frame para eliminar cualquier espacio fantasma

        if not items:
            Label(self.cards_frame, text="No results found.", bg=theme.BG, fg=theme.MUTED).pack(pady=24)
            self.canvas.yview_moveto(0)
            return

        for i, item in enumerate(items):
            fila = item[0] if isinstance(item, tuple) and len(item) == 2 else item

            card = Frame(self.cards_frame, bg=theme.CARD, relief=FLAT)
            pad_top = 0 if i == 0 else 4
            card.pack(fill=X, pady=(pad_top, 4), padx=6)

            thumb_frame = Frame(card, width=120, height=96, bg=theme.CARD)
            thumb_frame.pack_propagate(False)
            thumb_frame.pack(side=LEFT)

            try:
                img_path = fila[3]
                img = Image.open(img_path)
                img.thumbnail((92, 92), Image.LANCZOS)
                thumb = ImageOps.expand(img, border=2, fill="#151515")
                tkimg = ImageTk.PhotoImage(thumb)
                lbl_img = Label(thumb_frame, image=tkimg, bg=theme.CARD)
                lbl_img.image = tkimg
                lbl_img.pack(expand=True, pady=6, padx=6)
            except:
                Label(thumb_frame, text="No image", bg=theme.CARD, fg=theme.MUTED).pack(expand=True)

            info_frame = Frame(card, bg=theme.CARD)
            info_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=12)

            marca = fila[1] if len(fila) > 1 else "N/A"
            tipo = fila[2] if len(fila) > 2 else "N/A"
            Label(info_frame, text=f"{marca}", bg=theme.CARD, fg=theme.TEXT, font=("Segoe UI", 11, "bold")).pack(anchor="w")
            Label(info_frame, text=f"Type: {tipo}", bg=theme.CARD, fg=theme.MUTED).pack(anchor="w", pady=(2, 8))

        self._update_scrollregion()
        self.canvas.yview_moveto(0)

if __name__ == "__main__":
    root = Tk()
    app = App(root)
    root.mainloop()
