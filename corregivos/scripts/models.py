import os
import sys
import yaml
from corregivos.commandLine.ModelsCommandLine import ModelsCommandLine


if __name__ == "__main__":
    print(ModelsCommandLine().make().models())
