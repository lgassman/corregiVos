import logging
from corregivos.types import FileOrValue
import openai
import os
# class Worker

#     def work(self, local_repo, remote_repo, context):
#         raise CutChain()

class CutChain(Exception):
    pass

class DummyWorker:
    def work(self, local_repo, remote_repo, context):
        who = context.student.get('Identifier', "unknown")
        logging.debug("WORKING FOR {who} ")


class ReviewWorker:


    def work(self, local_repo, remote_repo, context):
        self.context = context
        self.context.comments=[]
        self.context.general_comment=""
        self.context.event="COMMENT"
        
        self._work(local_repo, remote_repo, context)
    
    def _work(self, local_repo, remote_repo, context):
        pass
    
    def comment(self, body, path=None, line=None, position=None):
    #'''<https://docs.github.com/en/rest/reference/pulls#reviews>'''
        if path:
            comment = {"body": body, "path": path}
            if line:
                comment["line"] = line
            if position:
                comment["position"] = position
            self.context.comments.append(comment)
        else: 
            if self.context.general_comment:
                self.context.general_comment = self.context.general_comment + " \n" + body
            else:
                self.context.general_comment = body
class Openai(ReviewWorker):

    evaluaciones= {
        "colecciones": "Buen uso de colecciones, el forEach solo se permite para órdenes. Una órden es  una acción que puede tener efecto y nunca tiene valor de retorno",
        "precálculos": "No tener atributos cuyos valores se pueden calcular en el momento de necesitarse",
        "polimorfismo": "Debe usarse polimorfismo. No tener `if` que consulten por la identidad de un objeto o denoten su tipo",
        "excepciones": "Use el método `error()` o `throw` para realizar validaciones. No tenga `if` que ignore un error",
        "tests": "los casos de ejemplo del enunciado deben tener al menos un test que lo prueba"
    }

    def __init__(self, api_key, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, tipo_assigment, enunciado, evaluar, noevaluar):

        self.api_key=FileOrValue()(api_key)#TODO: Modificar para que Factory pueda usar los tipos de la configuración así evitamos hacer la conversión acá
        openai.api_key=self.api_key       
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.tipo_assigment = tipo_assigment
        self.enunciado = FileOrValue()(enunciado)
        self.evaluar = evaluar
        self.noevaluar=noevaluar
    
    def _create_prompt(self, local_repo, remote_repo, context):
        prompt = '"""\n'

        prompt += f"Sos profesor de una materia de programación en una universidad para la enseñanza de POO con el lenguaje Wollok. Corregirás un {self.tipo_assigment} \n"
        prompt += f"La corrección será parseada por un programa para realizar un Pull Request en Github\n"
        prompt += "Reemplazarás [Resumen] con un resumen evaluando la calidad de la solución, [Archivo] con el nombre del archivo sobre el que haces comentario, [Comentario] con el comentario sobre el código fuente. [Línea] con el número de línea del archivo al que corresponde el comentario.\n"
        prompt += "# Evaluar:\n"
        for punto in self.evaluar: 
            prompt +=f"- {Openai.evaluaciones.get(punto, punto)}\n"
        prompt += "# No se espera que el estudiante tenga los siguientes conocmientos:\n"
        for punto in self.noevaluar: 
            prompt +=f"- {punto}\n"
        prompt += f"# Archivos con la solución de {context.student['name']}:\n"
        for fileName in self.wollokFiles(local_repo) :
            prompt += f"## {fileName}\n"
            prompt += f"```\n"
            prompt += f"{FileOrValue()(fileName)}\n"
            prompt += f"```\n"
        prompt += '"""\n'

        prompt += f"Evaluar los archivos de {context.student['name']} y completar: \n"
        prompt += "[Resumen]\n"
        prompt += "- [Archivo] \n"
        prompt += "  - [Linea]|[Comentario] \n"
        return prompt

    def _create_prompt_long(self, local_repo, remote_repo, context):
        prompt = '"""\n'

        prompt += f"Sos profesor de una materia de programación en una universidad para la enseñanza de POO con el lenguaje Wollok. Corregirás un {self.tipo_assigment} \n"
        prompt += f"La corrección será parseada por un programa para realizar un Pull Request en Github\n"
        prompt += "Reemplazarás [Resumen] con un resumen evaluando la calidad de la solución, [Nota] con una nota numérica dónde 2 es desaprobado. de 4 a 5 es aceptable, de 6 a 8 es bueno y de 9 a 10 muy bueno, [Archivo] con el nombre del archivo sobre el que haces comentario, [Comentario] con el comentario sobre el código fuente. [Línea] con el número de línea del archivo al que corresponde el comentario.\n"

        prompt += f"# Enunciado\n"
        prompt += "```\n"
        prompt += f"{self.enunciado}\n"
        prompt += "```\n"
        prompt += "# Evaluar:\n"
        for punto in self.evaluar: 
            prompt +=f"- {Openai.evaluaciones.get(punto, punto)}\n"
        prompt += "# No se espera que el estudiante tenga los siguientes conocmientos"
        for punto in self.noevaluar: 
            prompt +=f"- {punto}\n"
        prompt += f"# Archivos con la solución de {context.student['name']}:"
        for fileName in self.wollokFiles(local_repo) :
            prompt += f"## {fileName}\n"
            prompt += f"```\n"
            prompt += f"{FileOrValue()(fileName)}\n"
            prompt += f"```\n"
        prompt += '"""\n'

        prompt += f"Evaluar los archivos de {context.student['name']} y completar: \n"
        prompt += "[Resumen]\n"
        prompt += "- [Archivo] \n"
        prompt += "    - [Linea]:[Comentario] \n"
        return prompt

    def _work(self, local_repo, remote_repo, context):
        prompt = self._create_prompt(local_repo, remote_repo, context)
        logging.debug(prompt)

        response = openai.Completion.create(
            model=self.model,
            prompt= prompt,
            temperature= 0.7,
            max_tokens= 1000,
            top_p= 1,
            frequency_penalty= 0,
            presence_penalty= 0
        )
        logging.debug("############################################################")
        logging.debug(response)

    def wollokFiles(self, local_repo):
        files = []
        for root, _, filenames in os.walk(local_repo.working_dir):
            for filename in filenames:
                if filename.endswith(('.wlk', '.wpgm')):
                    files.append(os.path.join(root, filename))
        return files
class EndReviewWorker:

    def __init__(self, title=None, base=None, head=None):
        self.base = base 
        self.head = head
        self.title= title

    def work(self, local_repo, remote_repo, context):
        base = self.base or remote_repo.default_branch
        head = self.base or remote_repo.default_branch

        #pull_requests = remote_repo.get_pulls(base="feedback", head=remote_repo.default_branch)
        pull_requests = remote_repo.get_pulls(base=base, head=head)
        pr = next((pr for pr in pull_requests if not self.title or pr.title.lower() == self.title.lower()), None)
        commits_list = pr.get_commits().reversed.get_page(0)
        last_commit = commits_list[-1]
                
        pr.create_review(commit=last_commit, body=context.general_comment , event=context.event, comments=context.comments)
    