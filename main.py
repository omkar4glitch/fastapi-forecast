from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from prophet import Prophet
import io
import datetime

app = FastAPI()

# Allow CORS for Adalo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your Adalo domain for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "API is working!"}

def forecast_sales(df, start_date, end_date):
    forecast_results = pd.DataFrame()
    date_range = pd.date_range(start=start_date, end=end_date)

    for column in df.columns:
        if column.lower() == 'date':
            continue

        store_df = pd.DataFrame({
            'ds': df['Date'],
            'y': df[column]
        })

        # Ensure no missing values
        store_df.dropna(inplace=True)

        # Initialize and fit model
        model = Prophet()
        model.fit(store_df)

        # Forecast future dates
        future = pd.DataFrame({'ds': date_range})
        forecast = model.predict(future)

        # Extract only required columns
        store_forecast = forecast[['ds', 'yhat']].rename(columns={'yhat': column})

        if forecast_results.empty:
            forecast_results['Date'] = store_forecast['ds']
        forecast_results[column] = store_forecast[column]

    return forecast_results

@app.post("/forecast")
async def forecast_endpoint(
    file: UploadFile = File(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))

    # Convert 'Date' to datetime
    df['Date'] = pd.to_datetime(df['Date'])

    forecast_df = forecast_sales(df, start_date, end_date)

    # Return as Excel file
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        forecast_df.to_excel(writer, index=False)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=forecast_result.xlsx"}
    )
