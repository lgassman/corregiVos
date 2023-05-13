from corregivos.domain.githubObject import Github
from corregivos.utils import exec
import os
import logging
from urllib.parse import urlparse
import subprocess
import logging
import git

class Classroom(Github):

    def __init__(self, user, token, org, assignment_name, dest_dir, students):
        super().__init__(user, token)
        self.org=org
        self.assignment_name=assignment_name
        self.dir=dest_dir
        self.students=students
        self.user=user
        self.logger().error(f"creando classroom para user {user} token {token} org {org} assignment:{assignment_name} dir:{dest_dir} students:{self.students}" )

    def pull(self, just_clone=False):
        "clone and pull"
        orga = self.api.get_organization(self.org)
        assignment_dir=os.path.join(self.dir, self.assignment_name)
        if not os.path.exists(assignment_dir):
            os.mkdir(assignment_dir)
        for student in self.students:
            try:
                self.logger().debug(f"working with {student['identifier']}")
                reponame=f"{self.assignment_name}-{student['github_username']}"
                repo =  orga.get_repo(reponame)

                url_parts = urlparse(repo.clone_url)


                clone_folder_path = os.path.join(assignment_dir, student["github_username"])
                if os.path.exists(clone_folder_path) :
                    if just_clone:
                        self.logger().debug(f"{student['github_username']} already cloned ({student['identifier']})")
                        return
                    else:
                        local_repo=git.Repo(clone_folder_path)
                        self.logger().debug(f"pulling {clone_folder_path}" )
                        local_repo.remotes.origin.pull()
                        
                else:
                    url_with_auth = f"{url_parts.scheme}://{self.user}:{self.token}@{url_parts.netloc}{url_parts.path}"
#                    exec(f"git clone {url_with_auth} {clone_folder_path}")
                    git.Repo.clone_from(url_with_auth, clone_folder_path)

            except:
                self.logger().exception(f"No repo for {student['github_username']} ({student['identifier']})")
