from corregivos.domain.githubObject import Github
from corregivos.utils import exec
from corregivos.domain.workers import CutChain
import os
import logging
from urllib.parse import urlparse
import subprocess
import logging
import git

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

    def __init__(self, user, token, org, assignment_name, dest_dir, students, workers, action):
        super().__init__(user, token)
        self.org=org
        self.assignment_name=assignment_name
        self.dir=dest_dir
        self.students=students
        self.user=user
        self.workers=workers or []
        self.action=action
        self.logger().error(f"creando classroom para user {user} token {token} org {org} assignment:{assignment_name} dir:{dest_dir} students:{self.students} workers:{workers} action: {action}" )

    def work(self):
        context = Context({"org": self.org, "action":self.action})
        for i in range(len(self.assignment_name)):
            context.set_global("assignment_name", self.assignment_name[i])
            context.set_global("students", self.students[i])
            try:
                self.do_work(context)
            except:
                logging.exception(f"problem working with assigment {self.assignment_name[i]}")
        self.end(context)
    
    def end(self, context):
        for worker in self.workers:
            try:
                worker.end(context)
            except:
                logging.exception(f"problem ending {worker}")

    def do_work(self, context):
        orga = self.api.get_organization(context.org)
        assignment_dir=os.path.join(self.dir, context.assignment_name)
        if not os.path.exists(assignment_dir):
            os.mkdir(assignment_dir)
        
        for student in context.students:
            try:
                context.student=student
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
                        getattr(worker, self.action)(local_repo,remote_repo,context)
                    except CutChain:
                        break
                    except Exception as e:
                        self.logger().exception(f"Error {e} working on {student['identifier']} ")

            except:
                self.logger().exception(f"No repo for {student['github_username']} ({student['identifier']})")
            finally:
                context.clean()
