from fastapi import FastAPI, Form
from pydantic import HttpUrl
from typing import Annotated
import pandas as pd
from prophet import Prophet
from io import BytesIO
from fastapi.responses import StreamingResponse
import requests

app = FastAPI()

@app.post("/forecast")
async def forecast(
    file: Annotated[HttpUrl, Form()],
    start_date: Annotated[str, Form()],
    end_date: Annotated[str, Form()]
):
    try:
        # Download the Excel file from the given URL
        response = requests.get(str(file))
        df = pd.read_excel(BytesIO(response.content))

        # Ensure the first column is date
        df.columns = [str(c).strip() for c in df.columns]
        df.rename(columns={df.columns[0]: "ds"}, inplace=True)
        df["ds"] = pd.to_datetime(df["ds"])

        # Prepare to collect all forecasted results
        output_df = pd.DataFrame({"ds": pd.date_range(start=start_date, end=end_date)})

        # Loop through each store column (skip 'ds')
        for col in df.columns[1:]:
            store_df = df[["ds", col]].rename(columns={col: "y"}).dropna()

            if len(store_df) < 2:
                # Skip if insufficient data for forecasting
                continue

            model = Prophet()
            model.fit(store_df)

            future = pd.DataFrame({"ds": output_df["ds"]})
            forecast = model.predict(future)

            # Add forecast to output DataFrame
            output_df[col + "_forecast"] = forecast["yhat"]

        # Write results to an Excel file in memory
        output_stream = BytesIO()
        output_df.to_excel(output_stream, index=False)
        output_stream.seek(0)

        # Return downloadable Excel file
        return StreamingResponse(output_stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=forecast_result.xlsx"})

    except Exception as e:
        return {"error": str(e)}
