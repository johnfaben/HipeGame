from app import app

'''app.run(
      host = "0.0.0.0", # or 127.0.0.1 (DONT USE LO#CALHOST)
      port = 8080,
      debug = True
)'''

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)