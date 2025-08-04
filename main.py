from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from datetime import datetime
import pandas as pd
from io import BytesIO
from prophet import Prophet

app = FastAPI()

@app.get("/")
def home():
    return {"status": "API is working!"}

@app.post("/forecast")
async def forecast_sales(
    file: UploadFile = File(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    # Read uploaded Excel file
    contents = await file.read()
    df = pd.read_excel(BytesIO(contents))

    # Make sure columns are as expected
    if df.columns[0].lower() != "date":
        return {"error": "First column must be 'Date'"}

    df['Date'] = pd.to_datetime(df['Date'])

    # Prepare output DataFrame
    result_df = pd.DataFrame()

    for col in df.columns[1:]:
        temp_df = df[['Date', col]].rename(columns={"Date": "ds", col: "y"}).dropna()

        m = Prophet()
        m.fit(temp_df)

        future = m.make_future_dataframe(periods=(pd.to_datetime(end_date) - df['Date'].max()).days)
        forecast = m.predict(future)

        forecast_trimmed = forecast[['ds', 'yhat']].rename(columns={'yhat': col})

        if result_df.empty:
            result_df['Date'] = forecast_trimmed['ds']
        result_df[col] = forecast_trimmed[col]

    # Filter forecasted date range
    result_df = result_df[(result_df['Date'] >= pd.to_datetime(start_date)) & (result_df['Date'] <= pd.to_datetime(end_date))]

    # Convert to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        result_df.to_excel(writer, index=False)
    output.seek(0)

    return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=forecast.xlsx"})
