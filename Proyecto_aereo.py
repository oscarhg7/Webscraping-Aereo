# -*- coding: utf-8 -*-
"""
Scraper de vuelos Kayak – versión final para GitHub Actions con debug
"""

import os
import time
import logging
from datetime import date
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# -------------------------
# LOGGING
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper_debug.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)
log.info("=== INICIO PROYECTO AEREO (DEBUG) ===")

# -------------------------
# CONFIGURACIÓN
# -------------------------
RUTA_BASE = "data"
TRAYECTO_DOMESTICO = ["MAD-BRU"]
TRAYECTO_INTERNAC = ["MAD-BOG"]

FECHAS = {
    "DOM_15DIAS": ("2026-03-25", "2026-03-27"),
    "INTER_15DIAS": ("2026-03-29", "2026-04-03"),
}

# -------------------------
# FUNCIONES
# -------------------------

def crear_driver():
    """Crea un driver de Firefox headless con debug"""
    try:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")

        # Ruta explícita del binario de Firefox en Ubuntu GH Actions
        firefox_path = "/usr/bin/firefox"
        if not os.path.exists(firefox_path):
            log.error("No se encontró Firefox en %s", firefox_path)
        else:
            log.info("Firefox encontrado en: %s", firefox_path)
            options.binary_location = firefox_path

        service = Service()
        driver = webdriver.Firefox(service=service, options=options)
        log.info("Driver Firefox creado correctamente")
        return driver
    except Exception as e:
        log.exception("Error creando driver: %s", e)
        raise

def cargar_con_reintentos(driver, url, intentos=2, espera=12):
    """Carga una URL con reintentos"""
    for i in range(intentos):
        try:
            driver.get(url)
            WebDriverWait(driver, espera).until(
                EC.presence_of_element_located((By.CLASS_NAME, "e2GB-price-text"))
            )
            log.info("Página cargada correctamente: %s", url)
            return True
        except Exception as exc:
            log.warning("Intento %d/%d fallido para %s → %s", i+1, intentos, url, exc)
            time.sleep(3)
    log.error("No se pudo cargar tras %d intentos: %s", intentos, url)
    return False

def scrape_vuelos(trayectos, fecha_ida, fecha_vuelta):
    """Ejemplo mínimo de scraping con debug"""
    try:
        log.info("Scrapeando vuelos: %s %s-%s", trayectos, fecha_ida, fecha_vuelta)
        driver = crear_driver()
        for trayecto in trayectos:
            url = f"https://www.kayak.es/flights/{trayecto}/{fecha_ida}/{fecha_vuelta}?sort=bestflight_a"
            log.info("Accediendo a URL: %s", url)
            if cargar_con_reintentos(driver, url):
                log.info("Scraping simulado para %s cargado correctamente", trayecto)
            else:
                log.error("No se pudo cargar %s", trayecto)
        driver.quit()
    except Exception as e:
        log.exception("Error en scrape_vuelos: %s", e)
        raise

# -------------------------
# EJECUCIÓN
# -------------------------
if __name__ == "__main__":
    try:
        os.makedirs(RUTA_BASE, exist_ok=True)
        scrape_vuelos(TRAYECTO_DOMESTICO, *FECHAS["DOM_15DIAS"])
        scrape_vuelos(TRAYECTO_INTERNAC, *FECHAS["INTER_15DIAS"])
        log.info("Scraping finalizado correctamente")
    except Exception as e:
        log.exception("Error general en ejecución: %s", e)
