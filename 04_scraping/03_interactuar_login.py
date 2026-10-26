# 03_interactuar_login.py — send_keys y click
# Selenium no solo lee: rellena formularios y pulsa botones. Con eso automatizas
# tareas repetitivas en webs internas, no solo scraping.
# El login de esta web de práctica acepta CUALQUIER credencial.
import time

from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://quotes.toscrape.com/login")

# Los sleep de aquí son ritmo de demo, para ver al robot teclear. No son
# sincronización: el fichero 04 enseña cómo se hace bien.
time.sleep(2)

# send_keys escribe tecla a tecla, disparando los eventos de teclado que muchos
# formularios con JavaScript necesitan para validar o activar el botón.
driver.find_element(By.ID, "username").send_keys("alumno")
time.sleep(2)

# En una web real la contraseña iría en una variable de entorno, nunca en el código.
driver.find_element(By.ID, "password").send_keys("1234")
time.sleep(2)

# Selector por atributo: útil cuando el botón no tiene id.
driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()

# ESTE sleep sí hace trabajo: el click navega a otra página y sin la pausa leeríamos
# el HTML de la ANTERIOR. Y ese es el problema — funciona con la red de hoy y falla
# con la de mañana. Solución correcta: fichero 04.
time.sleep(2)

# page_source es el HTML tal como está AHORA, con el JavaScript ya ejecutado.
print("¿Logueado?", "Logout" in driver.page_source)
time.sleep(5)
driver.quit()
