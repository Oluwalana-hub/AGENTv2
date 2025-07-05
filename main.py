from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import openai
import os
import uuid
from dotenv import load_dotenv
from weasyprint import HTML
import requests


# Load environment variables from .env
load_dotenv()

# Initialize FastAPI app
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def validate_license(license_key):
    response = requests.post(GUMROAD_API_URL, data={
        "product_id": GUMROAD_PRODUCT_ID,
        "license_key": license_key
    })
    return response.json()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})

@app.post("/generate", response_class=HTMLResponse)
async def generate(
        request: Request,
        niche: str = Form(...),
        offer: str = Form(...),
        license_key: str = Form(...),
):
    license_data = validate_license(license_key)
    if not license_data("success"):
        return templates.TemplateResponse("form.html", {
            "request": request,
            "error": "Invalid or expired license key."
            })
    prompt = f"""
    You are a cold email strategist. Given the niche: '{niche}' and the offer: '{offer}', create:
    - A 3-part cold email sequence
    - 5 subject lines
    - A LinkedIn message version

    Make the emails persuasive, short, and use a Hook → Pain → Value → CTA structure.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a cold email strategist."},
                {"role": "user", "content": prompt}
            ]
        )
        content = response['choices'][0]['message']['content']
    except Exception as e:
        content = f"Error: {str(e)}"

    return templates.TemplateResponse("result.html", {
        "request": request,
        "niche": niche,
        "offer": offer,
        "content": content
    })

@app.post("/download-pdf")
async def download_pdf(request: Request, content: str = Form(...), niche: str = Form(...), offer: str = Form(...)):
    html_content = templates.get_template("pdf_template.html").render({
        "niche": niche,
        "offer": offer,
        "content": content
    })
    filename = f"static/{uuid.uuid4()}.pdf"
    HTML(string=html_content).write_pdf(target=filename)
    return FileResponse(path=filename, filename="cold_outreach_campaign.pdf", media_type="application/pdf")
