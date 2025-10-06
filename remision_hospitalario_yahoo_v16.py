"""Interfaz de remisión hospitalaria con automatización para Yahoo Mail."""

from __future__ import annotations

import importlib
import os
import platform
import subprocess
import time
import tkinter as tk
import webbrowser
from copy import deepcopy
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import quote

from tkinter import messagebox, ttk

from configuracion import DEFAULT_CONFIG, ConfiguracionError, cargar_configuracion

TIPOS_DOCUMENTO = [
    "Cédula de ciudadanía",
    "Tarjeta de identidad",
    "Registro civil",
    "Pasaporte",
    "NIT",
    "Otro",
]

CONFIG_PATH = Path(__file__).with_name("configuracion.json")
try:
    CONFIG = cargar_configuracion(CONFIG_PATH)
    CONFIG_ERROR_MESSAGE = None
except ConfiguracionError as exc:  # pragma: no cover - solo ocurre con archivo corrupto
    CONFIG = deepcopy(DEFAULT_CONFIG)
    CONFIG_ERROR_MESSAGE = str(exc)


def generar_asunto(nombre_paciente: str) -> str:
    return f"Solicitud de aceptación de remisión – Paciente {nombre_paciente}"


def generar_cuerpo_mensaje(campos: Dict[str, str]) -> str:
    return (
        "Respetados señores del servicio de Referencia y Contrarreferencia,\n\n"
        "Reciban un cordial saludo.\n\n"
        f"Por medio del presente correo, desde el Hospital {campos['Nombre del hospital']}, "
        f"solicitamos amablemente la aceptación de remisión del paciente {campos['Nombre completo del paciente']}, "
        f"identificado con {campos['Tipo de documento del paciente']} {campos['Número de documento']}, de "
        f"{campos['Edad']} años, quien requiere valoración y manejo por el servicio de {campos['Especialidad']}.\n\n"
        "El paciente se encuentra actualmente bajo observación en el área de urgencias de nuestro hospital y, debido a las "
        "condiciones clínicas que presenta, amerita manejo en una institución de segundo nivel de atención, de acuerdo con los "
        "protocolos vigentes.\n\n"
        "Adjuntamos los documentos clínicos pertinentes para su revisión y el soporte de remisión correspondiente.\n\n"
        "Quedamos atentos a su pronta respuesta.\n\n"
        "Atentamente,\n"
        f"{campos['Nombre del remitente']}\n"
        f"Cargo: {campos['Cargo del remitente']}\n"
        "Área de Urgencias – Referencia y Contrarreferencia\n"
        f"Hospital {campos['Nombre del hospital']}\n"
        f"Tel: {campos['Número de contacto']}\n"
        f"Correo: {campos['Correo institucional del remitente']}"
    )


def copiar_al_portapapeles(root: tk.Tk, texto: str) -> None:
    root.clipboard_clear()
    root.clipboard_append(texto)
    root.update()


def abrir_yahoo_compose(destinatarios: Iterable[str], asunto: str) -> bool:
    url = f"https://compose.mail.yahoo.com/?to={quote(','.join(destinatarios))}&subject={quote(asunto)}"

    if platform.system() == "Windows":
        chrome_paths = [
            r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
            r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
        ]
        for path in chrome_paths:
            if os.path.isfile(path):
                try:
                    subprocess.Popen([path, "--new-tab", url], close_fds=True)
                    return True
                except OSError:
                    continue
        try:
            os.startfile(url)  # type: ignore[attr-defined]
            return True
        except OSError:
            pass
    else:
        comando = ["open", url] if platform.system() == "Darwin" else ["xdg-open", url]
        try:
            subprocess.Popen(comando, close_fds=True)
            return True
        except OSError:
            pass

    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception:
        return False


def cargar_pyautogui():
    spec = importlib.util.find_spec("pyautogui")
    if spec is None:
        return None, "La dependencia opcional 'pyautogui' no está instalada."
    try:
        modulo = importlib.import_module("pyautogui")
    except Exception as exc:  # pragma: no cover - protección ante import fallido
        return None, f"No se pudo inicializar pyautogui: {exc}"
    return modulo, None


def esperar_editor_compose(pyautogui_mod, timeout: float) -> bool:
    obtener_ventana = getattr(pyautogui_mod, "getActiveWindow", None)
    if not callable(obtener_ventana):
        time.sleep(timeout)
        return True

    fin = time.time() + timeout
    while time.time() < fin:
        try:
            ventana = obtener_ventana()
        except Exception:  # pragma: no cover - dependiente del entorno
            ventana = None
        titulo = getattr(ventana, "title", "") or ""
        if "yahoo" in titulo.lower():
            return True
        time.sleep(0.5)
    return False


def abrir_carpeta_documentos(ruta_carpeta: str) -> bool:
    carpeta = Path(ruta_carpeta).expanduser()
    if not carpeta.exists():
        return False
    try:
        if platform.system() == "Windows":
            os.startfile(carpeta)  # type: ignore[attr-defined]
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", str(carpeta)], close_fds=True)
        else:
            subprocess.Popen(["xdg-open", str(carpeta)], close_fds=True)
    except OSError:
        return False
    return True


def validar_campos(campos: Dict[str, str], dests: List[str]) -> List[str]:
    errores: List[str] = []

    if not campos["Nombre completo del paciente"]:
        errores.append("Ingrese el nombre completo del paciente.")

    if not campos["Número de documento"]:
        errores.append("Ingrese el número de documento del paciente.")

    if not campos["Especialidad"]:
        errores.append("Indique el servicio o especialidad requerida.")

    if not campos["Nombre del remitente"]:
        errores.append("Ingrese el nombre del remitente.")

    if not campos["Cargo del remitente"]:
        errores.append("Ingrese el cargo del remitente.")

    try:
        edad = int(campos["Edad"])
        if edad <= 0:
            raise ValueError
    except ValueError:
        errores.append("La edad debe ser un número entero positivo.")
    else:
        campos["Edad"] = str(edad)

    if not dests:
        errores.append("Seleccione al menos un destinatario.")

    return errores


def yahoo_pegar_mensaje(root: tk.Tk, campos: Dict[str, str], dests: List[str], asunto: str) -> None:
    if not abrir_yahoo_compose(dests, asunto):
        messagebox.showerror("Navegador", "No se pudo abrir Yahoo Mail en el navegador predeterminado.")
        return

    pyautogui_mod, error_pyautogui = cargar_pyautogui()
    if pyautogui_mod is None:
        messagebox.showwarning(
            "Automatización no disponible",
            f"{error_pyautogui}\nEl mensaje se copiará al portapapeles para que pueda pegarlo manualmente.",
        )
        try:
            copiar_al_portapapeles(root, generar_cuerpo_mensaje(campos))
        except tk.TclError as exc:
            messagebox.showerror("Portapapeles", f"No se pudo copiar el mensaje: {exc}")
        return

    if not esperar_editor_compose(pyautogui_mod, CONFIG["compose_wait_seconds"]):
        messagebox.showwarning(
            "Editor no disponible",
            "No fue posible detectar la ventana de Yahoo Mail a tiempo.\n"
            "El mensaje se copiará al portapapeles para que pueda pegarlo manualmente.",
        )
        try:
            copiar_al_portapapeles(root, generar_cuerpo_mensaje(campos))
        except tk.TclError as exc:
            messagebox.showerror("Portapapeles", f"No se pudo copiar el mensaje: {exc}")
        return

    mensaje = generar_cuerpo_mensaje(campos)
    try:
        copiar_al_portapapeles(root, mensaje)
    except tk.TclError as exc:
        messagebox.showerror("Portapapeles", f"No se pudo copiar el mensaje: {exc}")
        return

    try:
        pyautogui_mod.hotkey("ctrl", "v")
    except Exception as exc:  # pragma: no cover - dependiente del entorno gráfico
        messagebox.showwarning(
            "Automatización interrumpida",
            f"No se pudo pegar automáticamente el mensaje ({exc}).\nPégalo manualmente en la ventana abierta.",
        )
        return

    messagebox.showinfo(
        "✅ Correo generado",
        "Correo preparado en Yahoo. Revise la redacción, adjunte los documentos clínicos y envíe el mensaje.",
    )

    if not abrir_carpeta_documentos(CONFIG["documents_folder"]):
        messagebox.showwarning(
            "Carpeta no disponible",
            "No se pudo abrir la carpeta de documentos configurada. Verifique la ruta en configuracion.json.",
        )


def crear_icono_cruz_azul(size: int = 28) -> tk.PhotoImage:
    img = tk.PhotoImage(width=size, height=size)
    blanco, azul = "#FFFFFF", "#1976D2"
    img.put(blanco, to=(0, 0, size, size))
    grosor = size // 3
    centro = size // 2
    img.put(azul, to=(centro - grosor // 2, 3, centro + grosor // 2, size - 3))
    img.put(azul, to=(3, centro - grosor // 2, size - 3, centro + grosor // 2))
    return img


def crear_interfaz() -> None:
    root = tk.Tk()
    root.title("Sistema de Remisión – Área de Urgencias Hospitalarias")
    app_width, app_height = 1200, 800
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    pos_x, pos_y = (screen_w - app_width) // 2, (screen_h - app_height) // 2
    root.geometry(f"{app_width}x{app_height}+{pos_x}+{pos_y}")
    root.configure(bg="#FFFFFF")

    if CONFIG_ERROR_MESSAGE:
        root.after(
            200,
            lambda: messagebox.showwarning(
                "Configuración",
                "Se produjo un problema al leer configuracion.json.\n"
                "Se usarán los valores predeterminados disponibles.\n\n"
                f"Detalle: {CONFIG_ERROR_MESSAGE}",
            ),
        )

    estilo = ttk.Style()
    estilo.configure("Header.TLabel", font=("Segoe UI Semibold", 20), foreground="#0D47A1", background="#FFFFFF")
    estilo.configure("TLabel", background="#FFFFFF", font=("Segoe UI", 11))
    estilo.configure("TButton", font=("Segoe UI", 10, "bold"), padding=10)
    estilo.configure("Fixed.TEntry", fieldbackground="#F5F5F5", foreground="#444444")

    header = tk.Frame(root, bg="#FFFFFF")
    header.pack(fill="x", pady=(30, 10))
    icon_img = crear_icono_cruz_azul(32)
    tk.Label(header, image=icon_img, bg="#FFFFFF").pack(side="left", padx=(260, 10))
    ttk.Label(header, text="Sistema de Remisión – Área de Urgencias Hospitalarias", style="Header.TLabel").pack(
        side="left"
    )
    header.icon_img = icon_img

    canvas_linea = tk.Canvas(root, bg="#FFFFFF", height=2, highlightthickness=0)
    canvas_linea.pack(fill="x", padx=260, pady=(0, 30))
    canvas_linea.create_line(0, 1, 680, 1, fill="#1976D2", width=3)

    card = tk.Frame(root, bg="#FFFFFF", highlightbackground="#E0E0E0", highlightthickness=1)
    card.place(relx=0.5, rely=0.52, anchor="center")
    card.configure(bd=0)
    card.grid_columnconfigure(1, weight=1)

    campos_dinamicos = [
        ("Nombre completo del paciente", "entry"),
        ("Tipo de documento del paciente", "combo"),
        ("Número de documento", "entry"),
        ("Edad", "entry"),
        ("Especialidad", "entry"),
        ("Nombre del remitente", "entry"),
        ("Cargo del remitente", "entry"),
    ]

    entradas: Dict[str, tk.Widget] = {}

    for fila, (campo, tipo) in enumerate(campos_dinamicos):
        ttk.Label(card, text=f"{campo}:").grid(row=fila, column=0, sticky="e", padx=10, pady=6)
        if tipo == "combo":
            cb = ttk.Combobox(card, values=TIPOS_DOCUMENTO, state="readonly")
            cb.set(TIPOS_DOCUMENTO[0])
            cb.grid(row=fila, column=1, padx=10, pady=6, ipadx=100)
            entradas[campo] = cb
        else:
            entry = ttk.Entry(card, width=50)
            entry.grid(row=fila, column=1, padx=10, pady=6, ipadx=100)
            entradas[campo] = entry

    ttk.Label(card, text="Nombre del hospital:").grid(row=7, column=0, sticky="e", padx=10, pady=6)
    e_hosp = ttk.Entry(card, width=50, style="Fixed.TEntry")
    e_hosp.insert(0, CONFIG["hospital"])
    e_hosp.state(["readonly"])
    e_hosp.grid(row=7, column=1, padx=10, pady=6, ipadx=100)

    ttk.Label(card, text="Número de contacto (Tel):").grid(row=8, column=0, sticky="e", padx=10, pady=6)
    e_tel = ttk.Entry(card, width=50, style="Fixed.TEntry")
    e_tel.insert(0, CONFIG["contact_number"])
    e_tel.state(["readonly"])
    e_tel.grid(row=8, column=1, padx=10, pady=6, ipadx=100)

    ttk.Label(card, text="Correo institucional del remitente:").grid(row=9, column=0, sticky="e", padx=10, pady=6)
    e_cor = ttk.Entry(card, width=50, style="Fixed.TEntry")
    e_cor.insert(0, CONFIG["institutional_email"])
    e_cor.state(["readonly"])
    e_cor.grid(row=9, column=1, padx=10, pady=6, ipadx=100)

    ttk.Label(card, text="Destinatarios (selección múltiple):").grid(row=10, column=0, sticky="ne", padx=10, pady=6)
    frame_chk = tk.Frame(card, bg="#FFFFFF")
    frame_chk.grid(row=10, column=1, sticky="w")
    vars_dest: Dict[str, tk.BooleanVar] = {}
    for correo in CONFIG["recipients"]:
        correo_e = correo["email"]
        var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_chk, text=f"{correo['label']} ({correo_e})", variable=var).pack(anchor="w")
        vars_dest[correo_e] = var

    def _campos() -> Dict[str, str]:
        return {
            "Nombre completo del paciente": entradas["Nombre completo del paciente"].get().strip(),
            "Tipo de documento del paciente": entradas["Tipo de documento del paciente"].get().strip(),
            "Número de documento": entradas["Número de documento"].get().strip(),
            "Edad": entradas["Edad"].get().strip(),
            "Especialidad": entradas["Especialidad"].get().strip(),
            "Nombre del remitente": entradas["Nombre del remitente"].get().strip(),
            "Cargo del remitente": entradas["Cargo del remitente"].get().strip(),
            "Nombre del hospital": CONFIG["hospital"],
            "Número de contacto": CONFIG["contact_number"],
            "Correo institucional del remitente": CONFIG["institutional_email"],
        }

    def _destinatarios() -> List[str]:
        return [correo for correo, var in vars_dest.items() if var.get()]

    barra = tk.Frame(root, bg="#FFFFFF")
    barra.pack(pady=30)

    def efecto_boton(btn: tk.Button, color_base: str, color_hover: str) -> None:
        btn.bind("<Enter>", lambda e: btn.config(background=color_hover))
        btn.bind("<Leave>", lambda e: btn.config(background=color_base))
        btn.bind("<ButtonPress-1>", lambda e: btn.config(background="#42A5F5"))
        btn.bind("<ButtonRelease-1>", lambda e: btn.config(background=color_hover))

    def abrir_en_yahoo_web() -> None:
        campos = _campos()
        dests = _destinatarios()
        errores = validar_campos(campos, dests)
        if errores:
            mensaje = "\n".join(f"• {error}" for error in errores)
            messagebox.showwarning("Campos incompletos", mensaje)
            return
        asunto = generar_asunto(campos["Nombre completo del paciente"])
        yahoo_pegar_mensaje(root, campos, dests, asunto)

    btn_env = tk.Button(
        barra,
        text="📩 Enviar Solicitud",
        bg="#1976D2",
        fg="white",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=20,
        pady=10,
        borderwidth=0,
        cursor="hand2",
        command=abrir_en_yahoo_web,
    )
    efecto_boton(btn_env, "#1976D2", "#0D47A1")
    btn_env.pack(side="left", padx=10)

    btn_salir = tk.Button(
        barra,
        text="Salir",
        bg="#E0E0E0",
        fg="#333333",
        font=("Segoe UI", 11, "bold"),
        relief="flat",
        padx=20,
        pady=10,
        borderwidth=0,
        cursor="hand2",
        command=root.destroy,
    )
    efecto_boton(btn_salir, "#E0E0E0", "#BDBDBD")
    btn_salir.pack(side="left", padx=10)

    root.mainloop()


if __name__ == "__main__":
    crear_interfaz()
