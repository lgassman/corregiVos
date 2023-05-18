import logging
from corregivos.types import FileOrValue
import openai
import os
import json
import re
 
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


class ReviewWorker:


    def grade(self, local_repo, remote_repo, context):
        self.context = context
        self.context.comments=[]
        self.context.general_comment=""
        self.context.event="COMMENT"
        
        self._grade(local_repo, remote_repo, context)
    
    def train(self, local_repo, remote_repo, contex):
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
        "precálculos": "No tener atributos cuyos valores se pueden calcular en el momento de necesitarse",
        "polimorfismo": "Debe usarse polimorfismo. No tener `if` que consulten por la identidad de un objeto o denoten su tipo",
    }

    def __init__(self, model, temperature, max_tokens, top_p, frequency_penalty, presence_penalty, teachers):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.frequency_penalty = frequency_penalty
        self.presence_penalty = presence_penalty
        self.teachers=teachers
    
    def _create_rol(self):
        return """Sos profesor de una materia de programación en una universidad para la enseñanza de POO con el lenguaje Wollok y evaluarás una solución de un estudiante.
Tu objetivo es proporcionar información precisa sobre malas prácticas en el código fuente y recomendar una alternativa. Esta información se debe presentar con un breve resumen general y una lista que tenga para cada archivo todos los comentarios. Un comentario tiene el número de línea del archivo donde se detectó el problema y un texto que indica cuál es la mala práctica, por qué se considera mala práctica y una alternativa de solución de la mala práctica. 
Estas son algunas malas prácticas a detectar:
-  No usa polimorfismo dónde se pueda.
-  Presencia de precálculos.
-  Precencia de atributos interdependientes
-  Presencia de 'If's que denoten la identidad del objeto
-  Presencia de 'If' que formen una 'Overcomplicated Boolean Expression'
-  Presencia de code smells
En caso de code smell indicar cuál es el mismo.
"""

    def short_file_name(self, filename, local_repo):
        return filename.replace(local_repo.working_dir + '/', '')
    
    def _create_prompt(self, local_repo, remote_repo, context, training=False):
        prompt = '"""\n'
        if not training:
            prompt += self._create_rol()
#        prompt = f"{context.student['identifier']}\n"
        prompt += f"# Archivos\n"
        for fileName in self.wollokFiles(local_repo) :
            prompt += f"## {self.short_file_name(fileName, local_repo) }\n"
            prompt += f"```\n"
            prompt += f"{FileOrValue()(fileName)}\n"
            prompt += f"```\n"
        if not training:
            prompt += """Armarás un json bien formado con la estructura que se describe a continuación, reemplazando [resumen] con el resumen general ,  [file] con el nombre del archivo sobre el que haces comentario, [issue] con el texto del comentario sobre el código fuente que tiene una mala práctica y [line] con el número entero de línea del archivo al que corresponde el comentario. 
{"resumen":"[resumen]"
  "issues": [ {"file":"[file]", "issue":"[issue]",  "line":[line]} ]
}
"""
            prompt += '"""'
        else:
            prompt += '"""'
            prompt += self.prompt_suffix
        
        return prompt

    def _grade(self, local_repo, remote_repo, context):
        prompt = self._create_prompt(local_repo, remote_repo, context)
        logging.debug(prompt)

        response = openai.Completion.create(
            model=self.model,
            prompt= prompt,
            temperature= float(self.temperature),
            max_tokens= int(self.max_tokens),
            top_p= int(self.top_p),
            frequency_penalty= float(self.frequency_penalty),
            presence_penalty= float(self.presence_penalty)
        )
        logging.debug(response)
        self.parse(response["choices"][0]["text"])

    def parse(self, text): 
        try :
            json_response = json.loads(text)
            self.comment(body="*Generado por openai*\n" + json_response["resumen"])
            for comment in json_response["issues"]:
                try:
                    self.comment(body="*Generado por openai*\n" + comment["issue"], line=comment["line"], path=comment["file"])
                except:
                    self.comment(f"No pudimos parsear esta parte de respuesta de openai: {json.dumps(comment)}" )
        except Exception as e:
                logging.exception(f"{e} parsing response {text}")
                self.comment(f"No pudimos parsear la respuesta de openai, pero aquí te la dejamos igual: {text}" )


    def train(self, local_repo, remote_repo, context):
        prompt = self._create_prompt(local_repo, remote_repo, context, training=True)
        logging.debug(prompt)

        pr = self.get_pull_request(remote_repo)
        
        reviews = pr.get_reviews()
        resumen  = "\n".join([review.body for review in reviews if review.user.login.lower() in self.teachers])
        resumen = resumen.lstrip()
        all_comments = pr.get_comments()
        comments = [comment for comment in all_comments if comment.user.login.lower() in self.teachers]
        if len(comments) == 0 and (not resumen or resumen.isspace()):
            reviewers = ", ".join([comment.user.login for comment in all_comments])
            msg=f"No review for {context.student['identifier']} reviewers:{reviewers}"
            logging.info(msg)
            context.append_global("ignores", msg)
            return #no review of this

        issues= [{"file":comment["path"], "issue": comment["body"], "line": comment["position"]} for comment in comments if hasattr(comment, "path")] 
        completion={"resumen":resumen, "issues":issues}
        
        context.append_global("training", {"prompt":prompt, "completion":completion})


    def wollokFiles(self, local_repo):
        files=[]
        for root, _, filenames in os.walk(local_repo.working_dir):
            for filename in filenames:
                if self.is_wollok_file(filename):
                    files.append(os.path.join(root, filename))
        return files
    
    def is_wollok_file(self, filename):
        return filename.endswith(('.wlk', '.wpgm'))
    
    @property
    def prompt_suffix(self):
        return getattr(self, "github_object").prompt_suffix

    @property
    def completion_suffix(self):
        return getattr(self, "github_object").completion_suffix
 

class EndReviewWorker(PullRequestReviwer):

    def __init__(self, base_model,model_suffix):
        super().__init__
        self.base_model=base_model
        self.model_suffix=model_suffix

    def grade(self, local_repo, remote_repo, context):

        pr = self.get_pull_request(remote_repo)
        commits_list = pr.get_commits().reversed.get_page(0)
        last_commit = commits_list[-1]

        logging.info(f"commit={last_commit}, body={context.general_comment} , event={context.event}, comments={context.comments}")        
        pr.create_review(commit=last_commit, body=context.general_comment , event=context.event, comments=context.comments)
    
    def train(self, local_repo, remote_repo, contex):
        pass
    
    def end_train(self, context):
        logging.info(f"#saving {self.training_file} entries: {len(context.training)} ignores: {len(context.ignores or [])} errors: {len(context.errors or [])}")
       
        #convertir al formato de openai
        with open(self.training_file, "w") as file:
            for obj in context.training:
                file.write(json.dumps(obj) + "\n")
    
    def upload(self, context):  
        response = openai.File.create(
            file=open(self.training_file, "rb"),
            purpose="fine-tune"
        )
        logging.info(response)
        with open(self.output_training_file_data, "w") as file:
            json.dump(response, file)

    def update_model(self, context):  

        data=None
        with open(self.output_training_file_data, "r") as file:
            data=json.load(file)
        file_id=data["id"]
        logging.info(f"id: {file_id}")

        response = openai.FineTune.create(
            training_file=file_id,
            model=self.base_model,
            suffix=self.model_suffix
        )
    
        logging.info(response)
        with open(self.output_update_model_file, "w") as file:
            json.dump(response, file)
        print(response)
    

    #REFACTOR! Todos esos metodos deberían volar. O uso dependency injection de verdad, o le toqueto el __getattr__
    @property
    def output_update_model_file(self):
        return getattr(self, "github_object").output_update_model_file

    @property 
    def training_file(self):
        return getattr(self, "github_object").training_file

    @property
    def output_training_file_data(self):
        return getattr(self, "github_object").output_training_file_data

