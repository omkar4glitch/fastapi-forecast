from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime
from prophet import Prophet
from fastapi.responses import FileResponse
import tempfile

app = FastAPI()

class ForecastRequest(BaseModel):
    file_url: str
    start_date: str
    end_date: str

def generate_forecast(file_url: str, start_date: str, end_date: str):
    try:
        # Download file from URL
        response = requests.get(file_url)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download file from URL")

        file = BytesIO(response.content)

        # Detect file type
        if file_url.lower().endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # Normalize column names (remove spaces, lowercase)
        df.columns = df.columns.str.strip().str.lower()

        # Check 'date' column
        if 'date' not in df.columns:
            raise HTTPException(status_code=400, detail="'date' column not found in file")

        # Convert 'date' column to datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        if df['date'].isnull().any():
            raise HTTPException(status_code=400, detail="Invalid date format in 'date' column")

        # Get store columns
        stores = [col for col in df.columns if col != 'date']
        if not stores:
            raise HTTPException(status_code=400, detail="No store columns found in file")

        # Prepare output date range
        output = pd.DataFrame({'date': pd.date_range(start=start_date, end=end_date)})

        # Forecast for each store column
        for store in stores:
            store_df = df[['date', store]].rename(columns={'date': 'ds', store: 'y'})
            model = Prophet()
            model.fit(store_df)

            # Number of extra days to forecast
            future_periods = (pd.to_datetime(end_date) - pd.to_datetime(df['date'].max())).days
            if future_periods < 0:
                future_periods = 0

            future = model.make_future_dataframe(periods=future_periods)
            forecast = model.predict(future)

            forecast_tail = forecast[['ds', 'yhat']].tail(len(output))
            output[store] = forecast_tail['yhat'].values

        # Save forecast to Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            output.to_excel(tmp.name, index=False)
            return tmp.name

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forecast")
def forecast(req: ForecastRequest):
    file_path = generate_forecast(req.file_url, req.start_date, req.end_date)
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename="forecast_result.xlsx"
    )
