from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pandas as pd
from io import BytesIO

app = FastAPI()

class FileURL(BaseModel):
    file_url: str

@app.post("/forecast")
async def forecast_from_url(data: FileURL):
    # Download file
    response = requests.get(data.file_url)
    response.raise_for_status()
    
    # Load into pandas
    df = pd.read_excel(BytesIO(response.content))
    
    # Process your forecast logic here
    forecast_df = df  # placeholder
    
    # Save result to bytes
    output_bytes = BytesIO()
    forecast_df.to_excel(output_bytes, index=False)
    output_bytes.seek(0)

    return {"message": "Forecast complete", "rows": len(forecast_df)}
