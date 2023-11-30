from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import json

SECRET_KEY = "25ce8b918a5d21abec4a39f7ba25c245699f245ac8bdcb73ead119543a6d1e0b"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 6000

class InputUser(BaseModel):
    username : str
    nama_user: str
    id_barang: int
    jumlah: int
    
class DataUser(BaseModel):
    username : str
    nama_user: str
    password: str
 
class Token(BaseModel):
    access_token : str
    token_type : str
    
class TokenData(BaseModel):
    username: str or None = None
    
class UserInDB(DataUser):
    id_user : int
    username : str
    hashed_password: str
    disabled: bool or None = None

    
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

def get_user(username: str):
    for user in user_pemesanan['user_pemesanan']:
        if user['username'] == username:
           user_dict = {
               "id_user" : user['id_user'],
                "username" :  user['username'],
                "nama_user": user['nama_user'],
               "hashed_password": user['password'],
               "password" : ""
           }
           return UserInDB(**user_dict)
    return None




def authenticate_user(username: str, password: str):
    user = get_user(username)
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
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[DataUser, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/register", tags=['Register'])
async def register_user(data: DataUser):
    dataUser_found = False

    for user in user_pemesanan['user_pemesanan']:
        if user['nama_user'] == data.username:
            dataUser_found = True
            return f"User {user['id_user']} dengan username {user['nama_user']} telah terdaftar."

    if not dataUser_found:
        i = len(user_pemesanan['user_pemesanan']) + 1
        result = {
            "id_user": i,
            "nama_user": data.nama_user,
            "username" : data.username,
            "password": get_password_hash(data.password)
        }
        user_pemesanan['user_pemesanan'].append(result)
        save_result_to_json(user_pemesanan, "user_pemesanan.json")
        return {"message": "User berhasil mendaftar"}

    raise HTTPException(
        status_code=404, detail=f'User not found'
    )
@app.post("/token", response_model=Token, tags=['Generate Token'])
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
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


@app.put("/update/me", tags=['Auth Users'])
async def update_my_data(
    current_user: Annotated[DataUser, Depends(get_current_active_user)],
    data: DataUser
):
    # Check if the user making the request is the same as the one being updated
    if current_user.username != data.username:
        raise HTTPException(
            status_code=403,
            detail="You can only update your own data",
        )

    # Update the user data here
    current_user.username = data.username
    current_user.nama_user = data.nama_user
    current_user.password = get_password_hash(data.password)

    # Save the updated user data back to your storage (e.g., JSON file)
    save_result_to_json(user_pemesanan, "user_pemesanan.json")

    return {"message": "User data updated successfully"}


# Mendapatkan seluruh data barang
@app.get('/barang')
async def read_data_barang():
	return data_barang['data_barang']

@app.get('/hasil', response_model=list[InputUser], tags=['Get User Pemesanan'])
async def get_data_hasil_pemesanan_user(
    current_user: Annotated[DataUser, Depends(get_current_active_user)]
):
    username: str = current_user.username

    matching_user = []
    for hasil in hasil_pemesanan['hasil_pemesanan']:
        if 'username' in hasil and hasil['username'] == username:
            matching_user.append(hasil)
    
    if not matching_user:
        raise HTTPException(
            status_code=404, detail='User tidak memiliki data hasil pemesanan'
        )

    return matching_user



#Melakukan post ke JSON hasil_pemesanan 
@app.post('/pemesanan', response_model=dict, tags=['Add Hasil Pemesanan'])
async def add_hasil_pemesanan(
    current_user: Annotated[DataUser, Depends(get_current_active_user)],
    data: InputUser
):
    # Check if the username in the submitted data matches the username of the current user
    if data.username != current_user.username:
        raise HTTPException(
            status_code=403,
            detail="You can only add hasil pemesanan for yourself",
        )

    i = 1
    jumlah = data.jumlah
    data_dict = data.dict()
    barang_found = False
    stok_tersedia = False
    nominal = 0

    for barang in data_barang['data_barang']:
        if barang['id_barang'] == data_dict['id_barang']:
            barang_found = True
            if barang['stok'] >= jumlah:
                stok_tersedia = True
                hasilPemesanan = "Anda berhasil memesan barang"
                nominal = jumlah * barang['harga']
                stok = barang['stok'] - jumlah
            else:
                hasilPemesanan = "Anda tidak berhasil memesan barang"
            break
    if not stok_tersedia:
        hasilPemesanan = "Anda tidak berhasil memesan barang, Stok habis"
    if not barang_found:
        hasilPemesanan = "Barang tidak tersedia"
    
    for barang in data_barang['data_barang']:
        if barang['id_barang'] == data_dict['id_barang']:
                barang['stok'] -= jumlah
        
    with open("data_barang.json", "w") as write_file:
                    json.dump(data_barang, write_file)

    # Add hasil pemesanan for the current user
    for user in user_pemesanan['user_pemesanan']:
        for count in hasil_pemesanan['hasil_pemesanan']:
            i += 1
            result = {
                "id_pesanan": i,
                "username" : data.username,
                "nama_user": data.nama_user,
                "id_barang": data.id_barang,
                "jumlah" : jumlah,
                "nominal" : nominal,
                "hasilPemesanan" : hasilPemesanan,
            }
            hasil_pemesanan['hasil_pemesanan'].append(result)
            save_result_to_json(hasil_pemesanan, "hasil_pemesanan.json")
            return {"message": hasilPemesanan}
    raise HTTPException(
		status_code=404, detail=f'user not found'
	)

@app.delete('/user/me', tags=['Delete User'])
async def delete_authenticated_user(current_user: Annotated[DataUser, Depends(get_current_active_user)]):
    user_id = current_user.id_user

    user_found = False
    for user_idx, user_item in enumerate(user_pemesanan['user_pemesanan']):
        if user_item['id_user'] == user_id:
            user_found = True
            user_pemesanan['user_pemesanan'].pop(user_idx)
            save_result_to_json(user_pemesanan, "user_pemesanan.json")
            return {"message": "User deleted successfully"}

    if not user_found:
        raise HTTPException(
            status_code=404, detail='User not found'
        )
