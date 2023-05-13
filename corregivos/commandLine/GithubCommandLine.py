import os
from corregivos.commandLine.commandLine import CommandLine
from corregivos.types import FileOrValue, Csv, Factory
from corregivos.domain.classroom import Classroom

class GitHubCommandLine(CommandLine):
    
    
    def declare_params(self):
        super().declare_params()
        self.add_argument("--user",  help="GitHub User Name")
        self.add_argument("--token", type=FileOrValue(parentFolder=self.directory), help="GitHub Personal Access Token", default="github.token")
        self.add_argument("--org", help="GitHub Organization Name")
        self.add_argument("--students", type=FileOrValue(parentFolder=self.directory, contentType=Csv), help="an exported csv file from classroom with all students", default="classroom_roster.csv")
        self.add_argument("--workers", type=Factory, nargs="*", help="list of classes used to work with repos")
  

class ClassroomCommandLine(GitHubCommandLine):
    def declare_params(self):
        super().declare_params()
        self.add_argument("-a", "--assignment_name", required=True, help="Name of the GitHub Classroom assignment") 
    

    def _new(self):
        return Classroom(user=self.user,
                token=self.token, 
                org=self.org, 
                assignment_name=self.assignment_name, 
                dest_dir=self.dir,
                students=self.students,
                workers=self.workers)

