import os
from corregivos.commandLine.commandLine import CommandLine, FileOrValue, Set, Csv
from corregivos.domain.classroom import Classroom

class GitHubCommandLine(CommandLine):
    
    
    def _add_args(self):
        super()._add_args()
        self.add_argument("--user",  help="GitHub Personal Access Token")
        self.add_argument("--token", type=FileOrValue(), help="GitHub Personal Access Token", default="github.token")
        self.add_argument("--org", help="GitHub Organization Name")
        self.add_argument("--students", type=FileOrValue(contentType=Csv), help="csv file", default="classroom_roster.csv")
        self.add_argument("--just_clone", help="if present only clone, else pull if folder exists", default=False)
  

class ClassroomCommandLine(GitHubCommandLine):
    def _add_args(self):
        super()._add_args()
        self.add_argument("--assignment_name", required=True, help="Name of the GitHub Classroom assignment") 

    def _new(self, args):
        return Classroom(user=self.user,
                token=self.token, 
                org=self.org, 
                assignment_name=self.assignment_name, 
                dest_dir=self.dir,
                students=self.students)

