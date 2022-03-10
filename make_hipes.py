import pymongo
import os

def get_db():
  client = pymongo.MongoClient(os.environ.get('MONGO_DB_STRING'))
  database = client.hipegame
  return database
  
def add_hipes_mongo(filename,num_to_load = 10000,delete_first=False):
  database = get_db()
  if delete_first: 
    database.hipes.delete_many({})
  print('populating list of HIPEs from the file')
  i = 0
  with open(filename,'r') as f:
    for line in f:
      i+=1
      line = line.strip().split(',')
      letters = line[0]
      answers = line[1:]
      
      database.hipes.insert_one({'letters':letters,'answers':answers})
      if i > num_to_load:
        break


