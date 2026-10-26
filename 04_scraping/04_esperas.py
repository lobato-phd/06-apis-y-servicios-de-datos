# 04_esperas.py — el error nº 1 del principiante, y su solución
# Esta página pinta las citas con JavaScript unos segundos DESPUÉS de cargar:
# el HTML ya está, pero el contenido que buscamos todavía no.
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

driver = webdriver.Chrome()
driver.get("https://quotes.toscrape.com/js-delayed/")

# LA TRAMPA: buscar nada más cargar. Imprime 0, y sin excepción ni aviso — con
# find_elements el fallo es SILENCIOSO: una lista vacía parece "no había datos".
print("Nada más cargar:", len(driver.find_elements(By.CSS_SELECTOR, ".quote")), "citas")

# LA SOLUCIÓN: espera explícita.
t0 = time.time()

# No duerme 15 segundos: comprueba cada 0,5 s y sigue EN CUANTO se cumple. Por eso
# es más rápida que un sleep, además de más fiable. Los 15 s son el tope; si se
# agota, lanza TimeoutException.
wait = WebDriverWait(driver, 15)

# Condiciones, de menos a más exigente:
#   presence_of_element_located    -> está en el DOM (puede ser invisible)
#   visibility_of_element_located  -> está Y se ve
#   element_to_be_clickable        -> se ve Y está habilitado -> para .click()
# Elegir mal aquí causa la mitad de los scrapers intermitentes.
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".quote")))

# Volvemos a buscar en plural a propósito: la espera solo garantiza que existe LA
# PRIMERA cita, no las diez.
citas = driver.find_elements(By.CSS_SELECTOR, ".quote")
print(f"Tras esperar {time.time() - t0:.1f} s: {len(citas)} citas")

driver.quit()
