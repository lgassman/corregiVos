import logging
from corregivos.types import FileOrValue
import openai
import os
import json
# class Worker

#     def work(self, local_repo, remote_repo, context):
#         raise CutChain()

class CutChain(Exception):
    pass

class DummyWorker:
    def grade(self, local_repo, remote_repo, context):
        who = context.student.get('identifier', "unknown")
        logging.debug(f"GRADE TO {who} : {context.assignment}")

    def train(self, local_repo, remote_repo, context):
        who = context.student.get('identifier', "unknown")
        logging.debug(f"TRAINING FROM {who} : {context.assignment_name}")

    def end(self, context):
        logging.debug("END")


class ReviewWorker:


    def grade(self, local_repo, remote_repo, context):
        self.context = context
        self.context.comments=[]
        self.context.general_comment=""
        self.context.event="COMMENT"
        
        self._grade(local_repo, remote_repo, context)
    
    def train(self, local_repo, remote_repo, contex):
        pass
    
    def end(self, context):
        pass
    
    def _grade(self, local_repo, remote_repo, context):
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
    
    def to_comment(self):
        return None

class PullRequestReviwer():
    
    def get_pull_request(self, remote_repo,title= "feedback" , base="feedback", head=None):
        head = head or remote_repo.default_branch
        pull_requests = remote_repo.get_pulls(base=base, head=head)
        return next((pr for pr in pull_requests if not title or pr.title.lower() == title.lower()), None)
class Openai(ReviewWorker,PullRequestReviwer):

    evaluaciones= {
        "colecciones": "Buen uso de colecciones, el forEach solo se permite para órdenes. Una órden es  una acción que puede tener efecto y nunca tiene valor de retorno",
        "precálculos": "No tener atributos cuyos valores se pueden calcular en el momento de necesitarse",
        "polimorfismo": "Debe usarse polimorfismo. No tener `if` que consulten por la identidad de un objeto o denoten su tipo",
        "excepciones": "Use el método `error()` o `throw` para realizar validaciones. No tenga `if` que ignore un error",
        "tests": "los casos de ejemplo del enunciado deben tener al menos un test que lo prueba"
    }

    def __init__(self, api_key, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, tipo_assigment, enunciado, evaluar, noevaluar, teachers):
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
        self.teachers=teachers
    

    def _create_rol(self):
        prompt = f"Sos profesor de una materia de programación en una universidad para la enseñanza de POO con el lenguaje Wollok. Corregirás un {self.tipo_assigment} \n"
        prompt += f"La corrección será parseada por un programa para realizar un Pull Request en Github\n"
        return prompt

    def _create_insertion_request(self):
        return "Reemplazarás [Resumen] con un resumen evaluando la calidad de la solución, [Archivo] con el nombre del archivo sobre el que haces comentario, [Comentario] con el comentario sobre el código fuente. [Línea] con el número de línea del archivo al que corresponde el comentario."
    
    def _create_prompt(self, local_repo, remote_repo, context, training=False):
        prompt = '"""\n'
        if not training:
            prompt += self._create_rol()
            prompt += "# Evaluar:\n"
            for punto in self.evaluar: 
                prompt +=f"- {Openai.evaluaciones.get(punto, punto)}\n"
            prompt += "# No se espera que use:\n"
            for punto in self.noevaluar: 
                prompt +=f"- {punto}\n"
        prompt += self._create_insertion_request()
        prompt += f"# Archivos :\n"
        for fileName in self.wollokFiles(local_repo) :
            prompt += f"## {fileName}\n"
            prompt += f"```\n"
            prompt += f"{FileOrValue()(fileName)}\n"
            prompt += f"```\n"
        prompt += '"""\n'

        prompt += f"Evaluar los archivos y completar: \n"
        prompt += "[Resumen]\n"
        prompt += "- [Archivo] \n"
        prompt += "    - [Linea] | [Comentario] \n"
        return prompt

    def _grade(self, local_repo, remote_repo, context):
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

   
 
    def train(self, local_repo, remote_repo, context):
        prompt = self._create_prompt(local_repo, remote_repo, context, training=True)
        logging.debug(prompt)

        logging.debug("############################################################")
        pr = self.get_pull_request(remote_repo)
        
        reviews = pr.get_reviews()
        resumen  = "\n".join([review.body for review in reviews if review.user.login.lower() in self.teachers])
        comments = [comment for comment in pr.get_comments() if comment.user.login.lower() in self.teachers]
        if len(comments) == 0 and (not resumen or resumen.isspace()):
            logging.debug(f"No review for {context.student['identifier']}")
            return #no review of this

        fileCommentsDict={}
        for comment in comments:
            if hasattr(comment, "path") and comment.path:
                fileComments = fileCommentsDict.get(comment.path)
                if fileComments is None:
                    fileComments = []
                    fileCommentsDict[comment.path] = fileComments
                fileComments.append({"line":comment.position or 0, "body":comment.body})
            else:
                reviews += f"\n{comment.body}"
        completation=" " + resumen + "\n"
        for file in fileCommentsDict:
            completation += f"- {file} \n"
            for comment in fileCommentsDict[file]:
                completation += f"    - {comment['line']} | {comment['body']}\n"
        
        context.append_global("training", {"prompt":prompt, "completation":completation})


    def wollokFiles(self, local_repo):
        files = []
        for root, _, filenames in os.walk(local_repo.working_dir):
            for filename in filenames:
                if filename.endswith(('.wlk', '.wpgm')):
                    files.append(os.path.join(root, filename))
        return files
      
    def end(self, context):
        pass

class EndReviewWorker(PullRequestReviwer):

    def __init__(self, training_file):
        self.training_file=os.path.expanduser(training_file)

    def grade(self, local_repo, remote_repo, context):

        pr = self.get_pull_request(remote_repo)
        commits_list = pr.get_commits().reversed.get_page(0)
        last_commit = commits_list[-1]
                
        pr.create_review(commit=last_commit, body=context.general_comment , event=context.event, comments=context.comments)
    
    def train(self, local_repo, remote_repo, contex):
        pass
    
    def end(self, context):
        logging.debug("####################TRAINING SET###################33")
        with open(self.training_file, "w") as file:
            json.dump(context.training, file)

    