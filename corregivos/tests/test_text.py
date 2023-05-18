import logging
from corregivos.domain.workers import Openai



def test_text(): #Oh! como me gustaría un test de verdad
    text =  "En el archivo src/empleados.wlk hay una falta de polimorfismo en el m\u00e9todo pagarSueldo, se distinguen dos comportamientos posibles a partir del identificador de objeto, si es instancia de la clase baigorria o galvan. Esto no es recomendable porque se deja al usuario decidir con qu\u00e9 objetos trabaja, adem\u00e1s, se repite el c\u00f3digo en lugar de delegar la responsabilidad al objeto; la soluci\u00f3n propuesta corresponde a delegar la responsabilidad al objeto para controlar su comportamiento mediante polimorfismo.\n55 | Hay un code smell en el m\u00e9todo tieneDeuda, en el se compare la variable deuda con 0, esto deja entender que deuda represente su identidad, sin embargo esto responderia a la pregunta \u00bfEsta deuda como objeto v\u00e1lido?, lo que recomendamos es mantener los valores de los atributos e implementar m\u00e9todos que controle su comportamiento dependiendo del estado de los atributos. \"\"\""
    obj = Openai(model=None, temperature=None, max_tokens=None, top_p=None, frequency_penalty=None, presence_penalty=None, teachers=None)
    obj._files=["/src/empleados.wlk"]
    logging.error(obj.parse(text, "/src/empleados.wlk"))

test_text()
  