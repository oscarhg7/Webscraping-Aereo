# Webscraping-Aereo
✈️ Scraper de vuelos – Proyecto Aéreo
<br>

Script en Python para el scraping automatizado de vuelos desde Kayak, con extracción, limpieza y consolidación de datos en archivos Excel.

🎯 Objetivo del proyecto

Este proyecto permite:

Analizar precios de vuelos por trayecto

Comparar clases (Turista vs Premium/Business)

Evaluar diferencias entre vuelos domésticos e internacionales

Obtener indicadores agregados (precio medio)

Automatizar la generación de datasets estructurados
<br>


📌 Funcionalidades principales

🔎 Scraping automático con Selenium (Firefox headless)

🧹 Limpieza y normalización de precios

🎯 Filtrado por clases válidas (Economy, Premium Economy, Business, First)

💰 Selección del precio más barato por compañía + horario + clase

📊 Cálculo de precios medios por trayecto y grupo de clase

📁 Exportación automática a Excel

🔗 Unión de ficheros domésticos e internacionales

➕ Creación de hoja adicional con medias dentro del Excel final

📝 Sistema de logging en consola y en fichero (scraper.log)

🧠 Estructura del proyecto
<br>


El script principal contiene las siguientes secciones:

1️⃣ Configuración general

Incluye:

Rutas locales (RUTA_BASE, FIREFOX_BIN, GECKODRIVER)

Trayectos domésticos e internacionales

Fechas de ida y vuelta

Clases válidas

Filtros por aerolínea

Tipos de búsqueda

Opciones de equipaje

<br>
2️⃣ Funciones auxiliares
crear_driver()

Crea un driver Firefox en modo headless.

cargar_con_reintentos()

Carga la URL con reintentos y espera explícita hasta que aparezcan precios.

parsear_vuelos()

Extrae del HTML:

Precio

Compañía

Horario

Clase

Devuelve un DataFrame.

limpiar_precio()

Convierte el precio a formato numérico eliminando símbolos monetarios.

deduplicar_mas_baratos()

Mantiene únicamente el vuelo más barato por:

Compania + Horario + Clase
filtrar_clases()

Elimina clases no deseadas o combinaciones mixtas.

calcular_medias()

Agrupa por:

Trayecto + Grupo de Clase

y calcula el precio medio.


3️⃣ Scraping principal
scrape_vuelos()

Para cada combinación de:

Trayecto

Tipo

Aerolínea

Equipaje

Construye la URL dinámica y:

Realiza el scraping

Limpia y deduplica

Exporta a Excel

Calcula medias


4️⃣ Unión de ficheros
unir_excels()

Une vuelos domésticos e internacionales y:

Añade columna origen

Elimina duplicados

Recalcula medias

agregar_hoja_medias()

Añade una nueva hoja al Excel con:

Precio medio por Trayecto y Clase

Si la hoja existe, la reemplaza.




🛠 Requisitos
pip install pandas selenium beautifulsoup4 openpyxl

Además:

Mozilla Firefox instalado

geckodriver configurado correctamente

Ajustar rutas locales en el script

📈 Valor analítico

Este proyecto permite:

Construir series comparables entre fechas

Analizar dispersión por clase

Evaluar diferencias entre mercados

Automatizar la generación de indicadores replicables


