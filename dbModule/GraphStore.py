from neo4j import GraphDatabase

class GraphStore:
    __instance = None
    def __new__(cls,*args,**kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance
    
    def __init__(self,uri,user,password,database):
        if self._initialized:
            return
        self._initialized = True
        self.driver = GraphDatabase.driver(uri,auth=(user,password))
        self.database = database
        self._schema_cache = None

    def close(self):
        self.driver.close()
    
    