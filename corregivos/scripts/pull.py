import os
import sys
import yaml
from corregivos.commandLine.GithubCommandLine import ClassroomCommandLine
from corregivos.domain.classroom import Classroom

if __name__ == "__main__":
    c = ClassroomCommandLine()
    classroom=c.make()
    classroom.pull(c.just_clone)

