FROM python:3

ADD pemesanan.py .

COPY . /PEMESANANMEALKIT
WORKDIR /PEMESANANMEALKIT
RUN pip install fastapi uvicorn python-jose[cryptography] python-multipart passlib[bcrypt]
# Command to run the FastAPI server when the container starts
CMD ["uvicorn", "pemesanan:app", "--host=0.0.0.0", "--port=80"]