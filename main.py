from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
import os
import uuid
from dotenv import load_dotenv
from weasyprint import HTML

# Load environment variables
load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Configure OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
if not client :
    raise ValueError("No OPENAI_API_KEY found in environment variables")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("form.html", {"request": request})


@app.post("/generate", response_class=HTMLResponse)
async def generate(
        request: Request,
        niche: str = Form(...),
        offer: str = Form(...)
):
    try:
        # Validate inputs
        if not niche.strip() or not offer.strip():
            raise HTTPException(status_code=400, detail="Niche and offer cannot be empty")

        prompt = f"""
        Create a cold outreach campaign for:
        Niche: {niche}
        Offer: {offer}

        Include:
        1. 3 email sequence (Hook → Pain → Value → CTA)
        2. 5 subject line options
        3. LinkedIn message version
        """

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Changed to more accessible model
            messages=[
                {"role": "system", "content": "You are a cold email expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )

        content = response.choices[0].message.content

        return templates.TemplateResponse("result.html", {
            "request": request,
            "niche": niche,
            "offer": offer,
            "content": content
        })

    except Exception as e:
        print(f"Error: {str(e)}")
        return templates.TemplateResponse("form.html", {
            "request": request,
            "error": f"Failed to generate content: {str(e)}",
            "niche": niche,
            "offer": offer
        })


@app.post("/download-pdf")
async def download_pdf(
        content: str = Form(...),
        niche: str = Form(...),
        offer: str = Form(...)
):
    try:
        html_content = templates.get_template("pdf_template.html").render({
            "niche": niche,
            "offer": offer,
            "content": content
        })

        # Ensure static directory exists
        os.makedirs("static", exist_ok=True)

        filename = f"static/{uuid.uuid4()}.pdf"
        HTML(string=html_content).write_pdf(filename)

        return FileResponse(
            filename,
            filename="cold_outreach_campaign.pdf",
            media_type="application/pdf"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")