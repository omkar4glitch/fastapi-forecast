from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import requests
from io import BytesIO
from prophet import Prophet
from openpyxl import load_workbook
from openpyxl.styles import numbers
from fastapi.responses import StreamingResponse

app = FastAPI()

class ForecastRequest(BaseModel):
    file_url: str
    forecast_start: str
    forecast_end: str

@app.post("/forecast")
def forecast_sales(req: ForecastRequest):
    # Download file
    r = requests.get(req.file_url)
    df = pd.read_excel(BytesIO(r.content))

    # First column is date
    df.rename(columns={df.columns[0]: "ds"}, inplace=True)
    df["ds"] = pd.to_datetime(df["ds"])

    # Forecast for each store column
    forecast_results = pd.DataFrame()
    forecast_results["ds"] = pd.date_range(req.forecast_start, req.forecast_end)

    for store in df.columns[1:]:
        m = Prophet()
        temp_df = df[["ds", store]].rename(columns={store: "y"})
        m.fit(temp_df)
        future = pd.DataFrame({"ds": pd.date_range(req.forecast_start, req.forecast_end)})
        forecast = m.predict(future)
        forecast_results[store] = forecast["yhat"].round(0)  # No decimals

    # Save to Excel
    output = BytesIO()
    forecast_results.to_excel(output, index=False)
    output.seek(0)

    # Format Excel
    wb = load_workbook(output)
    ws = wb.active

    # Date format (short date)
    for row in ws.iter_rows(min_row=2, max_col=1):
        for cell in row:
            cell.number_format = "yyyy-mm-dd"

    # Comma style, no decimals
    for row in ws.iter_rows(min_row=2, min_col=2, max_col=ws.max_column):
        for cell in row:
            cell.number_format = "#,##0"

    output2 = BytesIO()
    wb.save(output2)
    output2.seek(0)

    return StreamingResponse(output2, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                              headers={"Content-Disposition": "attachment; filename=forecast.xlsx"})
