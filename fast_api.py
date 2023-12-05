from fastapi import FastAPI, UploadFile, File
import warnings
from time import time
import uvicorn
from predictions import getPredictions
import os
from io import BytesIO
from starlette.responses import RedirectResponse
warnings.filterwarnings('ignore')
app_desc = """<h2>Giấy chứng nhận đủ điều kiện an toàn thực phẩm - Cấp huyện</h2>"""
app = FastAPI(title="Tensorflow FastAPI Start Pack", description=app_desc)
@app.get("/", include_in_schema=False)
async def index():
    return RedirectResponse(url="/docs")
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    start_time = time()
    file_data = await file.read()
    file_path = BytesIO(file_data)
    result = getPredictions(file_path)
    end_time = time()
    return {"result": result, "execution_time": end_time - start_time}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.2", port=8000)
