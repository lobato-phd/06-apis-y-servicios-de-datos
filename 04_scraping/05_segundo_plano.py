# 05_segundo_plano.py — el mismo scraper del fichero 04, pero SIN ventana (headless)
# Mismo Chrome, mismo JavaScript; simplemente no dibuja en pantalla. Sin esto no hay
# scraping en un servidor, en un contenedor Docker (capítulo 5) ni en una tarea programada.
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

opciones = Options()
opciones.add_argument("--headless=new")

# Sin ventana, Chrome puede arrancar con un tamaño mínimo, y muchas webs responsive
# OCULTAN elementos en pantallas pequeñas: el scraper no los encuentra y parece que
# la web ha cambiado. Fijar el tamaño evita ese fallo fantasma.
opciones.add_argument("--window-size=1920,1080")

# En Docker y como root harían falta además --no-sandbox y --disable-dev-shm-usage.
# Aquí no: bajan defensas del navegador sin necesidad.

driver = webdriver.Chrome(options=opciones)   # la única diferencia con el fichero 04
driver.get("https://quotes.toscrape.com/js-delayed/")

print("Nada más cargar:", len(driver.find_elements(By.CSS_SELECTOR, ".quote")), "citas")

# Idéntico al fichero 04: el modo headless no cambia nada.
t0 = time.time()
wait = WebDriverWait(driver, 15)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".quote")))

citas = driver.find_elements(By.CSS_SELECTOR, ".quote")
print(f"Tras esperar {time.time() - t0:.1f} s: {len(citas)} citas")

# EL PRECIO DEL HEADLESS: cuando algo falla, no vemos nada. La captura es nuestra
# única ventana al navegador. La hacemos siempre en el except de un scraper real.
captura = Path(__file__).with_name("captura.png")
driver.save_screenshot(str(captura))
print(f"Captura guardada en {captura.name}")

driver.quit()
