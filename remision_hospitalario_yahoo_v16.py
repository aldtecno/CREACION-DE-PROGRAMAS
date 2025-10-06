# remision_hospitalario_yahoo_v16.py
# -*- coding: utf-8 -*-
"""
Sistema de Remisión – Área de Urgencias Hospitalarias (v16)
-----------------------------------------------------------
Versión con diseño hospitalario moderno y profesional.
- Ventana centrada 1200x800
- Fondo blanco limpio
- Encabezado estilizado con línea azul
- Campos alineados y tarjeta con bordes redondeados
- Botones modernos con efectos hover y animación
- Funcionalidad igual a v15 (Yahoo automático)
"""

import os, time, subprocess, webbrowser, json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from urllib.parse import quote

CORREO_INSTITUCIONAL_FIJO = "urgenciasaladoblanco@yahoo.com"
NUMERO_CONTACTO_FIJO = "3138899808"
HOSPITAL_FIJO = "Nuestra Señora de las Mercedes"

DESTINATARIOS_OPCIONES = [
    ("referenciaycontrarreferencia2@hospitalpitalito.gov.co", "Hospital Pitalito"),
    ("referenciaycontrarreferencia@clinicareinaisabel.com", "Referencia Ycontrareferencia"),
]

TIPOS_DOCUMENTO = [
    "Cédula de ciudadanía", "Tarjeta de identidad",
    "Registro civil", "Pasaporte", "NIT", "Otro"
]

def generar_asunto(nombre_paciente: str) -> str:
    return f"Solicitud de aceptación de remisión – Paciente {nombre_paciente}"

def abrir_yahoo_compose(dests: list[str], asunto: str) -> bool:
    url = f"https://compose.mail.yahoo.com/?to={quote(','.join(dests))}&subject={quote(asunto)}"
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in chrome_paths:
        if os.path.isfile(path):
            try:
                subprocess.Popen([path, "--new-tab", url], close_fds=True)
                return True
            except Exception:
                pass
    try:
        webbrowser.open_new_tab(url)
        return True
    except Exception:
        return False

def copiar(texto: str):
    r = tk.Tk(); r.withdraw()
    r.clipboard_clear(); r.clipboard_append(texto); r.update(); r.destroy()

def yahoo_pegar_mensaje(campos: dict, dests: list[str], asunto: str):
    ok = abrir_yahoo_compose(dests, asunto)
    if not ok:
        messagebox.showerror("Navegador", "No se pudo abrir Yahoo Mail.")
        return
    import pyautogui
    time.sleep(8.5)
    w, h = pyautogui.size()
    pyautogui.click(w // 2, int(h * 0.6))

    mensaje = f"""\
Respetados señores del servicio de Referencia y Contrarreferencia,

Reciban un cordial saludo.

Por medio del presente correo, desde el Hospital {campos['Nombre del hospital']}, solicitamos amablemente la aceptación de remisión del paciente {campos['Nombre completo del paciente']}, identificado con {campos['Tipo de documento del paciente']} {campos['Número de documento']}, de {campos['Edad']} años, quien requiere valoración y manejo por el servicio de {campos['Especialidad']}.

El paciente se encuentra actualmente bajo observación en el área de urgencias de nuestro hospital y, debido a las condiciones clínicas que presenta, amerita manejo en una institución de segundo nivel de atención, de acuerdo con los protocolos vigentes.

Adjuntamos los documentos clínicos pertinentes para su revisión y el soporte de remisión correspondiente.

Quedamos atentos a su pronta respuesta.

Atentamente,
{campos['Nombre del remitente']}
Cargo: {campos['Cargo del remitente']}
Área de Urgencias – Referencia y Contrarreferencia
Hospital {campos['Nombre del hospital']}
Tel: {campos['Número de contacto']}
Correo: {campos['Correo institucional del remitente']}
"""
    copiar(mensaje)
    pyautogui.hotkey("ctrl", "v")
    messagebox.showinfo("✅ Correo generado", "Correo generado correctamente en Yahoo.\nAdjunte los documentos clínicos y envíe el mensaje.")
    carpeta = os.path.join(os.path.expanduser("~"), "Documents")
    if os.path.isdir(carpeta):
        os.startfile(carpeta)

def crear_icono_cruz_azul(size=28):
    img = tk.PhotoImage(width=size, height=size)
    blanco, azul = "#FFFFFF", "#1976D2"
    img.put(blanco, to=(0, 0, size, size))
    grosor = size // 3
    centro = size // 2
    img.put(azul, to=(centro - grosor // 2, 3, centro + grosor // 2, size - 3))
    img.put(azul, to=(3, centro - grosor // 2, size - 3, centro + grosor // 2))
    return img

def crear_interfaz():
    root = tk.Tk()
    root.title("Sistema de Remisión – Área de Urgencias Hospitalarias")
    app_width, app_height = 1200, 800
    screen_w, screen_h = root.winfo_screenwidth(), root.winfo_screenheight()
    pos_x, pos_y = (screen_w - app_width) // 2, (screen_h - app_height) // 2
    root.geometry(f"{app_width}x{app_height}+{pos_x}+{pos_y}")
    root.configure(bg="#FFFFFF")

    estilo = ttk.Style()
    estilo.configure("Header.TLabel", font=("Segoe UI Semibold", 20), foreground="#0D47A1", background="#FFFFFF")
    estilo.configure("TLabel", background="#FFFFFF", font=("Segoe UI", 11))
    estilo.configure("TButton", font=("Segoe UI", 10, "bold"), padding=10)
    estilo.configure("Fixed.TEntry", fieldbackground="#F5F5F5", foreground="#444444")

    header = tk.Frame(root, bg="#FFFFFF")
    header.pack(fill="x", pady=(30, 10))
    icon_img = crear_icono_cruz_azul(32)
    tk.Label(header, image=icon_img, bg="#FFFFFF").pack(side="left", padx=(260, 10))
    ttk.Label(header, text="Sistema de Remisión – Área de Urgencias Hospitalarias", style="Header.TLabel").pack(side="left")
    header.icon_img = icon_img

    canvas_linea = tk.Canvas(root, bg="#FFFFFF", height=2, highlightthickness=0)
    canvas_linea.pack(fill="x", padx=260, pady=(0, 30))
    canvas_linea.create_line(0, 1, 680, 1, fill="#1976D2", width=3)

    card = tk.Frame(root, bg="#FFFFFF", highlightbackground="#E0E0E0", highlightthickness=1)
    card.place(relx=0.5, rely=0.52, anchor="center")
    card.configure(bd=0)
    card.grid_columnconfigure(1, weight=1)

    labels = [
        "Nombre completo del paciente:", "Tipo de documento del paciente:",
        "Número de documento:", "Edad:", "Especialidad:",
        "Nombre del remitente:", "Cargo del remitente:"
    ]
    entradas = {}

    for i, texto in enumerate(labels):
        ttk.Label(card, text=texto).grid(row=i, column=0, sticky="e", padx=10, pady=6)
        if "Tipo de documento" in texto:
            cb = ttk.Combobox(card, values=TIPOS_DOCUMENTO, state="readonly")
            cb.set(TIPOS_DOCUMENTO[0])
            cb.grid(row=i, column=1, padx=10, pady=6, ipadx=100)
            entradas[texto] = cb
        else:
            e = ttk.Entry(card, width=50)
            e.grid(row=i, column=1, padx=10, pady=6, ipadx=100)
            entradas[texto] = e

    ttk.Label(card, text="Nombre del hospital:").grid(row=7, column=0, sticky="e", padx=10, pady=6)
    e_hosp = ttk.Entry(card, width=50, style="Fixed.TEntry")
    e_hosp.insert(0, HOSPITAL_FIJO)
    e_hosp.state(["readonly"])
    e_hosp.grid(row=7, column=1, padx=10, pady=6, ipadx=100)

    ttk.Label(card, text="Número de contacto (Tel):").grid(row=8, column=0, sticky="e", padx=10, pady=6)
    e_tel = ttk.Entry(card, width=50, style="Fixed.TEntry")
    e_tel.insert(0, NUMERO_CONTACTO_FIJO)
    e_tel.state(["readonly"])
    e_tel.grid(row=8, column=1, padx=10, pady=6, ipadx=100)

    ttk.Label(card, text="Correo institucional del remitente:").grid(row=9, column=0, sticky="e", padx=10, pady=6)
    e_cor = ttk.Entry(card, width=50, style="Fixed.TEntry")
    e_cor.insert(0, CORREO_INSTITUCIONAL_FIJO)
    e_cor.state(["readonly"])
    e_cor.grid(row=9, column=1, padx=10, pady=6, ipadx=100)

    ttk.Label(card, text="Destinatarios (selección múltiple):").grid(row=10, column=0, sticky="ne", padx=10, pady=6)
    frame_chk = tk.Frame(card, bg="#FFFFFF")
    frame_chk.grid(row=10, column=1, sticky="w")
    vars_dest = {}
    for correo, etiqueta in DESTINATARIOS_OPCIONES:
        var = tk.BooleanVar(value=False)
        ttk.Checkbutton(frame_chk, text=f"{etiqueta} ({correo})", variable=var).pack(anchor="w")
        vars_dest[correo] = var

    def _campos():
        return {
            "Nombre completo del paciente": entradas["Nombre completo del paciente:"].get().strip(),
            "Tipo de documento del paciente": entradas["Tipo de documento del paciente:"].get().strip(),
            "Número de documento": entradas["Número de documento:"].get().strip(),
            "Edad": entradas["Edad:"].get().strip(),
            "Especialidad": entradas["Especialidad:"].get().strip(),
            "Nombre del remitente": entradas["Nombre del remitente:"].get().strip(),
            "Cargo del remitente": entradas["Cargo del remitente:"].get().strip(),
            "Nombre del hospital": HOSPITAL_FIJO,
            "Número de contacto": NUMERO_CONTACTO_FIJO,
            "Correo institucional del remitente": CORREO_INSTITUCIONAL_FIJO,
        }

    def _destinatarios():
        return [c for c, v in vars_dest.items() if v.get()]

    barra = tk.Frame(root, bg="#FFFFFF")
    barra.pack(pady=30)

    def efecto_boton(btn, color_base, color_hover):
        btn.bind("<Enter>", lambda e: btn.config(background=color_hover))
        btn.bind("<Leave>", lambda e: btn.config(background=color_base))
        btn.bind("<ButtonPress-1>", lambda e: btn.config(background="#42A5F5"))
        btn.bind("<ButtonRelease-1>", lambda e: btn.config(background=color_hover))

    def abrir_en_yahoo_web():
        campos = _campos()
        dests = _destinatarios()
        if not campos["Nombre completo del paciente"] or not dests:
            messagebox.showwarning("Campos incompletos", "Complete los campos requeridos y seleccione al menos un destinatario.")
            return
        asunto = generar_asunto(campos["Nombre completo del paciente"])
        yahoo_pegar_mensaje(campos, dests, asunto)

    btn_env = tk.Button(barra, text="📩 Enviar Solicitud", bg="#1976D2", fg="white", font=("Segoe UI", 11, "bold"),
                        relief="flat", padx=20, pady=10, borderwidth=0, cursor="hand2", command=abrir_en_yahoo_web)
    efecto_boton(btn_env, "#1976D2", "#0D47A1")
    btn_env.pack(side="left", padx=10)

    btn_salir = tk.Button(barra, text="Salir", bg="#E0E0E0", fg="#333333", font=("Segoe UI", 11, "bold"),
                          relief="flat", padx=20, pady=10, borderwidth=0, cursor="hand2", command=root.destroy)
    efecto_boton(btn_salir, "#E0E0E0", "#BDBDBD")
    btn_salir.pack(side="left", padx=10)

    root.mainloop()

if __name__ == "__main__":
    crear_interfaz()
