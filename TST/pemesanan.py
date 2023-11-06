from fastapi import FastAPI, HTTPException
import json
from pydantic import BaseModel

class InputUser(BaseModel):
    id_user : int
    nama_user : str
    id_barang : int
    nama_barang : str
    jumlah : int
    
class DataUser(BaseModel):
	id_user: int
	nama_user: str

app = FastAPI()

with open("user_pemesanan.json","r") as read_file:
	user_pemesanan = json.load(read_file)
 
with open("hasil_pemesanan.json","r") as read_file:
	hasil_pemesanan = json.load(read_file)

with open("data_barang.json","r") as read_file:
	data_barang = json.load(read_file)
 
# Save ke json setiap hasil_pemesanan dilakukan
def save_result_to_json(data, filename):
    with open(filename, "w") as write_file:
        json.dump(data, write_file)

# Mendapatkan seluruh riwayat hasil pemesanan
@app.get('/hasil')
async def read_data_hasil_pemesanan():
	return hasil_pemesanan['hasil_pemesanan']

# Mendapatkan seluruh data barang
@app.get('/barang')
async def read_data_barang():
	return data_barang['data_barang']

# Mendapatkan riwayat hasil pemesanan untuk user_id tertentu
@app.get('/hasil/{user_id}')
async def get_data_hasil_pemesanan_user(user_id: int):
    matching_user = []
    for hasil in hasil_pemesanan['hasil_pemesanan']:
        if hasil['id_user'] == user_id:
            matching_user.append(hasil_pemesanan)
    
    if not matching_user :
        raise HTTPException(
		    status_code=404, detail=f'User tidak terdaftar'
	)

    return matching_user

# Melakukan post ke dalam JSON user_pemesanan dan mengembalikan daftar user yang memesan
@app.post('/add_user')
async def add_user(dataUser : DataUser):
	data = dataUser.dict()
	dataUser_found = False
	for user in user_pemesanan['user_pemesanan']:
		if user['id_user'] == data['id_user'] or user['nama_user'] == data['nama_user']:
			dataUser_found = True
			return "User " + str(user['id_user']) + " dengan username " + str(user['nama_user']) + " telah terdaftar."
	
	if not dataUser_found:
		user_pemesanan['user_pemesanan'].append(data)
		save_result_to_json(user_pemesanan, "user_pemesanan.json")
		return data
	raise HTTPException(
		status_code=404, detail=f'user not found'
	)

#Melakukan post ke JSON hasil_pemesanan 
@app.post('/pemesanan')
async def add_hasil_pemesanan(item: InputUser):
    data = item.dict()
    i = 1
    jumlah = data.get("jumlah")
    barang_found = False
    stok_tersedia = False
    id_barang = data.get("id_barang")
    for barang in data_barang['data_barang']:
        if barang['id_barang'] == data['id_barang']:
            barang_found = True
            if barang['stok'] >= jumlah:
                stok_tersedia = True
                hasilPemesanan = "Anda berhasil memesan barang"
                nominal = jumlah * barang['harga']
                stok = barang['stok'] - jumlah
            else :
                hasilPemesanan = "Anda tidak berhasil memesan barang"
            break

    if not barang_found :
        return "Barang tidak tersedia"
    if not stok_tersedia :
        return "Anda tidak berhasil memesan barang"


# Update stok barang di dalam data_barang.json
    for barang in data_barang['data_barang']:
        if barang['id_barang'] == data['id_barang']:
            barang['stok'] -= jumlah

# Simpan perubahan stok ke dalam file data_barang.json
    with open("data_barang.json", "w") as write_file:
        json.dump(data_barang, write_file)

	
    for user in user_pemesanan['user_pemesanan'] :
        if user['id_user'] == data['id_user']:
            for count in hasil_pemesanan['hasil_pemesanan']:
                i += 1
            result = {
                "id_pesanan": i,
                "id_user" : data['id_user'],
                "nama_user": data['nama_user'],
                "id_barang": data['id_barang'],
                "nama_barang": data['nama_barang'],
                "jumlah" : jumlah,
                "nominal" : nominal,
                "hasilPemesanan" : hasilPemesanan
            }
            hasil_pemesanan['hasil_pemesanan'].append(result)
            save_result_to_json(hasil_pemesanan,"hasil_pemesanan.json")
            return hasilPemesanan
        
    

        
    raise HTTPException(
		status_code=404, detail=f'item not found'
	)

@app.delete('/user/{user_id}')
async def delete_user(user_id: int):
	user_found = False
	for user_idx, user_item in enumerate(user_pemesanan['user_pemesanan']):
		if user_item['id_user'] == user_id:
			user_found = True
			user_pemesanan['user_pemesanan'].pop(user_idx)
			
			save_result_to_json(user_pemesanan, "user_pemesanan.json")
			return "updated"
	
	if not user_found:
		return "User ID not found."
	raise HTTPException(
		status_code=404, detail=f'User not found'
	)
