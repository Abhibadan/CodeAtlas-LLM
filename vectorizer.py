from dbModule.MongoDb import MongoDb
dbInstance = MongoDb()

# while True:
projects,markdowns,descriptions= dbInstance.getCollection("projects"),dbInstance.getCollection("markdowns"),dbInstance.getCollection("descriptions")

print(markdowns.find_one())
