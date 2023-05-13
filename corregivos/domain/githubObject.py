from github import Github as GitHubApi
import logging

class Github():

    def __init__(self, user, token):
        self.token=token
        self.user=user
        self.api = GitHubApi(self.user, self.token)
    
    def logger(self):
        return logging.getLogger(self.__class__.__name__)

