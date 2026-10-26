# 06_scraper_paginacion.py — recorre todas las páginas y guarda un JSON
# Todas las piezas anteriores juntas. Y fijémonos en lo que produce: el citas.json
# que llevamos sirviendo desde el capítulo 3, el que nos daban hecho. Ya no.
import json
import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

# Freno propio: la condición de parada vive en una web que no controlamos.
MAX_PAGINAS = 50

driver = webdriver.Chrome()

# Con un navegador abierto hay que cerrarlo pase lo que pase: el finally se ejecuta
# también si salta una excepción. Sin esto, cada fallo deja un Chrome huérfano.
try:
    driver.get("https://quotes.toscrape.com")
    resultado = []
    pagina = 1

    while True:
        for c in driver.find_elements(By.CSS_SELECTOR, ".quote"):
            resultado.append({
                # La web envuelve las citas en comillas tipográficas: las quitamos
                # aquí, en la extracción, para que el dato salga ya limpio.
                "texto": c.find_element(By.CSS_SELECTOR, ".text").text.strip("“”"),
                "autor": c.find_element(By.CSS_SELECTOR, ".author").text,
                "etiquetas": [t.text for t in c.find_elements(By.CSS_SELECTOR, ".tag")],
            })

        # Un scraper que recorre diez páginas en silencio parece colgado.
        print(f"Página {pagina}: {len(resultado)} citas acumuladas")

        if pagina >= MAX_PAGINAS:
            print(f"Tope de {MAX_PAGINAS} páginas alcanzado, paramos")
            break

        try:
            # No preguntamos si existe "Next": lo pulsamos hasta que Selenium
            # proteste. La excepción ES la condición de salida.
            driver.find_element(By.CSS_SELECTOR, "li.next > a").click()
            pagina += 1

            # OJO: esto NO es el sleep mal usado del fichero 04. Aquel esperaba a que
            # apareciera un elemento; esta pausa modera NUESTRO ritmo de peticiones
            # para no castigar un servidor ajeno.
            time.sleep(0.5)
        except NoSuchElementException:
            break                    # el botón "Next" ya no existe: última página
finally:
    driver.quit()

# El navegador ya está cerrado: guardar es trabajo de Python.
destino = Path(__file__).with_name("citas.json")
with open(destino, "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)   # ensure_ascii: tildes legibles

print(f"\n{len(resultado)} citas guardadas en {destino.name}")
