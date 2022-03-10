from app import app

#from make_hipes import add_hipes_mongo
#add_hipes_mongo('list_of_hipes.txt',500,True)

app.run(
      host = "0.0.0.0", # or 127.0.0.1 (DONT USE LOCALHOST)
      port = 8080,
      debug = True
)

