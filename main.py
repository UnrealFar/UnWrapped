from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
import uvicorn

class App(FastAPI):
    ...

templates = Jinja2Templates(directory="templates")

app = App(
    title="UnWrapp",
    description="Get your spotify unwrapped any time of the year(You can modify it too!)",
)

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


