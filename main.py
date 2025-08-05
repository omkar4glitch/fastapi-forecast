from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse

app = FastAPI()

@app.get("/")
def root():
    return {"status": "API is working!"}

@app.post("/forecast")
async def forecast(start_date: str = Form(...), end_date: str = Form(...), file: UploadFile = File(...)):
    # save and return a dummy file or actual logic
    with open("output.xlsx", "wb") as buffer:
        buffer.write(await file.read())
    return FileResponse("output.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="forecast.xlsx")
