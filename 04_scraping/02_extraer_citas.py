# 02_extraer_citas.py — Localizar y extraer
# El selector es la mitad del trabajo. Truco de oficio: F12 en el navegador ->
# clic derecho sobre el elemento -> Copiar selector.
from selenium import webdriver
from selenium.webdriver.common.by import By

driver = webdriver.Chrome()
driver.get("https://quotes.toscrape.com")

# find_elementS (plural) devuelve una LISTA, vacía si no hay coincidencias.
# find_element (singular) devuelve la primera y lanza NoSuchElementException si no existe.
citas = driver.find_elements(By.CSS_SELECTOR, ".quote")
print(f"Encontradas {len(citas)} citas\n")

for c in citas:
    # CLAVE: buscamos dentro de `c`, no de `driver`. Eso es el "scoping", y es lo
    # que impide mezclar los datos de una tarjeta con los de la siguiente.
    texto = c.find_element(By.CSS_SELECTOR, ".text").text
    autor = c.find_element(By.CSS_SELECTOR, ".author").text
    # autor = driver.find_element(By.CSS_SELECTOR, ".author").text # Si buscamos con driver, retorna el primer elemento (no el de la cita)

    # .text da el texto visible; .get_attribute() da cualquier atributo del HTML
    # (href, src, value...), aunque no se vea en pantalla.
    enlace = c.find_element(By.CSS_SELECTOR, "a").get_attribute("href")

    etiquetas = [t.text for t in c.find_elements(By.CSS_SELECTOR, ".tag")]
    print(f"{autor}: {texto[:50]}...  {etiquetas}")
    print(f"   -> {enlace}")

driver.quit()
