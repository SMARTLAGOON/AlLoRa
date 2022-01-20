'''
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from fastapi import status
import os

class BuoyFile(BaseModel):
    content: str

try:
    os.mkdir('received')
except Exception as e:
    #If folder already exists...
    print(e)

app = FastAPI()

@app.get("/")
def ping_root():
    return {"PING": "PONG"}

@app.post("/source/{source_address}/{filename}")
def save_file(source_address: str, filename: str, buoyfile: BuoyFile):
    global i
    print(source_address, filename, buoyfile)
    try:
        os.mkdir('received/{}'.format(source_address))
        print('created folder')
    except Exception as e:
        #If folder already exists...
        print(e)

    file_path = "received/{}/{}".format(source_address, filename)
    with open(file_path, 'w') as f:
        #File's bytes are concatenated
        f.write(buoyfile.content)
        f.close()
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"filename": filename, "source_address": source_address})

@app.get("/source/sender_mac_list")
def get_sender_mac_list():
    sender_mac_list = ['70b3d549909cd59c', '70b3d549933c91d4', '70b3d54992152e85']
    #sender_mac_list = ['70b3d54992152e85']
    return JSONResponse(status_code=status.HTTP_200_OK, content={"sender_mac_list": sender_mac_list})
'''
