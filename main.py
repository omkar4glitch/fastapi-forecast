from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from typing import Optional
from forecast import generate_forecast  # your forecasting logic

app = FastAPI()

# ✅ Define the expected JSON body using Pydantic
class ForecastRequest(BaseModel):
    file_url: HttpUrl
    start_date: str
    end_date: str

@app.post("/forecast")
async def forecast(request: ForecastRequest):
    try:
        # Call your forecast logic
        output_file = generate_forecast(
            file_url=request.file_url,
            start_date=request.start_date,
            end_date=request.end_date
        )
        return {
            "status": "success",
            "download_url": output_file  # or return as StreamingResponse if needed
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
