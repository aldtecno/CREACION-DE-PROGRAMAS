"""Utilidades para cargar la configuración del sistema de remisión."""

from __future__ import annotations

import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_CONFIG: Dict[str, Any] = {
    "hospital": "Nuestra Señora de las Mercedes",
    "contact_number": "3138899808",
    "institutional_email": "urgenciasaladoblanco@yahoo.com",
    "documents_folder": "~/Documents",
    "compose_wait_seconds": 8.5,
    "recipients": [
        {
            "email": "referenciaycontrarreferencia2@hospitalpitalito.gov.co",
            "label": "Hospital Pitalito",
        },
        {
            "email": "referenciaycontrarreferencia@clinicareinaisabel.com",
            "label": "Referencia Ycontrareferencia",
        },
    ],
}


class ConfiguracionError(RuntimeError):
    """Error al cargar la configuración externa."""


def _normalizar_recipientes(recipients: Any) -> List[Dict[str, str]]:
    if not isinstance(recipients, list):
        return deepcopy(DEFAULT_CONFIG["recipients"])

    resultado: List[Dict[str, str]] = []
    for item in recipients:
        if not isinstance(item, dict):
            continue
        correo = item.get("email")
        etiqueta = item.get("label")
        if not isinstance(correo, str) or not correo.strip():
            continue
        resultado.append(
            {
                "email": correo.strip(),
                "label": etiqueta.strip() if isinstance(etiqueta, str) and etiqueta.strip() else correo.strip(),
            }
        )
    return resultado or deepcopy(DEFAULT_CONFIG["recipients"])


def cargar_configuracion(ruta: Path | None = None) -> Dict[str, Any]:
    """Carga la configuración desde ``ruta`` fusionándola con los valores predeterminados."""

    ruta_config = ruta or Path(__file__).with_name("configuracion.json")
    configuracion = deepcopy(DEFAULT_CONFIG)

    if ruta_config.exists():
        try:
            with ruta_config.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except json.JSONDecodeError as exc:  # pragma: no cover - Protección ante archivos corruptos
            raise ConfiguracionError(f"El archivo de configuración no es válido: {exc}") from exc
        except OSError as exc:
            raise ConfiguracionError(f"No se pudo leer la configuración: {exc}") from exc
        else:
            if isinstance(datos, dict):
                for clave in ("hospital", "contact_number", "institutional_email", "documents_folder"):
                    valor = datos.get(clave)
                    if isinstance(valor, str) and valor.strip():
                        configuracion[clave] = valor.strip()
                espera = datos.get("compose_wait_seconds")
                if isinstance(espera, (int, float)) and espera > 0:
                    configuracion["compose_wait_seconds"] = float(espera)
                configuracion["recipients"] = _normalizar_recipientes(datos.get("recipients"))

    configuracion["hospital"] = os.getenv("REMISION_HOSPITAL", configuracion["hospital"])
    configuracion["contact_number"] = os.getenv("REMISION_CONTACT_NUMBER", configuracion["contact_number"])
    configuracion["institutional_email"] = os.getenv(
        "REMISION_INSTITUTIONAL_EMAIL", configuracion["institutional_email"]
    )
    configuracion["documents_folder"] = os.getenv("REMISION_DOCUMENTS_FOLDER", configuracion["documents_folder"])

    espera_env = os.getenv("REMISION_COMPOSE_WAIT_SECONDS")
    if espera_env:
        try:
            espera_val = float(espera_env)
        except ValueError:
            pass
        else:
            if espera_val > 0:
                configuracion["compose_wait_seconds"] = espera_val

    return configuracion
