from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


class App(FastAPI):
    ...



app = App(
    title="UnWrapp",
    description="Get your spotify unwrapped any time of the year(You can modify it too!)",
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


