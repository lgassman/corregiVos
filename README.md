# Corregí Vos

Este proyecto (con nombre en construcción) es para realizar correcciones masivas de assigments de github classroom.
Actualmente posee una integración con openai para realizar corrección automática. Pero es es un pryecto que sirve
como base para realizar más tareas sobre los repositorios de los/las estudiantes

Está desarrollado en python y funciona por línea de comandos. Se le indica el assigment y el roost de estudiantes
(ambas cosas se obtienen de github classroom) y el resultado es una serie de comentarios en el PullRequest de feedback

# Dependencias

[requerimients.txt](requirements.txt)

```plaintext
```bash
$(cat requirements.txt)
```
```
# Configuración y ejecución

Se puede correr como script python o instalar el módulo con pip

## Instalación 
``` 
#instalar las dependencias
    pip install -r requirements.txt
#crear el directorio de trabajo
    mkdir ~/work_here 
#copiar un template de configuración
    cp config.yaml ~/work_here
#poner el token de github en donde está configurado por default
    printf "my_github_token" >> ~/work_here/github.token
#poner el token de openai en donde está configurado por default
    printf "my_open_ai_key" >> ~/work_here/openai.api_key
#descargar de classrrom el archivo classroom_roster.csv y copiarlo al directorio de trabajo    
    cp ~/downloads/classroom_roster.csv ~/work_here
   
```
## Editar el archivo de configuración
Las siguientes entradas de ~/work_here/config.yaml son importantes de configurar:

```
#Puede ser más de uno, por eso es una lista. Lo normal es que sea uno
assignment_name: [my_assignment_name] 
orga: my_classroom_orga
user: my_github_user
```
### Editar para training

Si se quiere armar el training set también configurar:

```
    #Usar tantos assigments como se quiera
    assignment_name: [my_assignment_name_last_semester, my_assignment_name_other_semester]  
    students: [last_semeter_classroom_rooster.csv, other_semester_classroom_rooster.csv]
    action: train
    #La lista de teachers es usada para filtrar los comentarios relevantes
    teachers: [teacher1_github_login_name, teacher2_github_login_name,]
```
## Otras configuraciones

Todos los parámetros de openai y nombres de archivos se pueden configurar en el archivo de configuración. Figuran en el template
Adicionalmente casi todos los parámetros pueden ser sobrescritos por línea de comando. el lookup de un parámetro eso:
1. Primero se fija si se pasó por parámetro en la línea de comando
2. Se fija si existe en la configuraicón
3. Usa el valor por default que figura en el help 


# Uso:

```
    #help:
    python3 corregivos/scripts/grade.py --help

    #run
    python3 corregivos/scripts/grade.py --dir ~/work_here

```

Todos los parámetros que se refieren a archivos para ir a buscar información pueden recibir tanto la ruta (absoluta o relativa al directorio
de trabajo) como el contenido mismo. Por ejemplo, no es necesario tener archivos con los tokens de github y openai, ya que se puede
usar los parámetros para enviar directmante los valores por línea de comando por ejemplo:

```
    #run
    python3 corregivos/scripts/grade.py --dir ~/work_here --openai_api_key "<esta es mi key>"

```

Si el archivo de configuración el action es **grade**, entonces el resultado se va a ver en los PullRequests de los repos del assigment
Mientras que si el action es **train** el resultado es un archivo llamado (por default) `training.jsonl`

# Arquitectura

## Línea de comando
    
Las clases `CommandLine` permiten definir parámetros que se buscan con el lookup descripto anteriormente. Para eso deben implementar
el método `declare_params(self)` haciendo uso del método `add_argument` que se usa de la misma manera que el `argument_parser` estandard

Además Un CommandLine puede sobreescrir el método _build() para construir un objeto de dominio. Si no lo hace él mismo es considerado
el objeto de dominio.

Todos los parámetros definidos terminan siendo atributos del objeto CommandLine. 

El objeto CommandLine es ejecutado desde un script. Se le pide que genere el objeto de dominio y luego se invoca a
algún método de dicho objeto.

Ejemplo:
- [GithubCommandLine](corregivos/commandLine/GithubCommandLine.py)
- [grade.py](corregivos/scripts/grade.py)

## Workers

Tanto las acciones **grade** como **train** se resuelve de la siguiente manera:
1. Se realiza un clone (o un pull si ya estaba clonado) de cada repositorio del assigment
2. Se invoca a una __chain of responsability__ de objetos workers por cada estudiante. 
3. Se invoca por única vez para cada worker el método de fin

Cada worker puede elegir si participa en el grade y/o train. Para lo cual debe implementar estos métodos según lo desee
```
    def grade(self, local_repo, remote_repo, context):

    def train(self, local_repo, remote_repo, context):

    def end_grade(self, context):

    def end_train(self, context):

```

Si en el método grade o train ocurre una excepción de tipo corregivos.workers.CutChain la cadena se corta y se pasa al siguiente estudiante.

Cualquier otro error cancela la operación completa

Los workers dejan información en el contexto que puede ser usada por el siguiente worker. Existen dos niveles de información:
    - global: Lo que se pone ahí queda para todo el proceso. Se setea con el método `set_global(self, key, value)`
    - local: Lo que se pone aquí es limpiado al iniciar el proceso para cada estudiante (repo).  Se seta simplemente
    como atributos del objeto context

Cuando se le pide al contecto por un atributo, lo busca local y si no lo encuentra usa el global

Al inicio de cada proceso se setea en el contexto el objeto "student" que es el asociado a los repos `local_repo`y `remote_repo` que figura en el classroom_rooster.csv

También están de manera global el `assigment_name` y la `orga`

Antes de comenzar el proceso, a los workers se le setea el atributo `github_object` con una referencia al objeto "Classroom" que es
el objeto de dominio creado por línea de comando




    

