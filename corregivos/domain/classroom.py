from corregivos.domain.githubObject import Github
from corregivos.utils import exec
from corregivos.domain.workers import CutChain
import os
import logging
from urllib.parse import urlparse
import subprocess
import logging
import git
import openai

class Context:
    def __init__(self, _global=None):
        self._global=_global or {}
        self._local={}
    
    def __getattr__(self, name):
        if name not in  ["_local", "_global"]:
            x = self._local.get(name) 
            if x is None :
                x = self._global.get(name)
            return x
        else: 
            return self.__dict__[name]

    def __setattr__(self, name, value):
        if name not in[ "_local" , "_global"]:
            self._local[name]=value
        else:
            self.__dict__[name]=value
    
    def set_global(self, key, value):
        self._global[key]=value
    
    def append_global(self, key, value):
        if key not in self._global:
            self._global[key] = []
        self._global[key].append(value)

    def clean(self):
        self._local={}
class Classroom(Github):

    def __init__(self, user, token, org, assignment_name, dest_dir, students, workers, action, training_file, openai_api_key, output_training_file_data, output_update_model_file, prompt_suffix, completion_suffix) :
        super().__init__(user, token)
        self.org=org
        self.assignment_name=assignment_name
        self.dir=dest_dir
        self.students=students
        self.user=user
        self.workers=workers or []
        self.action=action
        self.logger().error(f"creando classroom para user {user} token {token} org {org} assignment:{assignment_name} dir:{dest_dir} workers:{workers} action: {action}" )
        self.training_file = training_file
        self.openai_api_key=openai_api_key
        openai.api_key=self.openai_api_key       
        for worker in self.workers:
            worker.github_object=self
        self.output_training_file_data= output_training_file_data
        self.output_update_model_file=output_update_model_file
        self.prompt_suffix = prompt_suffix
        self.completion_suffix = completion_suffix


    def work(self):
        context = Context({"org": self.org, "action":self.action})
        for i in range(len(self.assignment_name)):
            context.set_global("assignment_name", self.assignment_name[i])
            context.set_global("students", self.students[i])
            try:
                self.do_work(context)
            except:
                logging.exception(f"problem working with assigment {self.assignment_name[i]}")
            self.run_action(f"end_{self.action}", context)
    
    def run_action(self, method_name, context):
        for worker in self.workers:
            try:
                if hasattr(worker, method_name):
                    getattr(worker, method_name)(context)
            except:
                logging.exception(f"problem executing {method_name} on {worker}")

    def do_work(self, context):
        orga = self.api.get_organization(context.org)
        assignment_dir=os.path.join(self.dir, context.assignment_name)
        if not os.path.exists(assignment_dir):
            os.mkdir(assignment_dir)
        
        for student in context.students:
            try:
                context.student=student
                if not student["github_username"]:
                    raise Exception(f"No github user associated to {student['identifier']}")
                if student["github_username"] == "ghost" :
                    user = self.api.get_user_by_id(int(student["github_id"]))
                    student["github_username"] = user.login

                self.logger().debug(f"working with {student['identifier']}")
                reponame=f"{context.assignment_name}-{student['github_username']}"
                self.logger().debug(f"REPONAME {reponame} orga {orga}")
                
                remote_repo =  orga.get_repo(reponame)

                url_parts = urlparse(remote_repo.clone_url)


                clone_folder_path = os.path.join(assignment_dir, student["github_username"])
                local_repo=None
                if os.path.exists(clone_folder_path) :
                    local_repo=git.Repo(clone_folder_path)
                    self.logger().debug(f"pulling {clone_folder_path}" )
                    local_repo.remotes.origin.pull()                        
                else:
                    url_with_auth = f"{url_parts.scheme}://{self.user}:{self.token}@{url_parts.netloc}{url_parts.path}"
                    git.Repo.clone_from(url_with_auth, clone_folder_path)
                    local_repo=git.Repo(clone_folder_path)

                for worker in self.workers:
                    try:
                        if hasattr(worker, self.action):
                            getattr(worker, self.action)(local_repo,remote_repo,context)
                    except CutChain:
                        break
                    except Exception as e:
                        msg = f"Error {e} working on {student['identifier']} repo:{reponame}"
                        self.logger().exception(msg)
                        context.append_global("errors", msg)

            except Exception as e:
                self.logger().exception(f" {e} problem in {context.assignment_name} working with {student['github_username']} ({student['identifier']})  ")
            finally:
                context.clean()
