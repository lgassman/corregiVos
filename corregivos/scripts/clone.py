import os
import sys
import yaml
from corregivos.commandLine.GithubCommandLine import ClassroomCommandLine
from corregivos.lib.classroom import Classroom

if __name__ == "__main__":
    c = ClassroomCommandLine()
    c=c.make()
    c.clone_all_repos()

