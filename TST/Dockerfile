FROM python:3

ADD pemesanan.py .

COPY . /PEMESANANMEALKIT
WORKDIR /PEMESANANMEALKIT
RUN pip install fastapi uvicorn 
CMD ["uvicorn", "pemesanan:app", "--host=0.0.0.0", "--port=80"]