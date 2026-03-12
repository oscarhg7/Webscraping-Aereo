# -*- coding: utf-8 -*-
"""
Scraper de vuelos Kayak – v2 (actualizado para GitHub Actions)
"""

import os
import time
import logging
from datetime import date
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# -------------------------
# LOGGING
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# -------------------------
# CONFIGURACIÓN GENERAL
# -------------------------
RUTA_BASE = "data"

TRAYECTO_DOMESTICO = ['MAD-BRU']
TRAYECTO_INTERNAC  = ['MAD-BOG']

FECHAS = {
    "DOM_15DIAS": ("2026-03-25", "2026-03-27"),
    "DOM_1MES":   ("2026-04-15", "2026-04-17"),
    "INTER_15DIAS": ("2026-03-29", "2026-04-03"),
    "INTER_1MES":   ("2026-04-12", "2026-04-17")
}

CLASES_VALIDAS = {"Economy", "Premium Economy", "Business", "First"}

AEROLINEAS = [
    "&fs=airlines%3D~UX%3Bproviders%3D~UX",
    "&fs=airlines%3D~IB%3Bproviders%3D~IB",
    "&fs=airlines%3D~VY%3Bproviders%3D~VY",
]

TIPOS = [
    "?ucs=1gp416a&sort=bestflight_a",
    "/premium?ucs=1kklmbv&sort=bestflight_a",
]

MALETAS = {
    "":           "Sin equipaje",
    "%3Bbfc%3D1": "1 maleta facturada",
    "%3Bbfc%3D2": "2 maletas facturadas",
}

# -------------------------
# FUNCIONES AUXILIARES
# -------------------------

def crear_driver():
    """Crea un driver de Firefox en headless para GitHub Actions"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--window-size=1920,1080")

    # 🔹 Rutas explícitas en GitHub Actions
    firefox_path = "/usr/bin/firefox"
    geckodriver_path = "/usr/local/bin/geckodriver"

    options.binary_location = firefox_path
    service = Service(geckodriver_path)

    try:
        driver = webdriver.Firefox(service=service, options=options)
        log.info("✅ Driver creado correctamente")
        return driver
    except Exception as e:
        log.error("❌ Error creando driver: %s", e)
        raise

def cargar_con_reintentos(driver: webdriver.Firefox, url: str, intentos: int = 2, espera: int = 12) -> bool:
    """Carga una URL con reintentos. Devuelve True si tiene éxito."""
    for i in range(intentos):
        try:
            log.info("🔗 Cargando URL: %s (intento %d/%d)", url, i + 1, intentos)
            driver.get(url)
            WebDriverWait(driver, espera).until(
                EC.presence_of_element_located((By.CLASS_NAME, "e2GB-price-text"))
            )
            return True
        except Exception as exc:
            log.warning("❌ Intento %d/%d fallido para %s → %s", i + 1, intentos, url, exc)
            time.sleep(3)
    log.error("🚨 No se pudo cargar tras %d intentos: %s", intentos, url)
    return False

def parsear_vuelos(page_source: str, trayecto: str, maleta_etiqueta: str) -> pd.DataFrame | None:
    """Extrae datos de vuelo del HTML y devuelve un DataFrame o None si vacío."""
    soup = BeautifulSoup(page_source, "html.parser")
    precios = [x.get_text(strip=True) for x in soup.find_all("div", {"class": "e2GB-price-text"})]
    compania = [x.get_text(strip=True) for x in soup.find_all("div", {"class": "J0g6-operator-text"})]
    horarios = [x.get_text(strip=True) for x in soup.find_all("div", {"class": "vmXl vmXl-mod-variant-large"})]
    clases   = [x.get_text(strip=True) for x in soup.find_all("div", {"class": "DOum-name"})]

    horarios_unidos = [horarios[i] + " – " + horarios[i + 1] for i in range(0, len(horarios) - 1, 2)]
    min_len = min(len(precios), len(compania), len(horarios_unidos), len(clases))
    if min_len == 0:
        return None

    return pd.DataFrame({
        "Compania": compania[:min_len],
        "Trayecto": trayecto,
        "Precio":   precios[:min_len],
        "Horario":  horarios_unidos[:min_len],
        "Clase":    clases[:min_len],
        "Maletas":  maleta_etiqueta,
    })

def limpiar_precio(serie: pd.Series) -> pd.Series:
    return serie.str.replace(r"[€$£\s]", "", regex=True).str.replace(",", ".", regex=False).astype(float, errors="ignore")

def deduplicar_mas_baratos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_precio_num"] = limpiar_precio(df["Precio"])
    df = df.sort_values("_precio_num")
    df = df.drop_duplicates(subset=["Compania", "Horario", "Clase"], keep="first")
    return df.drop(columns=["_precio_num"])

def filtrar_clases(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["Clase"].isin(CLASES_VALIDAS)].reset_index(drop=True)

# -------------------------
# SCRAPING PRINCIPAL
# -------------------------

def scrape_vuelos(trayectos: list[str], fecha_ida: str, fecha_vuelta: str, ruta_carpeta: str) -> pd.DataFrame | None:
    """Scrapea vuelos y guarda un Excel. Devuelve el DataFrame final."""
    log.info("✈️ Scrapeando vuelos: %s %s-%s", trayectos, fecha_ida, fecha_vuelta)
    try:
        driver = crear_driver()
    except Exception as e:
        log.error("❌ Error en scrape_vuelos: %s", e)
        return None

    dfs = []

    try:
        for param_maleta, etiqueta_maleta in MALETAS.items():
            for tipo in TIPOS:
                for empresa in AEROLINEAS:
                    for trayecto in trayectos:
                        url = f"https://www.kayak.es/flights/{trayecto}/{fecha_ida}/{fecha_vuelta}{tipo}{empresa}{param_maleta}"
                        if not cargar_con_reintentos(driver, url):
                            continue
                        df = parsear_vuelos(driver.page_source, trayecto, etiqueta_maleta)
                        if df is not None:
                            dfs.append(df)
    finally:
        driver.quit()

    if not dfs:
        log.warning("⚠️ No se obtuvieron datos para %s / %s → %s", trayectos, fecha_ida, fecha_vuelta)
        return None

    df_final = pd.concat(dfs, ignore_index=True).drop_duplicates().pipe(filtrar_clases).pipe(deduplicar_mas_baratos)
    nombre_archivo = f"{trayectos[0]}_{fecha_ida}_{fecha_vuelta}.xlsx"
    ruta = os.path.join(ruta_carpeta, nombre_archivo)
    df_final.to_excel(ruta, index=False)
    log.info("✅ Excel generado: %s (%d filas)", ruta, len(df_final))

    return df_final

# -------------------------
# EJECUCIÓN
# -------------------------

if __name__ == "__main__":
    inicio = time.time()
    log.info("=== INICIO PROYECTO AEREO (DEBUG) ===")

    # Carpeta con fecha de hoy
    hoy = date.today().strftime("%Y-%m-%d")
    ruta_carpeta = os.path.join(RUTA_BASE, hoy)
    os.makedirs(ruta_carpeta, exist_ok=True)

    # --- Scraping ---
    for clave in ["DOM_15DIAS", "INTER_15DIAS", "DOM_1MES", "INTER_1MES"]:
        scrape_vuelos(TRAYECTO_DOMESTICO if "DOM" in clave else TRAYECTO_INTERNAC,
                      *FECHAS[clave],
                      ruta_carpeta)

    log.info("📌 Scraper finalizado")
    # --- Comprobación rápida de archivos ---
    archivos = os.listdir(ruta_carpeta)
    if archivos:
        log.info("📌 Archivos generados: %s", archivos)
    else:
        log.warning("⚠️ No se generó ningún archivo")
    fin = time.time()
    log.info("Tiempo total: %.1f minutos", (fin - inicio)/60)
