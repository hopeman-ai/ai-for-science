import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ai_for_science.api.routes import router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class UTF8JSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, ensure_ascii=False).encode("utf-8")


app = FastAPI(
    title="AI for Science 국가 전략",
    description="국가별 AI for Science 전략 비교 분석 및 시사점",
    version="2.0.0",
    default_response_class=UTF8JSONResponse,
)

app.include_router(router, prefix="/api")

app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}
