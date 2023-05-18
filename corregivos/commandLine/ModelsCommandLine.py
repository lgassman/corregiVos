from corregivos.commandLine.commandLine import CommandLine
from corregivos.types import FileOrValue
import openai

class ModelsCommandLine(CommandLine):
    
    
    def declare_params(self):
        super().declare_params()
        self.add_argument("--openai_api_key", type=FileOrValue(parentFolder=self.directory), default="openai.api_key")


    def models(self):
        openai.api_key=self.openai_api_key
        return openai.FineTune.list()
