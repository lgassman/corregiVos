import logging
from corregivos.domain.workers import Openai
import json

def test_text(): #Oh! como me gustaría un test de verdad
    x = """{
"resumen" : "Se detectaron diversas malas prácticas en el código fuente de los archivos analizados: No uso de polimorfismo, presencia de precálculos, presencia de atributos interdependientes, presencia de 'If's que denoten la identidad del objeto, presencia de 'If' que formen una 'Overcomplicated Boolean Expression' y la presencia de code smells.",
    "issues": [
        {"file":"src/camion.wlk", "issue":"No se está aprovechando el uso de polimorfismo.", "line": 33},
        {"file":"src/camion.wlk", "issue":"En la línea 49 se realiza un precálculo para saber si el camion supera el pesoMax.", "line":49},
        {"file":"src/camion.wlk", "issue":"Se debe evitar el uso de precálculos para asignar el peso de los objetos a la variable 'pesos', en lugar de ello se debería usar el método 'peso' de cada objeto.", "line":10},
        {"file":"src/camion.wlk", "issue":"En la línea 10 se realiza un mal uso de atributos interdependentes, la variable 'pesos' debería ser calculada al momento de llamar el método 'pesoTotal' en la línea 27.", "line":10},
        {"file":"src/camion.wlk", "issue":"En la línea 32, el 'If' denota la identidad del objeto 'camino', como se está trabajando con POO, se debería usar el 'instanceOf' o dotar a 'caminos ' de métodos para determinar si es la ruta9 o caminos vecinale.", "line":32},
        {"file":"src/camion.wlk", "issue":"En la línea 54 se forma Overcomplicated Boolean Expression, se podría acotar el condicional, replace conditionals with polymorphism.", "line":54},
        {"file":"src/camion.wlk", "issue":"El archivo presenta el Code Smell 'Data Clumps', hay métodos en camion que toman mas de dos parámetros que se repiten entre si. ('tieneAlgoQuePesaEntre', 'transportar', 'validarAlmacenar').", "line":10}
    ]
}
"""
    print(x.strip())
    s = json.loads(x.strip())
    print(s)

test_text()
  