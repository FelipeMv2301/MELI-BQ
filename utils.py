"""
Funciones reutilizables entre apps — mismo rol que gestorBQ/utils.py (no es una app Django, solo
funciones puras importables desde cualquier lado).
"""

import html as html_lib
import re

_TAG_BREAK = re.compile(r"</(h[1-6]|p|div|li|tr)>", re.IGNORECASE)
_BR = re.compile(r"<br\s*/?>", re.IGNORECASE)
_LI_OPEN = re.compile(r"<li[^>]*>", re.IGNORECASE)
_A_TAG = re.compile(r"<a\b[^>]*>(.*?)</a>", re.IGNORECASE | re.DOTALL)
_TR_TAG = re.compile(r"<tr[^>]*>(.*?)</tr>", re.IGNORECASE | re.DOTALL)
_TD_TAG = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.IGNORECASE | re.DOTALL)
_ANY_TAG = re.compile(r"<[^>]+>")

# Best-effort — ML no publica una allow-list de caracteres, solo se sabe (por la doc de
# descripción) que emoji hacen fallar el POST/PUT con item.description.type.invalid. Deja intacto
# el español (acentos, ñ, ±, ×, etc. — confirmados en el ejemplo real, no son el problema).
_EMOJI = re.compile(
    "["
    "\U0001F000-\U0001FFFF"
    "\U00002600-\U000027BF"
    "\U00002190-\U000021FF"
    "]+"
)


def _aplanar_fila_tabla(match):
    celdas = _TD_TAG.findall(match.group(1))
    celdas = [_ANY_TAG.sub("", celda).strip() for celda in celdas]
    celdas = [celda for celda in celdas if celda]
    return "\n" + " ".join(celdas) if celdas else ""


def limpiar_descripcion_html(html_bruto):
    """
    Convierte la descripción HTML de WooCommerce (tablas de specs, listas, links, entidades) al
    texto plano que exige la API de Mercado Libre — ver
    backlog_proyecto/Documentaciones/MercadoLibre/descripcion-de-productos.md (HU-CM2.4).

    Sin dependencias externas (bs4/lxml) a propósito: el HTML real de WooCommerce (confirmado
    contra ejemplo-payload-woocommerce.json) es simple — h3/p/br/table/ul/li/a/em, sin scripts ni
    shortcodes — y no las necesita.
    """
    if not html_bruto:
        return ""

    texto = html_bruto

    # Tablas de specs: una línea por fila (ej. "Largo: 180 mm").
    texto = _TR_TAG.sub(_aplanar_fila_tabla, texto)

    # Links: conservar solo el texto visible, descartar la URL — no es clickeable en texto plano,
    # y varios apuntan a un hosting de la plataforma anterior (Jumpseller) que no debe exponerse.
    texto = _A_TAG.sub(lambda m: _ANY_TAG.sub("", m.group(1)), texto)

    # <li> -> "- texto"
    texto = _LI_OPEN.sub("\n- ", texto)

    # Saltos de línea explícitos.
    texto = _BR.sub("\n", texto)
    texto = _TAG_BREAK.sub("\n", texto)

    # Cualquier tag que quede (aperturas de p/table/ul/em/strong, etc.) se descarta sin afectar
    # el texto — ya se extrajo lo que importaba de cada uno arriba.
    texto = _ANY_TAG.sub("", texto)

    # Entidades HTML (&#8211; -> –, &amp; -> &, etc.)
    texto = html_lib.unescape(texto)

    texto = _EMOJI.sub("", texto)

    # Colapsar líneas vacías/espacios sueltos que dejó la limpieza de tags.
    lineas = [linea.strip() for linea in texto.splitlines()]
    lineas = [linea for linea in lineas if linea]
    return "\n".join(lineas)
