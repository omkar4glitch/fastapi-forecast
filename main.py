from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse
from prophet import Prophet
import pandas as pd
import requests
from io import BytesIO
from datetime import datetime

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Forecast API is running."}

@app.post("/forecast")
async def forecast_from_url(
    file_url: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    try:
        # Download the file from URL
        response = requests.get(file_url)
        response.raise_for_status()
        file_content = BytesIO(response.content)
    except Exception as e:
        return {"error": f"Failed to download or read the file: {str(e)}"}

    try:
        df = pd.read_excel(file_content)
        stores = df.columns[1:]  # all columns except date
        date_col = df.columns[0]
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
    except Exception as e:
        return {"error": f"Invalid Excel format or dates: {str(e)}"}

    forecasts = []

    for store in stores:
        store_df = pd.DataFrame({
            "ds": pd.to_datetime(df[date_col]),
            "y": df[store]
        }).dropna()

        if store_df.empty:
            continue

        model = Prophet()
        model.fit(store_df)

        periods = (end - store_df['ds'].max()).days
        if periods <= 0:
            continue

        future = model.make_future_dataframe(periods=periods)
        future = future[future['ds'] >= start]

        forecast = model.predict(future)[["ds", "yhat"]]
        forecast.columns = ["Date", store]
        forecasts.append(forecast.set_index("Date"))

    if not forecasts:
        return {"error": "No valid store data found for forecasting."}

    final_df = pd.concat(forecasts, axis=1).reset_index()

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        final_df.to_excel(writer, index=False, sheet_name="Forecast")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=forecast.xlsx"}
    )
