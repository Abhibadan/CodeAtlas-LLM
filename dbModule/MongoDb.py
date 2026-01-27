import pymongo

from config import config

class MongoDb:
    __instance = None
    def __new__(cls,*args,**kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.client = pymongo.MongoClient(config["MONGO_URI"])
        self.db = self.client[config["MONGO_DB"]]
    
    def getCollection(self,collection_name):
        return self.db[collection_name]