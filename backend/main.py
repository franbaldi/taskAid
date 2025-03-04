from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from .utils import process_query
from .config import TWILIO_WHATSAPP_NUMBER
import os
from twilio.rest import Client

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Explicit 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return PlainTextResponse(
        status_code=404,
        content="Valid endpoint: POST /webhook/twilio",
    )

twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

@app.post("/webhook/twilio")
async def whatsapp_webhook(request: Request):
    try:
        form = await request.form()
        response = process_query(form.get("Body", ""))
        return PlainTextResponse(response, status_code=200)
    except Exception as e:
        return PlainTextResponse(str(e), status_code=500)
