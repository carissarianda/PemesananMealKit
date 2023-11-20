from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import json

SECRET_KEY = "d0ba1b2795d465f636c24af3980de67546109235434a71c90f474b21ea61899f7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class InputUser(BaseModel):
    id_user : int
    nama_user : str
    id_barang : int
    nama_barang : str
    jumlah : int
    waktu : datetime
    
class DataUser(BaseModel):
    username : str
    nama_user: str
    disabled: bool or None = None
    
db = {
    "carissa": {
        "username": "carissa",
        "nama_user": "carissa",
        "hashed_password": "$2b$12$eYicYMBGBlvM/jGJe9VXP.k7ujIhD8fSVkgi1T.nyOb0Xrq/ienia",
        "disabled": False,
    }
}
 
class Token(BaseModel):
    access_token : str
    token_type : str
    
class TokenData(BaseModel):
    username: str or None = None
    
class UserInDB(DataUser):
    hashed_password: str
    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated = "auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()
def save_result_to_json(data, filename):
    with open(filename, "w") as write_file:
        json.dump(data, write_file)

with open("user_pemesanan.json","r") as read_file:
	user_pemesanan = json.load(read_file)
 
with open("hasil_pemesanan.json","r") as read_file:
	hasil_pemesanan = json.load(read_file)

with open("data_barang.json","r") as read_file:
	data_barang = json.load(read_file)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user
        
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[DataUser, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=DataUser)
async def read_users_me(
    current_user: Annotated[DataUser, Depends(get_current_active_user)]
):
    return current_user


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[DataUser, Depends(get_current_active_user)]
):
    return [{"item_id": "Foo", "owner": current_user.username}]

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
    data['waktu'] = data['waktu'].isoformat()
    barang_found = False
    stok_tersedia = False
    user_found = False
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
    for user in user_pemesanan['user_pemesanan']:
        if user['id_user'] == data['id_user']:
            user_found = True
    for barang in data_barang['data_barang']:
        if barang['id_barang'] == data['id_barang'] and user_found == True:
                barang['stok'] -= jumlah

# Simpan perubahan stok ke dalam file data_barang.json
    with open("data_barang.json", "w") as write_file:
        json.dump(data_barang, write_file)
	
    for user in user_pemesanan['user_pemesanan']:
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
                "hasilPemesanan" : hasilPemesanan,
                "waktu" : data['waktu']
            }
            hasil_pemesanan['hasil_pemesanan'].append(result)
            save_result_to_json(hasil_pemesanan, "hasil_pemesanan.json")
            return hasilPemesanan
    raise HTTPException(
		status_code=404, detail=f'user not found'
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

