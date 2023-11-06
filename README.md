# Tugas TST - PemesananMealKit
**18221120 - Carissa Tabina Rianda**

Program Pemesanan Meal Kit menggunakan API yang digunakan untuk menambah data pesanan jika seseorang terdaftar sebagai user. Pada program ini akan diminta id user, nama user, id barang, nama barang, dan jumlah barang. Jika barang yang akan dibeli melebihi stok, program akan mengeluarkan output bahwa pesanan gagal dilakukan. Jika stok cukup, program akan mengeluarkan output bahwa pesanan berhasil dilakukan dan stok barang akan berkurang pada data barang.

 Library yang digunakan yaitu
 1. fastapi
 2. uvicorn

Cara Run Via Virtual Enviroment (venv) Python -- Windows
1. Pull repository ini ke dalam local folder
2. Buka terminal di VS Code atau via command prompt bisa
3. Ketik python -m venv [nama virtual enviroment (dibebaskan)] lalu enter
4. Masuk ke venv dengan cara ketik [nama virtual enviroment (dibebaskan)]\Scripts\activate
5. Install library terkait dengan cara pip install fastapi uvicorn
6. Jalankan aplikasi dengan uvicorn pemesanan:app --port 8000 --reload
