from fastapi import FastAPI, UploadFile, File
import spacy
import warnings
from time import time
import uvicorn
from predictions import getPredictions
import os
from io import BytesIO

warnings.filterwarnings('ignore')
app = FastAPI()
# Load NER model
# model_ner = spacy.load('./output/model-last/')
UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    start_time = time()
    # file_path = os.path.join(UPLOAD_DIR, file.filename)
    file_data = await file.read()
    file_path = BytesIO(file_data)
    # with open(file_path, "wb") as buffer:
    #     buffer.write(await file.read())
    result = getPredictions(file_path)
    end_time = time()
    return {"result": result, "execution_time": end_time - start_time}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.2", port=8000)
