# 01 — El "hola mundo" de Selenium: abrir un navegador de verdad y leerle el título.
# No es una simulación: es el mismo Chrome que usamos a diario, pilotado desde Python.
import time

from selenium import webdriver

# `driver` es el mando a distancia del navegador. Selenium Manager descarga el
# driver solo (v4.6+). Si falla con NoSuchDriverException, casi siempre falta Chrome.
driver = webdriver.Chrome()

# .get() bloquea hasta que la página carga. Aquí está la diferencia con requests:
# el JavaScript de la página YA se ha ejecutado.
driver.get("https://quotes.toscrape.com")

print(driver.title)  # "Quotes to Scrape"

# Solo para la demo, para que dé tiempo a ver la ventana. Nunca sincronizamos un
# scraper con sleep(): para eso están las esperas explícitas (fichero 04).
time.sleep(1)

# Cierra la ventana Y mata el proceso del driver; sin esto quedan Chromes huérfanos.
# (close() solo cierra la pestaña actual; el que limpia de verdad es quit()).
driver.quit()

