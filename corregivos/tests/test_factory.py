import logging
from corregivos.commandLine.commandLine import CommandLine
from corregivos.types import Factory, FileOrValue
import os
import sys
import traceback
import json

class InnerClass:
    def __init__(self, value1="hola", value2="mundo"):
        self.value1=value1
        self.value2=value2

class CommandLineForTest(CommandLine):
        def declare_params(self):
            super().declare_params()
            self.add_argument("--aStringFromParam")
            self.add_argument("--aConfiguratedString")
            self.add_argument("--aConfiguratedInt",  type=int)
            self.add_argument("--aStringWithDefault", default="myDefaultValue")
            self.add_argument("--aStringFromFile", type=FileOrValue(parentFolder=self.directory), default="aTestFile")
            self.add_argument("--aListOfObject", type=Factory(self), nargs="*", help="")


def test_factory(): 
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_args = ['--dir', current_dir, '--config', 'config-for-test.yaml', '--aStringFromParam', 'myStringValueFromParam']
    original_argv = sys.argv

    try:
        # Establecer los argumentos de línea de comandos simulados
        sys.argv = [original_argv[0]] + test_args

        commandLine = CommandLineForTest()
        args = commandLine.make()

        # Comprobar que los atributos de los argumentos coincidan
        assert args.aStringFromParam == 'myStringValueFromParam'
        assert args.aConfiguratedString == 'MyConfiguratedStringValue'
        assert args.aConfiguratedInt == 13
        assert args.aStringWithDefault == "myDefaultValue"
        assert args.aStringFromFile == "My Test File Content"
        assert len(args.aListOfObject) == 6

        assert isinstance(args.aListOfObject[0], InnerClass) 
        assert args.aListOfObject[0].value1 == "hola"
        assert args.aListOfObject[0].value2 == "mundo"

        assert isinstance(args.aListOfObject[1], InnerClass) 
        assert args.aListOfObject[1].value1 == "argValue1"
        assert args.aListOfObject[1].value2 == "argValue2"

        assert isinstance(args.aListOfObject[2], InnerClass) 
        assert args.aListOfObject[2].value1 == "kargValue1"
        assert args.aListOfObject[2].value2 == "kargValue2"

        assert isinstance(args.aListOfObject[3], InnerClass) 
        assert args.aListOfObject[3].value1 == "MyConfiguratedStringValue"
        assert args.aListOfObject[3].value2 == "$aConfiguratedString"

        assert isinstance(args.aListOfObject[4], InnerClass) 
        assert args.aListOfObject[4].value1 == "myStringValueFromParam"
        assert args.aListOfObject[4].value2 == "mundo"

        assert isinstance(args.aListOfObject[5], InnerClass) 
        assert args.aListOfObject[5].value1 == "$aStringFromParam"
        assert args.aListOfObject[5].value2 == "myStringValueFromParam"

    except Exception as err:
        print(err)
        traceback.print_exc()
        logging.exception(f"{err}")
        raise 
    finally:
        # Restaurar el estado original de sys.argv
        sys.argv = original_argv    
    
  