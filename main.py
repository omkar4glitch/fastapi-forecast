from fastapi import FastAPI, Form
from pydantic import BaseModel
import pandas as pd
import uuid
import os
import requests

app = FastAPI()

class ForecastResponse(BaseModel):
    download_link: str

@app.post("/forecast", response_model=ForecastResponse)
async def forecast(
    file_url: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    # 1️⃣ Download the uploaded file from Adalo
    response = requests.get(file_url)
    temp_filename = f"temp_{uuid.uuid4()}.xlsx"
    with open(temp_filename, "wb") as f:
        f.write(response.content)

    # 2️⃣ Read and process the file (replace with your forecasting code)
    df = pd.read_excel(temp_filename)
    # Example dummy processing: just save the same file as output
    output_filename = f"forecast_{uuid.uuid4()}.xlsx"
    df.to_excel(output_filename, index=False)

    # 3️⃣ Delete the original temp file
    os.remove(temp_filename)

    # 4️⃣ Return download link (Adalo will see `download_link` now)
    download_link = f"https://web-production-df285.up.railway.app/{output_filename}"
    return ForecastResponse(download_link=download_link)

# 5️⃣ Serve the generated files
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="."), name="static")
