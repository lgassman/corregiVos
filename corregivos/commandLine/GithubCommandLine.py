import os
from corregivos.commandLine.commandLine import CommandLine, FileOrValue, Set
from corregivos.lib.classroom import Classroom

class GitHubCommandLine(CommandLine):
    
    
    def _add_args(self):
        super()._add_args()
        self.add_argument("--token", type=FileOrValue(), help="GitHub Personal Access Token", default="github.token")
        self.add_argument("--org", help="GitHub Organization Name")
  

class ClassroomCommandLine(GitHubCommandLine):
    def _add_args(self):
        super()._add_args()
        self.add_argument("--assignment_name", required=True, help="Name of the GitHub Classroom assignment") 

    def _new(self, args):
        return Classroom(token=self.token, 
                org=self.org, 
                assignment_name=self.assignment_name, 
                dest_dir=self.dir)

