import os
import sys
import json
import re
import unicodedata
import shutil
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from PIL import Image, ImageOps, ImageTk


# ----------------------------
# Config
# ----------------------------
CATEGORIES = [
    ("marca", "Marca"),
    ("redes", "Redes"),
    ("promo", "Promo"),
    ("web", "Web"),
    ("musica", "Música"),
    ("all", "General"),
]

DEFAULT_MAX_LONG_SIDE = 1600
JPEG_QUALITY = 88

TICKER_CONFIG_FILE = "assets/ticker.config.json"
SITE_CONFIG_FILE = "assets/site.config.json"

DEFAULT_TICKER_CFG = {
    "mode": "auto",  # auto | custom
    "custom_rss_url": "",
    "speed_seconds": 55
}


# Minimal default site config (only if file missing)
DEFAULT_SITE_CFG = {
  "brand": {"name":"EJE VISUAL","tagline":"Diseño rápido · Precio claro","site_title":"EJE VISUAL — Diseño rápido. Precio claro.","meta_description":"EJE VISUAL: diseño gráfico, branding y contenido visual."},
  "contact": {"whatsapp_phone":"526633220567","phone_display":"(663) 322-0567","email":"ejevisualtj@gmail.com","hours":"10:00–18:00","facebook_url":"","instagram_url":"","location":"Tijuana, BC"},
  "home": {"hero_kicker":"Diseño que comunica, sin complicaciones.","hero_title_html":"Tu marca se nota.<br/>Tu mensaje se entiende.","hero_lead":"Soluciones visuales claras para negocios reales.","cta_primary":{"label":"Pedir cotización","href":"#contacto","kind":"whatsapp"},"cta_secondary":{"label":"Ver servicios","href":"#servicios"},"cta_tertiary":{"label":"Ver portafolio","href":"portfolio.html"},"pills":["FB / IG / WhatsApp","Entrega digital","Proceso simple"]},
  "services": {"section_title":"Servicios que resuelven","section_subtitle":"Rutas claras para urgencias, redes y marca.","cards":{}},
  "contact_form": {"title":"Cotización rápida","subtitle":"Esto abre WhatsApp con tu mensaje listo (editable).","service_options":["Imagen para redes","Flyer / cartel digital","Identidad visual","Web","Música"]},
  "tools_page": {"hero_kicker":"Herramientas","hero_title":"Stack de trabajo","hero_lead":"Herramientas reales para entregar rápido y con calidad.","cards":[]},
  "footer": {"note":"Diseño funcional para negocios reales.","copyright":"© {year} EJE VISUAL"},
  "policies": {"privacy_title":"Aviso de Privacidad","privacy_paragraphs":[],"terms_title":"Términos y Condiciones","terms_paragraphs":[]}
}


# ----------------------------
# Helpers
# ----------------------------
def slugify(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s-]+", "", text)
    text = re.sub(r"[\s_-]+", "-", text).strip("-")
    return text or "proyecto"


def now_iso() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def backup_file(path: Path, backup_dir: Path) -> None:
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = backup_dir / f"{path.name}.{ts}.bak"
    if path.exists():
        dest.write_bytes(path.read_bytes())


def move_to_trash(file_path: Path, trash_dir: Path) -> Path:
    trash_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = trash_dir / f"{file_path.stem}.{ts}{file_path.suffix}"
    shutil.move(str(file_path), str(dest))
    return dest


def safe_copy(src: Path, dst: Path) -> None:
    dst.write_bytes(src.read_bytes())


def ensure_project_structure(root: Path) -> Dict[str, Path]:
    index = root / "index.html"
    assets = root / "assets"
    portfolio = assets / "portfolio"
    manifest = assets / "portfolio.manifest.json"
    ticker_js = assets / "ticker.js"
    ticker_cfg = root / TICKER_CONFIG_FILE
    site_cfg = root / SITE_CONFIG_FILE

    if not index.exists():
        raise FileNotFoundError("No encontré index.html en la ruta seleccionada.")
    if not assets.exists():
        raise FileNotFoundError("No encontré la carpeta assets/ en la ruta seleccionada.")
    if not portfolio.exists():
        raise FileNotFoundError("No encontré assets/portfolio/.")
    if not manifest.exists():
        manifest.write_text(json.dumps({"items": []}, indent=2, ensure_ascii=False), encoding="utf-8")
    if not site_cfg.exists():
        site_cfg.parent.mkdir(parents=True, exist_ok=True)
        site_cfg.write_text(json.dumps(DEFAULT_SITE_CFG, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "root": root,
        "assets": assets,
        "portfolio": portfolio,
        "manifest": manifest,
        "ticker_js": ticker_js,
        "ticker_cfg": ticker_cfg,
        "site_cfg": site_cfg,
        "backups": assets / "_backups",
    }


def load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_manifest(manifest_path: Path) -> Dict:
    data = load_json(manifest_path, {"items": []})
    if isinstance(data, list):
        return {"items": [it for it in data if isinstance(it, dict)]}
    if isinstance(data, dict) and isinstance(data.get("items"), list):
        data["items"] = [it for it in data["items"] if isinstance(it, dict)]
        return data
    return {"items": []}


def save_manifest(manifest_path: Path, data: Dict) -> None:
    save_json(manifest_path, data)


def unique_filename(dest_dir: Path, base_name: str, ext: str = ".jpg") -> str:
    cand = f"{base_name}{ext}"
    if not (dest_dir / cand).exists():
        return cand
    i = 2
    while True:
        cand = f"{base_name}-{i}{ext}"
        if not (dest_dir / cand).exists():
            return cand
        i += 1


def process_image(in_path: Path, out_path: Path, max_long_side: int) -> None:
    img = Image.open(in_path)
    img = ImageOps.exif_transpose(img)

    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (0, 0, 0))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")

    w, h = img.size
    long_side = max(w, h)
    if long_side > max_long_side:
        scale = max_long_side / long_side
        new_size = (int(w * scale), int(h * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)


# ----------------------------
# Ticker config + patching
# ----------------------------
def load_ticker_cfg(cfg_path: Path) -> Dict:
    data = load_json(cfg_path, dict(DEFAULT_TICKER_CFG))
    if isinstance(data, dict):
        out = dict(DEFAULT_TICKER_CFG)
        out.update(data)
        return out
    return dict(DEFAULT_TICKER_CFG)


def patch_ticker_js_if_needed(ticker_js_path: Path) -> bool:
    if not ticker_js_path.exists():
        return False
    txt = ticker_js_path.read_text(encoding="utf-8", errors="ignore")
    if "EV_TICKER_CONFIG_URL" in txt:
        return True

    injected = """
  // ===== EJE VISUAL Ticker Config (patched by Site Manager) =====
  const EV_TICKER_CONFIG_URL = "assets/ticker.config.json";
  let EV_CFG = { mode: "auto", custom_rss_url: "", speed_seconds: 55 };

  async function EV_loadCfg(){
    try{
      const r = await fetch(EV_TICKER_CONFIG_URL, { cache: "no-store" });
      if(r.ok){
        const j = await r.json();
        EV_CFG = Object.assign(EV_CFG, j || {});
      }
    }catch(e){}
  }
"""
    marker = "if(!tTrack) return;"
    if marker in txt:
        txt = txt.replace(marker, marker + injected)
    else:
        txt = txt.replace("(function(){", "(function(){\n" + injected)

    txt = re.sub(r'async function load\(\)\{\s*', 'async function load(){\n    await EV_loadCfg();\n', txt, count=1)
    txt = txt.replace("const base = 44;", "const base = Number((EV_CFG && EV_CFG.speed_seconds) || 44);")

    m = re.search(r'const url\s*=\s*`https://news\.google\.com/rss/search\?[^`]+`;', txt)
    if m:
        auto_line = m.group(0)
        auto_url = auto_line.replace("const url", "const autoUrl")
        replacement = auto_url + "\n\n    const url = (EV_CFG.mode === \"custom\" && EV_CFG.custom_rss_url)\n      ? EV_CFG.custom_rss_url\n      : autoUrl;\n"
        txt = txt.replace(auto_line, replacement)

    ticker_js_path.write_text(txt, encoding="utf-8")
    return True


# ----------------------------
# Site Manager App
# ----------------------------
class SiteManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EJE VISUAL — Site Manager v3")
        self.geometry("1220x780")
        self.minsize(1220, 780)

        self.project_root = tk.StringVar(value=str(Path.cwd()))
        self.max_side = tk.IntVar(value=DEFAULT_MAX_LONG_SIDE)
        self.category_key = tk.StringVar(value="marca")
        self.title_text = tk.StringVar(value="")
        self.selected_files: List[str] = []
        self.auto_recents = tk.BooleanVar(value=True)

        self.paths: Optional[Dict[str, Path]] = None
        self.manifest: Dict = {"items": []}
        self.site_cfg: Dict = dict(DEFAULT_SITE_CFG)

        self.ticker_mode = tk.StringVar(value="auto")
        self.ticker_url = tk.StringVar(value="")
        self.ticker_speed = tk.IntVar(value=55)

        self._large_preview: Optional[ImageTk.PhotoImage] = None
        self._drag_item = None

        self._build_ui()
        self._try_load_project()

    # ---------- UI ----------
    def _style(self):
        try:
            style = ttk.Style()
            style.theme_use("clam")
        except Exception:
            style = ttk.Style()
        self.option_add("*Font", ("Segoe UI", 10))
        style.configure("Muted.TLabel", foreground="#777")
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        self._style()

        top = ttk.Frame(self)
        top.pack(fill="x", padx=14, pady=12)
        ttk.Label(top, text="Ruta del proyecto (donde está index.html):", style="Muted.TLabel").pack(anchor="w")

        row = ttk.Frame(top)
        row.pack(fill="x", pady=(8, 0))
        row.columnconfigure(0, weight=1)
        ttk.Entry(row, textvariable=self.project_root).grid(row=0, column=0, sticky="ew")
        ttk.Button(row, text="Buscar…", command=self.pick_project_root).grid(row=0, column=1, padx=(10, 0))
        ttk.Button(row, text="Cargar", command=self._try_load_project).grid(row=0, column=2, padx=(10, 0))

        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=14, pady=12)

        # Tabs
        self.tab_add = ttk.Frame(self.nb)
        self.tab_lib = ttk.Frame(self.nb)
        self.tab_recent = ttk.Frame(self.nb)
        self.tab_ticker = ttk.Frame(self.nb)
        self.tab_content = ttk.Frame(self.nb)
        self.tab_assets = ttk.Frame(self.nb)
        self.tab_diag = ttk.Frame(self.nb)

        self.nb.add(self.tab_add, text="Portafolio: Agregar")
        self.nb.add(self.tab_lib, text="Portafolio: Biblioteca")
        self.nb.add(self.tab_recent, text="Recientes")
        self.nb.add(self.tab_ticker, text="Ticker")
        self.nb.add(self.tab_content, text="Contenido del sitio (CMS)")
        self.nb.add(self.tab_assets, text="Assets (Logo/Favicon/Hero)")
        self.nb.add(self.tab_diag, text="Diagnóstico")

        self._build_add_tab()
        self._build_lib_tab()
        self._build_recent_tab()
        self._build_ticker_tab()
        self._build_content_tab()
        self._build_assets_tab()
        self._build_diag_tab()

        logbox = ttk.LabelFrame(self, text="Log")
        logbox.pack(fill="both", expand=False, padx=14, pady=(0, 14))
        self.log = tk.Text(logbox, height=7, wrap="word")
        self.log.pack(fill="both", expand=True, padx=10, pady=10)

    # ---------- Common ----------
    def log_line(self, msg: str):
        self.log.insert("end", msg + "\n")
        self.log.see("end")

    def pick_project_root(self):
        folder = filedialog.askdirectory(title="Selecciona la raíz del proyecto")
        if folder:
            self.project_root.set(folder)

    def _try_load_project(self):
        try:
            root = Path(self.project_root.get()).resolve()
            self.paths = ensure_project_structure(root)
            self.manifest = load_manifest(self.paths["manifest"])
            self.site_cfg = load_json(self.paths["site_cfg"], dict(DEFAULT_SITE_CFG))
            if not isinstance(self.site_cfg, dict):
                self.site_cfg = dict(DEFAULT_SITE_CFG)

            self._refresh_library()
            self._refresh_recents()
            self._load_ticker_settings()
            self._load_content_forms()
            self._refresh_assets_preview()
            self.log_line(f"✅ Proyecto cargado: {root}")
        except Exception as e:
            self.paths = None
            self.manifest = {"items": []}
            self.site_cfg = dict(DEFAULT_SITE_CFG)
            messagebox.showerror("No se pudo cargar", str(e))

    # ---------- Add Tab ----------
    def _build_add_tab(self):
        frm = ttk.Frame(self.tab_add, padding=14)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Agregar nuevas imágenes al portafolio", style="Title.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(frm, text="Imágenes:", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(14, 0))
        self.add_files_label = ttk.Label(frm, text="(ninguna seleccionada)")
        self.add_files_label.grid(row=1, column=1, sticky="w", pady=(14, 0))
        ttk.Button(frm, text="Seleccionar…", command=self.pick_images).grid(row=1, column=2, padx=(10, 0), pady=(14, 0))

        ttk.Label(frm, text="Categoría:", style="Muted.TLabel").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self.cat_menu = ttk.Combobox(frm, state="readonly",
                                     values=[f"{k} — {label}" for k, label in CATEGORIES])
        self.cat_menu.grid(row=2, column=1, sticky="w", pady=(12, 0))
        self.cat_menu.current(0)
        self.cat_menu.bind("<<ComboboxSelected>>", lambda _e: self._on_cat_change())
        self._on_cat_change()

        ttk.Label(frm, text="Nombre del proyecto (Title):", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(frm, textvariable=self.title_text).grid(row=3, column=1, sticky="ew", pady=(12, 0))

        ttk.Label(frm, text="Max lado largo (px):", style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Spinbox(frm, from_=800, to=4000, textvariable=self.max_side, width=12).grid(row=4, column=1, sticky="w", pady=(12, 0))

        ttk.Checkbutton(frm, text="Auto-actualizar 'Recientes' con los últimos 3 agregados", variable=self.auto_recents)\
            .grid(row=5, column=0, columnspan=2, sticky="w", pady=(12, 0))

        ttk.Button(frm, text="Procesar y Agregar", style="Accent.TButton", command=self.add_images).grid(row=6, column=0, sticky="w", pady=(18, 0))
        ttk.Label(frm, text="Optimiza, copia a assets/portfolio/ y actualiza portfolio.manifest.json", style="Muted.TLabel").grid(row=6, column=1, sticky="w", pady=(18, 0))

    def _on_cat_change(self):
        val = self.cat_menu.get().split("—")[0].strip()
        self.category_key.set(val)

    def pick_images(self):
        files = filedialog.askopenfilenames(
            title="Selecciona imágenes",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.webp *.gif *.avif"), ("Todos", "*.*")]
        )
        if files:
            self.selected_files = list(files)
            self.add_files_label.config(text=f"{len(files)} archivo(s) seleccionado(s)")

    def add_images(self):
        if not self.paths:
            messagebox.showwarning("Proyecto", "Carga primero un proyecto válido.")
            return
        if not self.selected_files:
            messagebox.showwarning("Imagen", "Selecciona al menos una imagen.")
            return
        title = self.title_text.get().strip()
        if not title:
            messagebox.showwarning("Nombre", "Escribe el nombre del proyecto.")
            return

        port_dir = self.paths["portfolio"]
        manifest_path = self.paths["manifest"]
        data = load_manifest(manifest_path)

        cat = self.category_key.get().strip().lower()
        slug = slugify(title)
        base = f"{cat}__{slug}" if cat != "all" else slug
        max_side = int(self.max_side.get())

        existing_files = {it.get("file") for it in data.get("items", []) if isinstance(it, dict)}
        backup_file(manifest_path, self.paths["backups"])

        stamp = now_iso()

        for f in self.selected_files:
            in_path = Path(f)
            out_name = unique_filename(port_dir, base, ".jpg")
            out_path = port_dir / out_name

            process_image(in_path, out_path, max_side)
            self.log_line(f"✅ Guardado: assets/portfolio/{out_name}")

            if out_name not in existing_files:
                data["items"].insert(0, {"file": out_name, "category": cat, "title": title, "added_at": stamp})
                existing_files.add(out_name)

        save_manifest(manifest_path, data)
        self.manifest = data

        if self.auto_recents.get():
            self.update_recents_from_latest()

        self._refresh_library()
        self._refresh_recents()
        messagebox.showinfo("Listo", "Imágenes agregadas y manifest actualizado.\nAbre la web con servidor local para ver cambios.")

    # ---------- Library Tab ----------
    def _build_lib_tab(self):
        outer = ttk.Frame(self.tab_lib, padding=14)
        outer.pack(fill="both", expand=True)

        left = ttk.Frame(outer)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(outer, width=360)
        right.pack(side="right", fill="y", padx=(14, 0))

        toolbar = ttk.Frame(left)
        toolbar.pack(fill="x", pady=(0, 10))

        ttk.Button(toolbar, text="Refrescar", command=self._refresh_library).pack(side="left")
        ttk.Button(toolbar, text="▲", width=3, command=lambda: self.move_selected(-1)).pack(side="left", padx=(8,0))
        ttk.Button(toolbar, text="▼", width=3, command=lambda: self.move_selected(+1)).pack(side="left", padx=(4,0))
        ttk.Button(toolbar, text="Guardar orden", style="Accent.TButton", command=self.save_order).pack(side="left", padx=(10,0))

        ttk.Button(toolbar, text="Borrar", command=self.delete_selected).pack(side="right")
        ttk.Button(toolbar, text="Renombrar archivo", command=self.rename_file_selected).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Cambiar título", command=self.rename_title_selected).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Cambiar categoría", command=self.change_category_selected).pack(side="right", padx=(8, 0))

        search_row = ttk.Frame(left)
        search_row.pack(fill="x", pady=(0, 8))
        ttk.Label(search_row, text="Buscar:", style="Muted.TLabel").pack(side="left")
        self.search_var = tk.StringVar(value="")
        ent = ttk.Entry(search_row, textvariable=self.search_var)
        ent.pack(side="left", fill="x", expand=True, padx=(8,0))
        ent.bind("<KeyRelease>", lambda _e: self._refresh_library())

        cols = ("file", "category", "title", "added_at")
        self.tree = ttk.Treeview(left, columns=cols, show="headings", height=21, selectmode="browse")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("file", width=300)
        self.tree.column("category", width=70)
        self.tree.column("title", width=440)
        self.tree.column("added_at", width=150)

        vsb = ttk.Scrollbar(left, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # drag reorder
        self.tree.bind("<ButtonPress-1>", self._on_tree_press)
        self.tree.bind("<B1-Motion>", self._on_tree_drag)
        self.tree.bind("<ButtonRelease-1>", self._on_tree_release)

        self.tree.bind("<<TreeviewSelect>>", lambda _e: self.update_preview())

        ttk.Label(right, text="Preview", style="Title.TLabel").pack(anchor="w")
        self.preview_img_label = ttk.Label(right)
        self.preview_img_label.pack(fill="x", pady=(10, 0))
        self.preview_meta = ttk.Label(right, text="Selecciona un item…", style="Muted.TLabel", justify="left")
        self.preview_meta.pack(fill="x", pady=(10, 0))

        ttk.Separator(right).pack(fill="x", pady=14)
        ttk.Button(right, text="Set como reciente-1", command=lambda: self.set_recent_from_selected(1)).pack(fill="x")
        ttk.Button(right, text="Set como reciente-2", command=lambda: self.set_recent_from_selected(2)).pack(fill="x", pady=(8,0))
        ttk.Button(right, text="Set como reciente-3", command=lambda: self.set_recent_from_selected(3)).pack(fill="x", pady=(8,0))
        ttk.Separator(right).pack(fill="x", pady=14)
        ttk.Button(right, text="Abrir carpeta portfolio", command=self.open_portfolio_folder).pack(fill="x")

    def _refresh_library(self):
        if not self.paths:
            return
        self.tree.delete(*self.tree.get_children())
        self.manifest = load_manifest(self.paths["manifest"])

        q = self.search_var.get().strip().lower() if hasattr(self, "search_var") else ""
        for it in self.manifest.get("items", []):
            file = it.get("file","")
            cat = it.get("category","")
            title = it.get("title","")
            added = it.get("added_at","")
            rowtxt = f"{file} {cat} {title} {added}".lower()
            if q and q not in rowtxt:
                continue
            self.tree.insert("", "end", values=(file, cat, title, added))

        self.update_preview()

    def _get_selected_values(self) -> Optional[Tuple[str,str,str,str]]:
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return None
        return vals[0], vals[1], vals[2], vals[3]

    def get_selected_item(self) -> Optional[Dict]:
        vals = self._get_selected_values()
        if not vals:
            return None
        return {"file": vals[0], "category": vals[1], "title": vals[2], "added_at": vals[3]}

    def _on_tree_press(self, event):
        self._drag_item = self.tree.identify_row(event.y)

    def _on_tree_drag(self, event):
        if not self._drag_item:
            return
        target = self.tree.identify_row(event.y)
        if target and target != self._drag_item:
            self.tree.move(self._drag_item, "", self.tree.index(target))
            self._drag_item = target

    def _on_tree_release(self, event):
        self._drag_item = None

    def move_selected(self, direction: int):
        sel = self.tree.selection()
        if not sel:
            return
        item = sel[0]
        idx = self.tree.index(item)
        new_idx = max(0, min(idx + direction, len(self.tree.get_children()) - 1))
        if new_idx == idx:
            return
        self.tree.move(item, "", new_idx)
        self.tree.selection_set(item)

    def save_order(self):
        if not self.paths:
            return
        manifest_path = self.paths["manifest"]
        backup_file(manifest_path, self.paths["backups"])

        order_files = []
        for iid in self.tree.get_children():
            vals = self.tree.item(iid, "values")
            if vals:
                order_files.append(vals[0])

        data = load_manifest(manifest_path)
        by_file = {it.get("file"): it for it in data.get("items", []) if isinstance(it, dict)}

        new_items = [by_file[f] for f in order_files if f in by_file]
        remaining = [it for it in data.get("items", []) if isinstance(it, dict) and it.get("file") not in set(order_files)]
        data["items"] = new_items + remaining

        save_manifest(manifest_path, data)
        self.manifest = data
        self.log_line("✅ Orden guardado en portfolio.manifest.json")
        messagebox.showinfo("Listo", "Orden guardado. Recarga tu web para verlo.")

    def update_preview(self):
        if not self.paths:
            return
        item = self.get_selected_item()
        if not item:
            self.preview_img_label.config(image="")
            self.preview_meta.config(text="Selecciona un item…")
            return

        port = self.paths["portfolio"]
        fp = port / item["file"]

        meta = f"Archivo: {item['file']}\nCategoría: {item['category']}\nTítulo: {item['title']}"
        if item.get("added_at"):
            meta += f"\nAgregado: {item['added_at']}"

        if fp.exists():
            try:
                img = Image.open(fp)
                img = ImageOps.exif_transpose(img)
                img_thumb = img.copy()
                img_thumb.thumbnail((340, 240), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img_thumb)
                self._large_preview = tk_img
                self.preview_img_label.config(image=tk_img)
                meta += f"\nTamaño: {img.size[0]}x{img.size[1]}"
            except Exception:
                self.preview_img_label.config(image="")
                meta += "\n(Preview no disponible)"
        else:
            self.preview_img_label.config(image="")
            meta += "\n(Archivo no existe en disco)"

        self.preview_meta.config(text=meta)

    def delete_selected(self):
        if not self.paths:
            return
        item = self.get_selected_item()
        if not item:
            messagebox.showwarning("Selecciona", "Selecciona un elemento en la lista.")
            return
        if not messagebox.askyesno("Confirmar", f"¿Mover a Trash y quitar del portafolio?\n\n{item['file']}"):
            return

        port_dir = self.paths["portfolio"]
        file_path = port_dir / item["file"]
        trash_dir = port_dir / "_trash"
        manifest_path = self.paths["manifest"]
        backup_file(manifest_path, self.paths["backups"])

        data = load_manifest(manifest_path)
        data["items"] = [it for it in data.get("items", []) if not (isinstance(it, dict) and it.get("file") == item["file"])]

        if file_path.exists():
            moved = move_to_trash(file_path, trash_dir)
            self.log_line(f"🗑️ Movido a Trash: {moved.relative_to(self.paths['root'])}")
        else:
            self.log_line("⚠️ Archivo no encontrado en disco, solo actualicé manifest.")

        save_manifest(manifest_path, data)
        self.manifest = data
        self._refresh_library()
        self._refresh_recents()

    def rename_title_selected(self):
        if not self.paths:
            return
        item = self.get_selected_item()
        if not item:
            messagebox.showwarning("Selecciona", "Selecciona un elemento en la lista.")
            return
        new_title = simpledialog.askstring("Cambiar título", "Nuevo título:", initialvalue=item["title"])
        if not new_title:
            return

        manifest_path = self.paths["manifest"]
        backup_file(manifest_path, self.paths["backups"])
        data = load_manifest(manifest_path)
        for it in data.get("items", []):
            if isinstance(it, dict) and it.get("file") == item["file"]:
                it["title"] = new_title.strip()
        save_manifest(manifest_path, data)
        self.manifest = data
        self._refresh_library()
        self.log_line(f"✏️ Título actualizado: {item['file']} → {new_title.strip()}")

    def rename_file_selected(self):
        if not self.paths:
            return
        item = self.get_selected_item()
        if not item:
            messagebox.showwarning("Selecciona", "Selecciona un elemento en la lista.")
            return
        new_base = simpledialog.askstring("Renombrar archivo", "Nuevo nombre (sin extensión):", initialvalue=Path(item["file"]).stem)
        if not new_base:
            return
        new_base = slugify(new_base)

        port_dir = self.paths["portfolio"]
        old_path = port_dir / item["file"]
        if not old_path.exists():
            messagebox.showerror("Archivo faltante", "No se encontró el archivo en assets/portfolio/")
            return

        new_name = unique_filename(port_dir, new_base, old_path.suffix.lower() or ".jpg")
        new_path = port_dir / new_name

        manifest_path = self.paths["manifest"]
        backup_file(manifest_path, self.paths["backups"])

        old_path.rename(new_path)
        self.log_line(f"🔁 Renombrado: {old_path.name} → {new_path.name}")

        data = load_manifest(manifest_path)
        for it in data.get("items", []):
            if isinstance(it, dict) and it.get("file") == item["file"]:
                it["file"] = new_name
        save_manifest(manifest_path, data)
        self.manifest = data
        self._refresh_library()
        self._refresh_recents()

    def change_category_selected(self):
        if not self.paths:
            return
        item = self.get_selected_item()
        if not item:
            messagebox.showwarning("Selecciona", "Selecciona un elemento en la lista.")
            return
        cat = simpledialog.askstring("Cambiar categoría", "Categoría key (marca/redes/promo/web/musica/all):", initialvalue=item["category"])
        if not cat:
            return
        cat = cat.strip().lower()
        valid = [k for k,_ in CATEGORIES]
        if cat not in valid:
            messagebox.showerror("Categoría", "Categoría inválida.")
            return

        manifest_path = self.paths["manifest"]
        backup_file(manifest_path, self.paths["backups"])
        data = load_manifest(manifest_path)
        for it in data.get("items", []):
            if isinstance(it, dict) and it.get("file") == item["file"]:
                it["category"] = cat
        save_manifest(manifest_path, data)
        self.manifest = data
        self._refresh_library()
        self.log_line(f"🏷️ Categoría actualizada: {item['file']} → {cat}")

    def open_portfolio_folder(self):
        if not self.paths:
            return
        folder = self.paths["portfolio"]
        try:
            if os.name == "nt":
                os.startfile(folder)  # type: ignore
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')
        except Exception:
            messagebox.showinfo("Ruta", str(folder))

    # ---------- Recents Tab ----------
    def _build_recent_tab(self):
        frm = ttk.Frame(self.tab_recent, padding=14)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Recientes (Home)", style="Title.TLabel").pack(anchor="w")
        ttk.Label(frm, text="Auto (últimos 3 agregados) o manual.", style="Muted.TLabel").pack(anchor="w", pady=(6, 18))

        self.rec_labels = {}
        self.rec_previews = {}

        for i in range(1, 4):
            row = ttk.Frame(frm)
            row.pack(fill="x", pady=(0, 14))

            left = ttk.Frame(row)
            left.pack(side="left", fill="x", expand=True)

            ttk.Label(left, text=f"Slot {i}:", style="Muted.TLabel").pack(anchor="w")
            lab = ttk.Label(left, text=f"reciente-{i}.jpg")
            lab.pack(anchor="w")
            self.rec_labels[i] = lab

            prev = ttk.Label(row)
            prev.pack(side="right")
            self.rec_previews[i] = prev

            btns = ttk.Frame(row)
            btns.pack(side="right", padx=(0, 12))
            ttk.Button(btns, text="Elegir desde Biblioteca…", command=lambda s=i: self.set_recent_from_library(s)).pack(fill="x")
            ttk.Button(btns, text="Limpiar", command=lambda s=i: self.clear_recent(s)).pack(fill="x", pady=(8, 0))

        ttk.Button(frm, text="Auto-recientes ahora (últimos 3 agregados)", style="Accent.TButton",
                   command=self.update_recents_from_latest).pack(anchor="w", pady=(18,0))

    def _refresh_recents(self):
        if not self.paths:
            return
        port = self.paths["portfolio"]
        for i in range(1, 4):
            fp = port / f"reciente-{i}.jpg"
            self.rec_labels[i].config(text=fp.name if fp.exists() else "(vacío)")
            if fp.exists():
                try:
                    img = Image.open(fp)
                    img = ImageOps.exif_transpose(img)
                    img.thumbnail((200, 130), Image.Resampling.LANCZOS)
                    tk_img = ImageTk.PhotoImage(img)
                    self.rec_previews[i].config(image=tk_img)
                    self.rec_previews[i].image = tk_img
                except Exception:
                    self.rec_previews[i].config(image="")
            else:
                self.rec_previews[i].config(image="")

    def set_recent_from_library(self, slot: int):
        if not self.paths:
            return
        items = [it for it in self.manifest.get("items", []) if isinstance(it, dict)]
        if not items:
            messagebox.showinfo("Biblioteca vacía", "No hay items en el manifest.")
            return

        dlg = tk.Toplevel(self)
        dlg.title(f"Elegir para reciente-{slot}.jpg")
        dlg.geometry("860x480")
        dlg.transient(self)
        dlg.grab_set()

        cols = ("file", "category", "title")
        tree = ttk.Treeview(dlg, columns=cols, show="headings", height=16, selectmode="browse")
        for c in cols:
            tree.heading(c, text=c)
        tree.column("file", width=300)
        tree.column("category", width=90)
        tree.column("title", width=440)
        tree.pack(fill="both", expand=True, padx=12, pady=12)

        for it in items:
            tree.insert("", "end", values=(it.get("file",""), it.get("category",""), it.get("title","")))

        def choose():
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            fname = vals[0]
            src = self.paths["portfolio"] / fname
            dst = self.paths["portfolio"] / f"reciente-{slot}.jpg"
            if not src.exists():
                messagebox.showerror("Falta archivo", "No existe el archivo en assets/portfolio/")
                return
            safe_copy(src, dst)
            self.log_line(f"⭐ reciente-{slot}.jpg ← {fname}")
            self._refresh_recents()
            dlg.destroy()

        ttk.Button(dlg, text="Asignar a reciente", command=choose).pack(pady=(0, 12))

    def clear_recent(self, slot: int):
        if not self.paths:
            return
        fp = self.paths["portfolio"] / f"reciente-{slot}.jpg"
        if fp.exists():
            if not messagebox.askyesno("Confirmar", f"¿Borrar {fp.name}?"):
                return
            trash = self.paths["portfolio"] / "_trash"
            moved = move_to_trash(fp, trash)
            self.log_line(f"🗑️ {fp.name} movido a Trash: {moved.name}")
        self._refresh_recents()

    def update_recents_from_latest(self):
        if not self.paths:
            return
        port = self.paths["portfolio"]
        data = load_manifest(self.paths["manifest"])
        items = [it for it in data.get("items", []) if isinstance(it, dict)]

        def key(it):
            return it.get("added_at") or ""

        items_sorted = sorted(items, key=key, reverse=True)
        latest = [it for it in items_sorted if (port / it.get("file","")).exists()][:3]

        for idx, it in enumerate(latest, start=1):
            safe_copy(port / it["file"], port / f"reciente-{idx}.jpg")
            self.log_line(f"⭐ Auto reciente-{idx}.jpg ← {it['file']}")
        self._refresh_recents()

    def set_recent_from_selected(self, slot: int):
        if not self.paths:
            return
        item = self.get_selected_item()
        if not item:
            return
        port = self.paths["portfolio"]
        src = port / item["file"]
        if not src.exists():
            messagebox.showerror("Falta archivo", "No existe el archivo en assets/portfolio/")
            return
        safe_copy(src, port / f"reciente-{slot}.jpg")
        self.log_line(f"⭐ reciente-{slot}.jpg ← {item['file']}")
        self._refresh_recents()

    # ---------- Ticker Tab ----------
    def _build_ticker_tab(self):
        frm = ttk.Frame(self.tab_ticker, padding=14)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Ticker", style="Title.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(frm, text="Velocidad + RSS URL (Auto o Custom).", style="Muted.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 18))

        ttk.Label(frm, text="Modo:", style="Muted.TLabel").grid(row=2, column=0, sticky="w")
        mode_row = ttk.Frame(frm)
        mode_row.grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(mode_row, text="Auto (local / Google)", variable=self.ticker_mode, value="auto").pack(side="left")
        ttk.Radiobutton(mode_row, text="Custom RSS URL", variable=self.ticker_mode, value="custom").pack(side="left", padx=(12, 0))

        ttk.Label(frm, text="RSS URL (modo custom):", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(frm, textvariable=self.ticker_url).grid(row=3, column=1, sticky="ew", pady=(12, 0))

        ttk.Label(frm, text="Velocidad (segundos por vuelta):", style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(12, 0))
        ttk.Scale(frm, from_=20, to=140, variable=self.ticker_speed, orient="horizontal").grid(row=4, column=1, sticky="ew", pady=(12, 0))
        self.speed_label = ttk.Label(frm, text="55s")
        self.speed_label.grid(row=4, column=2, sticky="w", padx=(10, 0))
        self.ticker_speed.trace_add("write", lambda *_: self.speed_label.config(text=f"{int(self.ticker_speed.get())}s"))

        ttk.Button(frm, text="Aplicar a la web", style="Accent.TButton", command=self.apply_ticker_settings).grid(row=5, column=0, sticky="w", pady=(18, 0))
        ttk.Label(frm, text="Guarda config y ajusta ticker.js si es necesario.", style="Muted.TLabel").grid(row=5, column=1, sticky="w", pady=(18, 0))

    def _load_ticker_settings(self):
        if not self.paths:
            return
        cfg = load_ticker_cfg(self.paths["ticker_cfg"])
        self.ticker_mode.set(cfg.get("mode","auto"))
        self.ticker_url.set(cfg.get("custom_rss_url",""))
        self.ticker_speed.set(int(cfg.get("speed_seconds", 55)))

    def apply_ticker_settings(self):
        if not self.paths:
            return
        cfg = {
            "mode": self.ticker_mode.get().strip(),
            "custom_rss_url": self.ticker_url.get().strip(),
            "speed_seconds": int(self.ticker_speed.get()),
        }
        if cfg["mode"] == "custom" and not cfg["custom_rss_url"]:
            if not messagebox.askyesno("RSS vacío", "Modo custom sin URL. ¿Continuar?"):
                return

        backup_file(self.paths["ticker_cfg"], self.paths["backups"])
        save_json(self.paths["ticker_cfg"], cfg)
        self.log_line(f"✅ ticker.config.json actualizado: mode={cfg['mode']} speed={cfg['speed_seconds']}s")

        if self.paths["ticker_js"].exists():
            backup_file(self.paths["ticker_js"], self.paths["backups"])
        ok = patch_ticker_js_if_needed(self.paths["ticker_js"])
        if ok:
            self.log_line("✅ ticker.js listo para leer ticker.config.json (parche aplicado o ya existía).")
            messagebox.showinfo("Ticker listo", "Cambios guardados. Recarga tu página para verlos.")
        else:
            messagebox.showwarning("Ticker", "No encontré assets/ticker.js. Solo guardé ticker.config.json.")

    # ---------- CMS (site.config.json) ----------
    def _build_content_tab(self):
        outer = ttk.Frame(self.tab_content, padding=14)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="Contenido del sitio (assets/site.config.json)", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Edita textos, links y listas sin tocar HTML. Guarda y recarga tu web.", style="Muted.TLabel").pack(anchor="w", pady=(6, 12))

        self.cms_nb = ttk.Notebook(outer)
        self.cms_nb.pack(fill="both", expand=True)

        self.cms_brand = ttk.Frame(self.cms_nb, padding=12)
        self.cms_home = ttk.Frame(self.cms_nb, padding=12)
        self.cms_services = ttk.Frame(self.cms_nb, padding=12)
        self.cms_tools = ttk.Frame(self.cms_nb, padding=12)
        self.cms_policies = ttk.Frame(self.cms_nb, padding=12)
        self.cms_raw = ttk.Frame(self.cms_nb, padding=12)

        self.cms_nb.add(self.cms_brand, text="Brand + Contacto")
        self.cms_nb.add(self.cms_home, text="Home (Hero)")
        self.cms_nb.add(self.cms_services, text="Servicios")
        self.cms_nb.add(self.cms_tools, text="Herramientas")
        self.cms_nb.add(self.cms_policies, text="Políticas")
        self.cms_nb.add(self.cms_raw, text="JSON (Avanzado)")

        self._build_cms_brand()
        self._build_cms_home()
        self._build_cms_services()
        self._build_cms_tools()
        self._build_cms_policies()
        self._build_cms_raw()

        btn_row = ttk.Frame(outer)
        btn_row.pack(fill="x", pady=(10,0))
        ttk.Button(btn_row, text="Guardar cambios", style="Accent.TButton", command=self.save_site_config).pack(side="left")
        ttk.Button(btn_row, text="Recargar desde archivo", command=self._try_load_project).pack(side="left", padx=(10,0))

    def _build_cms_brand(self):
        f = self.cms_brand
        f.columnconfigure(1, weight=1)

        self.cfg_brand_name = tk.StringVar()
        self.cfg_brand_tagline = tk.StringVar()
        self.cfg_brand_title = tk.StringVar()
        self.cfg_brand_desc = tk.StringVar()

        self.cfg_contact_whats = tk.StringVar()
        self.cfg_contact_phone = tk.StringVar()
        self.cfg_contact_email = tk.StringVar()
        self.cfg_contact_hours = tk.StringVar()
        self.cfg_contact_fb = tk.StringVar()
        self.cfg_contact_ig = tk.StringVar()
        self.cfg_contact_loc = tk.StringVar()

        row = 0
        ttk.Label(f, text="Marca", style="Title.TLabel").grid(row=row, column=0, sticky="w", pady=(0,8)); row+=1

        ttk.Label(f, text="Nombre:", style="Muted.TLabel").grid(row=row, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.cfg_brand_name).grid(row=row, column=1, sticky="ew"); row+=1

        ttk.Label(f, text="Tagline:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_brand_tagline).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Label(f, text="Título del sitio:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_brand_title).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Label(f, text="Meta description:", style="Muted.TLabel").grid(row=row, column=0, sticky="nw", pady=(8,0))
        self.brand_desc_box = tk.Text(f, height=4, wrap="word")
        self.brand_desc_box.grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Separator(f).grid(row=row, column=0, columnspan=2, sticky="ew", pady=14); row+=1
        ttk.Label(f, text="Contacto", style="Title.TLabel").grid(row=row, column=0, sticky="w", pady=(0,8)); row+=1

        ttk.Label(f, text="WhatsApp phone (5266...):", style="Muted.TLabel").grid(row=row, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.cfg_contact_whats).grid(row=row, column=1, sticky="ew"); row+=1

        ttk.Label(f, text="Teléfono display:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_contact_phone).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Label(f, text="Email:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_contact_email).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Label(f, text="Horario:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_contact_hours).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Label(f, text="Facebook URL:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_contact_fb).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Label(f, text="Instagram URL:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_contact_ig).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

        ttk.Label(f, text="Ubicación:", style="Muted.TLabel").grid(row=row, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_contact_loc).grid(row=row, column=1, sticky="ew", pady=(8,0)); row+=1

    def _build_cms_home(self):
        f = self.cms_home
        f.columnconfigure(1, weight=1)

        self.cfg_home_kicker = tk.StringVar()
        self.cfg_home_lead = tk.StringVar()
        self.cfg_cta1_label = tk.StringVar()
        self.cfg_cta1_href = tk.StringVar()
        self.cfg_cta2_label = tk.StringVar()
        self.cfg_cta2_href = tk.StringVar()
        self.cfg_cta3_label = tk.StringVar()
        self.cfg_cta3_href = tk.StringVar()

        ttk.Label(f, text="Hero", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0,8))
        ttk.Label(f, text="Kicker:", style="Muted.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.cfg_home_kicker).grid(row=1, column=1, sticky="ew")

        ttk.Label(f, text="Título (HTML permitido):", style="Muted.TLabel").grid(row=2, column=0, sticky="nw", pady=(10,0))
        self.home_title_box = tk.Text(f, height=3, wrap="word")
        self.home_title_box.grid(row=2, column=1, sticky="ew", pady=(10,0))

        ttk.Label(f, text="Lead:", style="Muted.TLabel").grid(row=3, column=0, sticky="nw", pady=(10,0))
        self.home_lead_box = tk.Text(f, height=4, wrap="word")
        self.home_lead_box.grid(row=3, column=1, sticky="ew", pady=(10,0))

        ttk.Separator(f).grid(row=4, column=0, columnspan=2, sticky="ew", pady=14)

        ttk.Label(f, text="CTAs", style="Title.TLabel").grid(row=5, column=0, sticky="w", pady=(0,8))
        ttk.Label(f, text="CTA 1 label:", style="Muted.TLabel").grid(row=6, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.cfg_cta1_label).grid(row=6, column=1, sticky="ew")
        ttk.Label(f, text="CTA 1 href:", style="Muted.TLabel").grid(row=7, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_cta1_href).grid(row=7, column=1, sticky="ew", pady=(8,0))

        ttk.Label(f, text="CTA 2 label:", style="Muted.TLabel").grid(row=8, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_cta2_label).grid(row=8, column=1, sticky="ew", pady=(8,0))
        ttk.Label(f, text="CTA 2 href:", style="Muted.TLabel").grid(row=9, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_cta2_href).grid(row=9, column=1, sticky="ew", pady=(8,0))

        ttk.Label(f, text="CTA 3 label:", style="Muted.TLabel").grid(row=10, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_cta3_label).grid(row=10, column=1, sticky="ew", pady=(8,0))
        ttk.Label(f, text="CTA 3 href:", style="Muted.TLabel").grid(row=11, column=0, sticky="w", pady=(8,0))
        ttk.Entry(f, textvariable=self.cfg_cta3_href).grid(row=11, column=1, sticky="ew", pady=(8,0))

        ttk.Separator(f).grid(row=12, column=0, columnspan=2, sticky="ew", pady=14)
        ttk.Label(f, text="Pills (una por línea):", style="Muted.TLabel").grid(row=13, column=0, sticky="nw")
        self.home_pills_box = tk.Text(f, height=4, wrap="word")
        self.home_pills_box.grid(row=13, column=1, sticky="ew")

    def _build_cms_services(self):
        f = self.cms_services
        f.columnconfigure(1, weight=1)

        self.cfg_services_title = tk.StringVar()
        self.cfg_services_sub = tk.StringVar()

        ttk.Label(f, text="Sección", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0,8))
        ttk.Label(f, text="Título:", style="Muted.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.cfg_services_title).grid(row=1, column=1, sticky="ew")

        ttk.Label(f, text="Subtítulo:", style="Muted.TLabel").grid(row=2, column=0, sticky="nw", pady=(10,0))
        self.services_sub_box = tk.Text(f, height=3, wrap="word")
        self.services_sub_box.grid(row=2, column=1, sticky="ew", pady=(10,0))

        ttk.Separator(f).grid(row=3, column=0, columnspan=2, sticky="ew", pady=14)

        ttk.Label(f, text="Cards (5)", style="Title.TLabel").grid(row=4, column=0, sticky="w", pady=(0,8))
        self.svc_vars = {}
        row = 5
        for key, label in [("express","Express"),("redes","Redes"),("marca","Marca"),("musica","Música"),("web","Web")]:
            box = ttk.LabelFrame(f, text=label, padding=10)
            box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0,10))
            box.columnconfigure(1, weight=1)

            v_badge = tk.StringVar()
            v_title = tk.StringVar()
            self.svc_vars[key] = {"badge": v_badge, "title": v_title}

            ttk.Label(box, text="Badge:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
            ttk.Entry(box, textvariable=v_badge).grid(row=0, column=1, sticky="ew")

            ttk.Label(box, text="Título:", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(8,0))
            ttk.Entry(box, textvariable=v_title).grid(row=1, column=1, sticky="ew", pady=(8,0))

            if key in ("express","redes","marca","web"):
                ttk.Label(box, text="Descripción:", style="Muted.TLabel").grid(row=2, column=0, sticky="nw", pady=(8,0))
                t_desc = tk.Text(box, height=3, wrap="word")
                t_desc.grid(row=2, column=1, sticky="ew", pady=(8,0))
                self.svc_vars[key]["desc_box"] = t_desc

            if key in ("express","redes","marca"):
                ttk.Label(box, text="Pills (comma):", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(8,0))
                v_pills = tk.StringVar()
                ttk.Entry(box, textvariable=v_pills).grid(row=3, column=1, sticky="ew", pady=(8,0))
                self.svc_vars[key]["pills"] = v_pills

            if key in ("musica",):
                ttk.Label(box, text="Contenido (HTML):", style="Muted.TLabel").grid(row=2, column=0, sticky="nw", pady=(8,0))
                t_html = tk.Text(box, height=5, wrap="word")
                t_html.grid(row=2, column=1, sticky="ew", pady=(8,0))
                self.svc_vars[key]["html_box"] = t_html
                ttk.Label(box, text="CTA label / href:", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(8,0))
                v_cl = tk.StringVar(); v_ch = tk.StringVar()
                rowcta = ttk.Frame(box)
                rowcta.grid(row=3, column=1, sticky="ew", pady=(8,0))
                rowcta.columnconfigure(1, weight=1)
                ttk.Entry(rowcta, textvariable=v_cl, width=18).grid(row=0, column=0, sticky="w")
                ttk.Entry(rowcta, textvariable=v_ch).grid(row=0, column=1, sticky="ew", padx=(8,0))
                self.svc_vars[key]["cta_label"] = v_cl
                self.svc_vars[key]["cta_href"] = v_ch

            if key in ("web",):
                ttk.Label(box, text="CTA label / href:", style="Muted.TLabel").grid(row=4, column=0, sticky="w", pady=(8,0))
                v_cl = tk.StringVar(); v_ch = tk.StringVar()
                rowcta = ttk.Frame(box)
                rowcta.grid(row=4, column=1, sticky="ew", pady=(8,0))
                rowcta.columnconfigure(1, weight=1)
                ttk.Entry(rowcta, textvariable=v_cl, width=18).grid(row=0, column=0, sticky="w")
                ttk.Entry(rowcta, textvariable=v_ch).grid(row=0, column=1, sticky="ew", padx=(8,0))
                self.svc_vars[key]["cta_label"] = v_cl
                self.svc_vars[key]["cta_href"] = v_ch

            row += 1

        ttk.Separator(f).grid(row=row, column=0, columnspan=2, sticky="ew", pady=14); row += 1
        ttk.Label(f, text="Opciones del formulario (una por línea):", style="Muted.TLabel").grid(row=row, column=0, sticky="nw")
        self.form_options_box = tk.Text(f, height=6, wrap="word")
        self.form_options_box.grid(row=row, column=1, sticky="ew")

    def _build_cms_tools(self):
        f = self.cms_tools
        f.columnconfigure(0, weight=1)
        ttk.Label(f, text="Cards de Herramientas (tabla editable)", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0,8))

        cols = ("badge","title","desc","image")
        self.tools_tree = ttk.Treeview(f, columns=cols, show="headings", height=12, selectmode="browse")
        for c in cols:
            self.tools_tree.heading(c, text=c)
        self.tools_tree.column("badge", width=90)
        self.tools_tree.column("title", width=200)
        self.tools_tree.column("desc", width=420)
        self.tools_tree.column("image", width=260)
        self.tools_tree.grid(row=1, column=0, sticky="nsew")
        f.rowconfigure(1, weight=1)

        btns = ttk.Frame(f)
        btns.grid(row=2, column=0, sticky="ew", pady=(10,0))
        ttk.Button(btns, text="Agregar", command=self.tools_add).pack(side="left")
        ttk.Button(btns, text="Editar", command=self.tools_edit).pack(side="left", padx=(8,0))
        ttk.Button(btns, text="Eliminar", command=self.tools_del).pack(side="left", padx=(8,0))

        ttk.Separator(f).grid(row=3, column=0, sticky="ew", pady=14)

        ttk.Label(f, text="Hero", style="Title.TLabel").grid(row=4, column=0, sticky="w", pady=(0,8))
        self.tools_kicker = tk.StringVar()
        self.tools_title = tk.StringVar()
        ttk.Label(f, text="Kicker:", style="Muted.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.tools_kicker).grid(row=6, column=0, sticky="ew")
        ttk.Label(f, text="Título:", style="Muted.TLabel").grid(row=7, column=0, sticky="w", pady=(10,0))
        ttk.Entry(f, textvariable=self.tools_title).grid(row=8, column=0, sticky="ew")

        ttk.Label(f, text="Lead:", style="Muted.TLabel").grid(row=9, column=0, sticky="w", pady=(10,0))
        self.tools_lead_box = tk.Text(f, height=3, wrap="word")
        self.tools_lead_box.grid(row=10, column=0, sticky="ew", pady=(0,10))

    def tools_add(self):
        item = self._tools_edit_dialog({"badge":"","title":"","desc":"","image":""}, title="Agregar herramienta")
        if item:
            self.tools_tree.insert("", "end", values=(item["badge"], item["title"], item["desc"], item["image"]))

    def tools_edit(self):
        sel = self.tools_tree.selection()
        if not sel:
            return
        vals = self.tools_tree.item(sel[0], "values")
        cur = {"badge":vals[0],"title":vals[1],"desc":vals[2],"image":vals[3]}
        item = self._tools_edit_dialog(cur, title="Editar herramienta")
        if item:
            self.tools_tree.item(sel[0], values=(item["badge"], item["title"], item["desc"], item["image"]))

    def tools_del(self):
        sel = self.tools_tree.selection()
        if not sel:
            return
        self.tools_tree.delete(sel[0])

    def _tools_edit_dialog(self, cur: Dict, title="Editar"):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.geometry("620x360")
        dlg.transient(self)
        dlg.grab_set()

        v_badge = tk.StringVar(value=cur.get("badge",""))
        v_title = tk.StringVar(value=cur.get("title",""))
        v_desc = tk.StringVar(value=cur.get("desc",""))
        v_image = tk.StringVar(value=cur.get("image",""))

        frm = ttk.Frame(dlg, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Badge:", style="Muted.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=v_badge).grid(row=0, column=1, sticky="ew")
        ttk.Label(frm, text="Title:", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(10,0))
        ttk.Entry(frm, textvariable=v_title).grid(row=1, column=1, sticky="ew", pady=(10,0))
        ttk.Label(frm, text="Desc:", style="Muted.TLabel").grid(row=2, column=0, sticky="nw", pady=(10,0))
        t_desc = tk.Text(frm, height=5, wrap="word")
        t_desc.grid(row=2, column=1, sticky="ew", pady=(10,0))
        t_desc.insert("1.0", v_desc.get())
        ttk.Label(frm, text="Image path:", style="Muted.TLabel").grid(row=3, column=0, sticky="w", pady=(10,0))
        rowi = ttk.Frame(frm)
        rowi.grid(row=3, column=1, sticky="ew", pady=(10,0))
        rowi.columnconfigure(0, weight=1)
        ttk.Entry(rowi, textvariable=v_image).grid(row=0, column=0, sticky="ew")
        def pick():
            fp = filedialog.askopenfilename(title="Selecciona imagen", filetypes=[("Imágenes","*.jpg *.jpeg *.png *.webp"),("Todos","*.*")])
            if fp:
                # If inside project, store relative-like
                if self.paths:
                    try:
                        rel = Path(fp).resolve().relative_to(self.paths["root"].resolve())
                        v_image.set(str(rel).replace("\\","/"))
                    except Exception:
                        v_image.set(fp)
        ttk.Button(rowi, text="Buscar…", command=pick).grid(row=0, column=1, padx=(8,0))

        result = {"ok": False}

        def ok():
            result["ok"] = True
            v_desc.set(t_desc.get("1.0","end").strip())
            dlg.destroy()

        ttk.Button(frm, text="Guardar", style="Accent.TButton", command=ok).grid(row=4, column=0, sticky="w", pady=(16,0))
        ttk.Button(frm, text="Cancelar", command=lambda: dlg.destroy()).grid(row=4, column=1, sticky="e", pady=(16,0))

        dlg.wait_window()
        if not result["ok"]:
            return None
        return {"badge": v_badge.get().strip(), "title": v_title.get().strip(), "desc": v_desc.get().strip(), "image": v_image.get().strip()}

    def _build_cms_policies(self):
        f = self.cms_policies
        f.columnconfigure(1, weight=1)

        self.privacy_title_var = tk.StringVar()
        self.terms_title_var = tk.StringVar()

        ttk.Label(f, text="Privacidad", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0,8))
        ttk.Label(f, text="Título:", style="Muted.TLabel").grid(row=1, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.privacy_title_var).grid(row=1, column=1, sticky="ew")
        ttk.Label(f, text="Párrafos (uno por línea):", style="Muted.TLabel").grid(row=2, column=0, sticky="nw", pady=(10,0))
        self.privacy_box = tk.Text(f, height=9, wrap="word")
        self.privacy_box.grid(row=2, column=1, sticky="ew", pady=(10,0))

        ttk.Separator(f).grid(row=3, column=0, columnspan=2, sticky="ew", pady=14)

        ttk.Label(f, text="Términos", style="Title.TLabel").grid(row=4, column=0, sticky="w", pady=(0,8))
        ttk.Label(f, text="Título:", style="Muted.TLabel").grid(row=5, column=0, sticky="w")
        ttk.Entry(f, textvariable=self.terms_title_var).grid(row=5, column=1, sticky="ew")
        ttk.Label(f, text="Párrafos (uno por línea):", style="Muted.TLabel").grid(row=6, column=0, sticky="nw", pady=(10,0))
        self.terms_box = tk.Text(f, height=9, wrap="word")
        self.terms_box.grid(row=6, column=1, sticky="ew", pady=(10,0))

    def _build_cms_raw(self):
        f = self.cms_raw
        f.columnconfigure(0, weight=1)
        f.rowconfigure(0, weight=1)
        self.raw_box = tk.Text(f, wrap="none")
        self.raw_box.grid(row=0, column=0, sticky="nsew")
        ttk.Label(f, text="Tip: si editas aquí, debe ser JSON válido.", style="Muted.TLabel").grid(row=1, column=0, sticky="w", pady=(10,0))

    def _load_content_forms(self):
        if not self.paths:
            return
        cfg = self.site_cfg if isinstance(self.site_cfg, dict) else dict(DEFAULT_SITE_CFG)

        # brand/contact
        self.cfg_brand_name.set(cfg.get("brand",{}).get("name",""))
        self.cfg_brand_tagline.set(cfg.get("brand",{}).get("tagline",""))
        self.cfg_brand_title.set(cfg.get("brand",{}).get("site_title",""))
        self.brand_desc_box.delete("1.0","end")
        self.brand_desc_box.insert("1.0", cfg.get("brand",{}).get("meta_description",""))

        self.cfg_contact_whats.set(cfg.get("contact",{}).get("whatsapp_phone",""))
        self.cfg_contact_phone.set(cfg.get("contact",{}).get("phone_display",""))
        self.cfg_contact_email.set(cfg.get("contact",{}).get("email",""))
        self.cfg_contact_hours.set(cfg.get("contact",{}).get("hours",""))
        self.cfg_contact_fb.set(cfg.get("contact",{}).get("facebook_url",""))
        self.cfg_contact_ig.set(cfg.get("contact",{}).get("instagram_url",""))
        self.cfg_contact_loc.set(cfg.get("contact",{}).get("location",""))

        # home
        self.cfg_home_kicker.set(cfg.get("home",{}).get("hero_kicker",""))
        self.home_title_box.delete("1.0","end")
        self.home_title_box.insert("1.0", cfg.get("home",{}).get("hero_title_html",""))
        self.home_lead_box.delete("1.0","end")
        self.home_lead_box.insert("1.0", cfg.get("home",{}).get("hero_lead",""))

        cta1 = cfg.get("home",{}).get("cta_primary",{})
        cta2 = cfg.get("home",{}).get("cta_secondary",{})
        cta3 = cfg.get("home",{}).get("cta_tertiary",{})
        self.cfg_cta1_label.set(cta1.get("label","")); self.cfg_cta1_href.set(cta1.get("href",""))
        self.cfg_cta2_label.set(cta2.get("label","")); self.cfg_cta2_href.set(cta2.get("href",""))
        self.cfg_cta3_label.set(cta3.get("label","")); self.cfg_cta3_href.set(cta3.get("href",""))

        pills = cfg.get("home",{}).get("pills",[])
        self.home_pills_box.delete("1.0","end")
        self.home_pills_box.insert("1.0", "\n".join([p for p in pills if str(p).strip()]))

        # services
        self.cfg_services_title.set(cfg.get("services",{}).get("section_title",""))
        self.services_sub_box.delete("1.0","end")
        self.services_sub_box.insert("1.0", cfg.get("services",{}).get("section_subtitle",""))

        cards = cfg.get("services",{}).get("cards",{})
        for k in self.svc_vars.keys():
            c = cards.get(k, {})
            self.svc_vars[k]["badge"].set(c.get("badge",""))
            self.svc_vars[k]["title"].set(c.get("title",""))
            if "desc_box" in self.svc_vars[k]:
                self.svc_vars[k]["desc_box"].delete("1.0","end")
                self.svc_vars[k]["desc_box"].insert("1.0", c.get("desc",""))
            if "pills" in self.svc_vars[k]:
                pillsv = c.get("pills", [])
                if isinstance(pillsv, list):
                    self.svc_vars[k]["pills"].set(", ".join(pillsv))
                else:
                    self.svc_vars[k]["pills"].set("")
            if "html_box" in self.svc_vars[k]:
                self.svc_vars[k]["html_box"].delete("1.0","end")
                self.svc_vars[k]["html_box"].insert("1.0", c.get("desc_html",""))
            if "cta_label" in self.svc_vars[k]:
                cta = c.get("cta", {})
                self.svc_vars[k]["cta_label"].set(cta.get("label",""))
                self.svc_vars[k]["cta_href"].set(cta.get("href",""))

        opts = cfg.get("contact_form",{}).get("service_options",[])
        self.form_options_box.delete("1.0","end")
        self.form_options_box.insert("1.0", "\n".join([o for o in opts if str(o).strip()]))

        # tools
        self.tools_tree.delete(*self.tools_tree.get_children())
        tp = cfg.get("tools_page", {})
        self.tools_kicker.set(tp.get("hero_kicker",""))
        self.tools_title.set(tp.get("hero_title",""))
        self.tools_lead_box.delete("1.0","end")
        self.tools_lead_box.insert("1.0", tp.get("hero_lead",""))
        for it in tp.get("cards", []) if isinstance(tp.get("cards", []), list) else []:
            if isinstance(it, dict):
                self.tools_tree.insert("", "end", values=(it.get("badge",""), it.get("title",""), it.get("desc",""), it.get("image","")))

        # policies
        pol = cfg.get("policies", {})
        self.privacy_title_var.set(pol.get("privacy_title",""))
        self.terms_title_var.set(pol.get("terms_title",""))
        self.privacy_box.delete("1.0","end")
        self.privacy_box.insert("1.0", "\n".join(pol.get("privacy_paragraphs", []) if isinstance(pol.get("privacy_paragraphs", []), list) else []))
        self.terms_box.delete("1.0","end")
        self.terms_box.insert("1.0", "\n".join(pol.get("terms_paragraphs", []) if isinstance(pol.get("terms_paragraphs", []), list) else []))

        # raw json
        self.raw_box.delete("1.0","end")
        self.raw_box.insert("1.0", json.dumps(cfg, indent=2, ensure_ascii=False))

    def save_site_config(self):
        if not self.paths:
            return
        cfg = dict(self.site_cfg) if isinstance(self.site_cfg, dict) else dict(DEFAULT_SITE_CFG)

        # If raw JSON tab edited, prefer it if valid and user is on that tab
        try:
            raw = self.raw_box.get("1.0","end").strip()
            if raw:
                cfg_try = json.loads(raw)
                if isinstance(cfg_try, dict):
                    cfg = cfg_try
        except Exception:
            # ignore; we'll save from forms
            pass

        # override from forms (these are safer)
        cfg.setdefault("brand", {})
        cfg["brand"]["name"] = self.cfg_brand_name.get().strip()
        cfg["brand"]["tagline"] = self.cfg_brand_tagline.get().strip()
        cfg["brand"]["site_title"] = self.cfg_brand_title.get().strip()
        cfg["brand"]["meta_description"] = self.brand_desc_box.get("1.0","end").strip()

        cfg.setdefault("contact", {})
        cfg["contact"]["whatsapp_phone"] = self.cfg_contact_whats.get().strip()
        cfg["contact"]["phone_display"] = self.cfg_contact_phone.get().strip()
        cfg["contact"]["email"] = self.cfg_contact_email.get().strip()
        cfg["contact"]["hours"] = self.cfg_contact_hours.get().strip()
        cfg["contact"]["facebook_url"] = self.cfg_contact_fb.get().strip()
        cfg["contact"]["instagram_url"] = self.cfg_contact_ig.get().strip()
        cfg["contact"]["location"] = self.cfg_contact_loc.get().strip()

        cfg.setdefault("home", {})
        cfg["home"]["hero_kicker"] = self.cfg_home_kicker.get().strip()
        cfg["home"]["hero_title_html"] = self.home_title_box.get("1.0","end").strip()
        cfg["home"]["hero_lead"] = self.home_lead_box.get("1.0","end").strip()
        cfg["home"]["cta_primary"] = {"label": self.cfg_cta1_label.get().strip(), "href": self.cfg_cta1_href.get().strip(), "kind":"whatsapp"}
        cfg["home"]["cta_secondary"] = {"label": self.cfg_cta2_label.get().strip(), "href": self.cfg_cta2_href.get().strip()}
        cfg["home"]["cta_tertiary"] = {"label": self.cfg_cta3_label.get().strip(), "href": self.cfg_cta3_href.get().strip()}
        pills = [ln.strip() for ln in self.home_pills_box.get("1.0","end").splitlines() if ln.strip()]
        cfg["home"]["pills"] = pills

        cfg.setdefault("services", {})
        cfg["services"]["section_title"] = self.cfg_services_title.get().strip()
        cfg["services"]["section_subtitle"] = self.services_sub_box.get("1.0","end").strip()
        cfg.setdefault("services", {}).setdefault("cards", {})
        for k, d in self.svc_vars.items():
            cfg["services"]["cards"].setdefault(k, {})
            cfg["services"]["cards"][k]["badge"] = d["badge"].get().strip()
            cfg["services"]["cards"][k]["title"] = d["title"].get().strip()
            if "desc_box" in d:
                cfg["services"]["cards"][k]["desc"] = d["desc_box"].get("1.0","end").strip()
            if "pills" in d:
                pills_str = d["pills"].get().strip()
                cfg["services"]["cards"][k]["pills"] = [p.strip() for p in pills_str.split(",") if p.strip()]
            if "html_box" in d:
                cfg["services"]["cards"][k]["desc_html"] = d["html_box"].get("1.0","end").strip()
            if "cta_label" in d:
                cfg["services"]["cards"][k]["cta"] = {"label": d["cta_label"].get().strip(), "href": d["cta_href"].get().strip()}

        cfg.setdefault("contact_form", {})
        cfg["contact_form"]["service_options"] = [ln.strip() for ln in self.form_options_box.get("1.0","end").splitlines() if ln.strip()]

        cfg.setdefault("tools_page", {})
        cfg["tools_page"]["hero_kicker"] = self.tools_kicker.get().strip()
        cfg["tools_page"]["hero_title"] = self.tools_title.get().strip()
        cfg["tools_page"]["hero_lead"] = self.tools_lead_box.get("1.0","end").strip()
        cards = []
        for iid in self.tools_tree.get_children():
            vals = self.tools_tree.item(iid, "values")
            cards.append({"badge": vals[0], "title": vals[1], "desc": vals[2], "image": vals[3]})
        cfg["tools_page"]["cards"] = cards

        cfg.setdefault("policies", {})
        cfg["policies"]["privacy_title"] = self.privacy_title_var.get().strip()
        cfg["policies"]["terms_title"] = self.terms_title_var.get().strip()
        cfg["policies"]["privacy_paragraphs"] = [ln.strip() for ln in self.privacy_box.get("1.0","end").splitlines() if ln.strip()]
        cfg["policies"]["terms_paragraphs"] = [ln.strip() for ln in self.terms_box.get("1.0","end").splitlines() if ln.strip()]

        # backup and save
        backup_file(self.paths["site_cfg"], self.paths["backups"])
        save_json(self.paths["site_cfg"], cfg)
        self.site_cfg = cfg
        self.raw_box.delete("1.0","end")
        self.raw_box.insert("1.0", json.dumps(cfg, indent=2, ensure_ascii=False))
        self.log_line("✅ site.config.json guardado.")
        messagebox.showinfo("Listo", "site.config.json actualizado. Recarga tu web (con servidor) para verlo.")

    # ---------- Assets Tab ----------
    def _build_assets_tab(self):
        frm = ttk.Frame(self.tab_assets, padding=14)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Assets Manager", style="Title.TLabel").grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(frm, text="Reemplaza logo/favicons/heroes con resize automático.", style="Muted.TLabel").grid(row=1, column=0, columnspan=3, sticky="w", pady=(6,18))

        self.asset_preview = ttk.Label(frm)
        self.asset_preview.grid(row=2, column=0, rowspan=6, sticky="n", padx=(0, 14))

        ttk.Label(frm, text="Logo (assets/logo.png):", style="Muted.TLabel").grid(row=2, column=1, sticky="w")
        ttk.Button(frm, text="Reemplazar logo…", style="Accent.TButton", command=lambda: self.replace_image("logo")).grid(row=2, column=2, sticky="e")

        ttk.Label(frm, text="Favicon (favicon.png + favicon.ico):", style="Muted.TLabel").grid(row=3, column=1, sticky="w", pady=(10,0))
        ttk.Button(frm, text="Reemplazar favicon…", style="Accent.TButton", command=lambda: self.replace_image("favicon")).grid(row=3, column=2, sticky="e", pady=(10,0))

        ttk.Label(frm, text="Hero (assets/hero-portfolio.jpg):", style="Muted.TLabel").grid(row=4, column=1, sticky="w", pady=(10,0))
        ttk.Button(frm, text="Reemplazar hero portfolio…", command=lambda: self.replace_image("hero-portfolio")).grid(row=4, column=2, sticky="e", pady=(10,0))

        ttk.Label(frm, text="Hero (assets/hero-web.jpg):", style="Muted.TLabel").grid(row=5, column=1, sticky="w", pady=(10,0))
        ttk.Button(frm, text="Reemplazar hero web…", command=lambda: self.replace_image("hero-web")).grid(row=5, column=2, sticky="e", pady=(10,0))

        ttk.Label(frm, text="Hero (assets/hero-redes.jpg):", style="Muted.TLabel").grid(row=6, column=1, sticky="w", pady=(10,0))
        ttk.Button(frm, text="Reemplazar hero redes…", command=lambda: self.replace_image("hero-redes")).grid(row=6, column=2, sticky="e", pady=(10,0))

        ttk.Button(frm, text="Refrescar preview", command=self._refresh_assets_preview).grid(row=7, column=1, sticky="w", pady=(18,0))

        note = ttk.LabelFrame(frm, text="Notas", padding=10)
        note.grid(row=8, column=0, columnspan=3, sticky="ew", pady=(18,0))
        ttk.Label(note, text="• Logo: se exporta PNG (máx 512px).", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(note, text="• Favicon: crea favicon.png (512x512) y favicon.ico (16/32/48).", style="Muted.TLabel").pack(anchor="w")
        ttk.Label(note, text="• Heroes: se exportan JPG optimizados (máx 2000px).", style="Muted.TLabel").pack(anchor="w")

    def _refresh_assets_preview(self):
        if not self.paths:
            return
        logo = self.paths["assets"] / "logo.png"
        if logo.exists():
            try:
                img = Image.open(logo)
                img = ImageOps.exif_transpose(img)
                img.thumbnail((260, 260), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(img)
                self.asset_preview.config(image=tk_img)
                self.asset_preview.image = tk_img
            except Exception:
                self.asset_preview.config(image="")
        else:
            self.asset_preview.config(image="")

    def replace_image(self, kind: str):
        if not self.paths:
            return
        fp = filedialog.askopenfilename(title="Selecciona imagen", filetypes=[("Imágenes","*.png *.jpg *.jpeg *.webp"),("Todos","*.*")])
        if not fp:
            return
        src = Path(fp)

        try:
            img = Image.open(src)
            img = ImageOps.exif_transpose(img)
        except Exception as e:
            messagebox.showerror("Imagen", f"No pude abrir la imagen: {e}")
            return

        # backups
        bdir = self.paths["backups"]

        if kind == "logo":
            dest = self.paths["assets"] / "logo.png"
            backup_file(dest, bdir)
            # fit within 512 preserving alpha if png
            out = img.convert("RGBA") if img.mode in ("RGBA","LA","P") else img.convert("RGBA")
            out.thumbnail((512,512), Image.Resampling.LANCZOS)
            out.save(dest, "PNG", optimize=True)
            self.log_line("✅ Logo actualizado: assets/logo.png")
        elif kind == "favicon":
            # output at root
            dest_png = self.paths["root"] / "favicon.png"
            dest_ico = self.paths["root"] / "favicon.ico"
            backup_file(dest_png, bdir); backup_file(dest_ico, bdir)

            # square crop center then resize
            out = img.convert("RGBA")
            w,h = out.size
            s = min(w,h)
            left = (w - s)//2
            top = (h - s)//2
            out = out.crop((left, top, left+s, top+s))
            out512 = out.resize((512,512), Image.Resampling.LANCZOS)
            out512.save(dest_png, "PNG", optimize=True)

            # ICO sizes
            ico_sizes = [(16,16),(32,32),(48,48)]
            out_ico = out.copy()
            out_ico.save(dest_ico, format="ICO", sizes=ico_sizes)
            self.log_line("✅ Favicon actualizado: favicon.png + favicon.ico")
        else:
            # heroes -> jpg
            name = {
                "hero-portfolio":"hero-portfolio.jpg",
                "hero-web":"hero-web.jpg",
                "hero-redes":"hero-redes.jpg"
            }[kind]
            dest = self.paths["assets"] / name
            backup_file(dest, bdir)
            out = img.convert("RGB")
            out.thumbnail((2000,2000), Image.Resampling.LANCZOS)
            out.save(dest, "JPEG", quality=88, optimize=True, progressive=True)
            self.log_line(f"✅ Hero actualizado: assets/{name}")

        self._refresh_assets_preview()
        messagebox.showinfo("Listo", "Asset actualizado. Recarga tu web para verlo.")

    # ---------- Diagnóstico ----------
    def _build_diag_tab(self):
        frm = ttk.Frame(self.tab_diag, padding=14)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(1, weight=1)

        ttk.Label(frm, text="Diagnóstico", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(frm, text="Revisa archivos faltantes y configuración.", style="Muted.TLabel").grid(row=0, column=0, sticky="e")

        self.diag_out = tk.Text(frm, wrap="word")
        self.diag_out.grid(row=1, column=0, sticky="nsew", pady=(12,0))

        btns = ttk.Frame(frm)
        btns.grid(row=2, column=0, sticky="ew", pady=(12,0))
        ttk.Button(btns, text="Ejecutar diagnóstico", style="Accent.TButton", command=self.run_diagnostics).pack(side="left")
        ttk.Button(btns, text="Copiar reporte", command=self.copy_diag).pack(side="left", padx=(8,0))

    def run_diagnostics(self):
        self.diag_out.delete("1.0","end")
        if not self.paths:
            self.diag_out.insert("end", "Carga un proyecto primero.\n")
            return

        root = self.paths["root"]
        assets = self.paths["assets"]
        port = self.paths["portfolio"]
        report = []

        # site config
        cfg_ok = False
        try:
            cfg = load_json(self.paths["site_cfg"], None)
            cfg_ok = isinstance(cfg, dict)
        except Exception:
            cfg_ok = False
        report.append(f"site.config.json: {'OK' if cfg_ok else 'ERROR'} ({self.paths['site_cfg']})")

        # manifest files
        man = load_manifest(self.paths["manifest"])
        missing = []
        for it in man.get("items", []):
            f = it.get("file","")
            if f and not (port / f).exists():
                missing.append(f)
        report.append(f"portfolio.manifest.json: {len(man.get('items',[]))} items, missing files: {len(missing)}")
        if missing:
            report.append("  - Missing examples (first 10): " + ", ".join(missing[:10]))

        # recents
        rec_missing = [f"reciente-{i}.jpg" for i in range(1,4) if not (port / f"reciente-{i}.jpg").exists()]
        report.append(f"Recientes: {'OK' if not rec_missing else 'FALTAN ' + ', '.join(rec_missing)}")

        # ticker config
        tcfg = load_ticker_cfg(self.paths["ticker_cfg"])
        report.append(f"ticker.config.json: mode={tcfg.get('mode')} speed={tcfg.get('speed_seconds')} custom_url={'YES' if tcfg.get('custom_rss_url') else 'NO'}")

        # ticker.js patched?
        tjs_ok = self.paths["ticker_js"].exists() and ("EV_TICKER_CONFIG_URL" in self.paths["ticker_js"].read_text(encoding='utf-8', errors='ignore'))
        report.append(f"ticker.js config support: {'OK' if tjs_ok else 'NO (se puede parchear desde Ticker tab)'}")

        # assets existence
        essentials = [
            root / "favicon.png",
            root / "favicon.ico",
            assets / "logo.png",
            assets / "site-content.js",
            assets / "site.config.json"
        ]
        miss_assets = [str(p.relative_to(root)) for p in essentials if not p.exists()]
        report.append(f"Assets esenciales faltantes: {len(miss_assets)}")
        for m in miss_assets[:20]:
            report.append("  - " + m)

        # html includes site-content.js?
        htmls = [p for p in root.glob("*.html") if p.name != "vr.html"]
        not_included = []
        for p in htmls:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            if "assets/site-content.js" not in txt:
                not_included.append(p.name)
        report.append(f"HTML con site-content.js: {'OK' if not not_included else 'FALTAN ' + ', '.join(not_included)}")

        self.diag_out.insert("end", "\n".join(report) + "\n")

    def copy_diag(self):
        txt = self.diag_out.get("1.0","end").strip()
        self.clipboard_clear()
        self.clipboard_append(txt)
        self.update()
        messagebox.showinfo("Copiado", "Reporte copiado al portapapeles.")


if __name__ == "__main__":
    SiteManager().mainloop()
