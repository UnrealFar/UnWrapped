from fastapi import FastAPI
import uvicorn

class App(FastAPI):
    ...

app = App(
    title="UnWrapp",
    description="Get your spotify unwrapped any time of the year(You can modify it too!)"
)

@app.get("/")
def root():
    return {"message": "Hello World"}

uvicorn.run(app, host="0.0.0.0", port=1602)
