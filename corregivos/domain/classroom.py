from corregivos.domain.githubObject import Github
from corregivos.utils import exec
from corregivos.domain.workers import CutChain
import os
import logging
from urllib.parse import urlparse
import subprocess
import logging
import git


class Classroom(Github):

    def __init__(self, user, token, org, assignment_name, dest_dir, students, workers):
        super().__init__(user, token)
        self.org=org
        self.assignment_name=assignment_name
        self.dir=dest_dir
        self.students=students
        self.user=user
        self.workers=workers or []
        self.logger().error(f"creando classroom para user {user} token {token} org {org} assignment:{assignment_name} dir:{dest_dir} students:{self.students} workers:{workers}" )

    def work(self):
        orga = self.api.get_organization(self.org)
        assignment_dir=os.path.join(self.dir, self.assignment_name)
        if not os.path.exists(assignment_dir):
            os.mkdir(assignment_dir)
        
        context = {orga: orga, self.assignment_name: self.assignment_name}
        for student in self.students:
            try:
                self.logger().debug(f"working with {student['identifier']}")
                reponame=f"{self.assignment_name}-{student['github_username']}"
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

                context["student"]=student
                for worker in self.workers:
                    try:
                        worker.work(local_repo,remote_repo,context)
                    except CutChain:
                        break
                    except:
                        self.logger().exception(f"Error working on {student['identifier']}")


            except:
                self.logger().exception(f"No repo for {student['github_username']} ({student['identifier']})")