from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import numpy as np
from prophet import Prophet
import os
from fastapi.responses import FileResponse
import uuid

app = FastAPI()

# Create a directory to store files temporarily
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

class ForecastRequest(BaseModel):
    file_url: str
    start_date: str
    end_date: str

@app.post("/forecast")
async def forecast(request: ForecastRequest):
    try:
        # Step 1: Download the file
        df = pd.read_excel(request.file_url) if request.file_url.endswith(".xlsx") else pd.read_csv(request.file_url)

        # Step 2: Standardize 'Date' column (case-insensitive)
        date_col = next((col for col in df.columns if col.lower() == "date"), None)
        if not date_col:
            raise HTTPException(status_code=400, detail="Missing 'Date' column in file")
        df.rename(columns={date_col: "ds"}, inplace=True)

        # Step 3: Forecast each store column
        results = pd.DataFrame({"ds": pd.date_range(start=request.start_date, end=request.end_date)})
        for col in df.columns:
            if col == "ds":
                continue
            store_df = df[["ds", col]].rename(columns={col: "y"})
            store_df.dropna(inplace=True)

            model = Prophet()
            model.fit(store_df)
            future = pd.DataFrame({"ds": pd.date_range(start=request.start_date, end=request.end_date)})
            forecast = model.predict(future)
            results[col] = forecast["yhat"].round(2)

        # Step 4: Save the forecast to Excel
        file_name = f"forecast_{uuid.uuid4().hex}.xlsx"
        file_path = os.path.join(FILES_DIR, file_name)
        results.to_excel(file_path, index=False)

        # Step 5: Return a download link
        base_url = "https://web-production-df285.up.railway.app"
        download_link = f"{base_url}/files/{file_name}"
        return {"download_link": download_link}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Static file serving for the files directory
from fastapi.staticfiles import StaticFiles
app.mount("/files", StaticFiles(directory=FILES_DIR), name="files")
