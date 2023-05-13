
#class Worker
#    def work(self, local_repo, remote_repo, context):
#        raise CutChain()

class CutChain(Exception):
    pass

class DummyCommentWorker():

    def work(self, local_repo, remote_repo, context):
        print(f"ESTA LLAMANDOME PARA {local_repo} {remote_repo} {context}")
