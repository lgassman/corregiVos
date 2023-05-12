import os
from corregivos.commandLine.commandLine import CommandLine, FileOrValue, Set
from corregivos.lib.classroom import Classroom

class GitHubCommandLine(CommandLine):
    
    
    def _add_args(self):
        super()._add_args()
        self.arg_parser.add_argument("--token", action=Set, type=FileOrValue(), holder=self, help="GitHub Personal Access Token", default="github.token")
        self.arg_parser.add_argument("--org", action=Set, holder=self, help="GitHub Organization Name")
  

class ClassroomCommandLine(GitHubCommandLine):
    def _add_args(self):
        super()._add_args()
        self.arg_parser.add_argument("--assignment_name", action=Set, holder=self, required=True, help="Name of the GitHub Classroom assignment") 

    def _new(self, args):
        return Classroom(token=self.token, 
                org=self.org, 
                assignment_name=self.assignment_name, 
                dest_dir=self.dir)

