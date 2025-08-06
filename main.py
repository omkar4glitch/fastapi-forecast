from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime, timedelta
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
        df = pd.read_excel(file)

        # Convert 'date' column to datetime
        df['date'] = pd.to_datetime(df['date'])

        # Forecast for each store column (excluding 'date')
        stores = [col for col in df.columns if col != 'date']
        output = pd.DataFrame({'date': pd.date_range(start=start_date, end=end_date)})

        for store in stores:
            store_df = df[['date', store]].rename(columns={'date': 'ds', store: 'y'})
            model = Prophet()
            model.fit(store_df)

            future = model.make_future_dataframe(periods=(pd.to_datetime(end_date) - pd.to_datetime(df['date'].max())).days)
            forecast = model.predict(future)
            forecast = forecast[['ds', 'yhat']].tail(len(output))
            output[store] = forecast['yhat'].values

        # Save forecast to Excel
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            output.to_excel(tmp.name, index=False)
            return tmp.name

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/forecast")
def forecast(req: ForecastRequest):
    file_path = generate_forecast(req.file_url, req.start_date, req.end_date)
    return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="forecast_result.xlsx")
