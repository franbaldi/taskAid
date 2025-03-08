from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from .utils import process_query
from .config import TWILIO_WHATSAPP_NUMBER
import os
from twilio.rest import Client
from twilio.request_validator import RequestValidator
import logging

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class XMLResponse(Response):
    media_type = "application/xml"

    def render(self, content: str) -> bytes:
        return content.encode("utf-8")


# Explicit 404 handler
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return XMLResponse(
        content="<Response><Message>Valid endpoint: POST /webhook/twilio</Message></Response>",
        status_code=404,
    )

twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
twilio_validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))

async def validate_twilio_request(request: Request):
    form_data = await request.form()
    url = str(request.url)
    signature = request.headers.get("X-Twilio-Signature", "")
    
    return twilio_validator.validate(url, form_data, signature)




@app.post("/webhook/twilio")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    """Webhook for Twilio WhatsApp messages with detailed logging"""
    # For debugging, disable signature validation during testing
    # if not await validate_twilio_request(request):
    #     raise HTTPException(status_code=403, detail="Invalid Twilio signature")
    
    try:
        # Log the beginning of request processing
        logging.info("Received webhook request")
        
        # Get the form data
        form = await request.form()
        logging.info(f"Form data: {dict(form)}")
        
        # Extract the message body
        body = form.get("Body", "")
        from_number = form.get("From", "unknown")
        logging.info(f"Received message: '{body}' from {from_number}")
        
        # Process the query and get a response
        logging.info("Starting query processing")
        response = process_query(body)
        logging.info(f"Generated response: '{response[:100]}...'")
        
        # Ensure response is not too long for SMS/WhatsApp
        if len(response) > 1500:  # WhatsApp message length limit
            response = response[:1497] + "..."
            logging.info("Response truncated due to length")
        
        # Escape any XML special characters to prevent XML parsing issues
        response = response.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        logging.info("Response XML-escaped")
        
        # Return the XML response
        xml_content = f"<Response><Message>{response}</Message></Response>"
        logging.info(f"Returning XML response: '{xml_content[:100]}...'")
        return XMLResponse(content=xml_content)
        
    except Exception as e:
        # Log the error with detailed information
        logging.error(f"Error in webhook processing: {str(e)}", exc_info=True)
        
        # Return a clean error message to the user
        xml_content = f"<Response><Message>Sorry, I couldn't process that request. Error: {str(e)}</Message></Response>"
        return XMLResponse(content=xml_content)