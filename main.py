from fastapi import FastAPI, Query
import pandas as pd
import joblib
import os
import uuid
import requests
from io import BytesIO
from fastapi.responses import FileResponse

app = FastAPI()

# Folder to store temporary files
FILES_DIR = "files"
os.makedirs(FILES_DIR, exist_ok=True)

@app.get("/forecast")
def forecast(file_url: str = Query(..., description="Public file URL")):
    try:
        # 1. Download file from public URL
        response = requests.get(file_url)
        response.raise_for_status()

        # 2. Read Excel or CSV
        try:
            df = pd.read_excel(BytesIO(response.content))
        except:
            df = pd.read_csv(BytesIO(response.content))

        # 3. Forecast logic (dummy example — replace with your model)
        # For now, let's just add a column 'Forecast' as a copy
        df["Forecast"] = df.iloc[:, 1]  # Copy second column as dummy forecast

        # 4. Save output as Excel
        output_filename = f"forecast_{uuid.uuid4().hex}.xlsx"
        output_path = os.path.join(FILES_DIR, output_filename)
        df.to_excel(output_path, index=False)

        # 5. Return public link to file
        download_url = f"https://{os.environ.get('RAILWAY_STATIC_URL', 'web-production-df285.up.railway.app')}/files/{output_filename}"

        return {
            "message": "Forecast complete",
            "download_url": download_url
        }

    except Exception as e:
        return {"error": str(e)}

# Serve files
@app.get("/files/{filename}")
def get_file(filename: str):
    file_path = os.path.join(FILES_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, filename=filename)
    return {"error": "File not found"}
