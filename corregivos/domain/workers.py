import logging

#class Worker
#    def work(self, local_repo, remote_repo, context):
#        raise CutChain()

class CutChain(Exception):
    pass

class DummyCommentWorker():

    def work(self, local_repo, remote_repo, context):
        print(f"ESTA LLAMANDOME PARA {local_repo} {remote_repo} {context}\n")

        pull_requests = remote_repo.get_pulls(base="feedback", head=remote_repo.default_branch)
        for x in pull_requests:
            print(f"PUUUUUUUL {x}")
        pr = next((pr for pr in pull_requests if pr.title.lower() == "feedback"), None)
        commits_list = pr.get_commits().reversed.get_page(0)
        last_commit = commits_list[-1]
        
        comments= [ {"body":"usar Polimorfisto", "path": "src/camion.wlk", "line":81}, 
                    {"body":"Esto debería ser polimórfico con ruta 9", "path":"src/caminos.wlk", "position":22}]
        
        pr.create_review(commit=last_commit, body="Este es otro comentario automático con mas comments", event="COMMENT", comments=comments)
    