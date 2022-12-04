import pandas as pd
import numpy as np
import pickle
import csv
import codecs
from io import StringIO
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from helpers_func import *


class Item(BaseModel):
    name: str
    year: int
    km_driven: int
    fuel: str
    seller_type: str
    transmission: str
    owner: str
    mileage: str 
    engine: str
    max_power: str
    torque: str
    seats: float | None


# функция - конвертор pydantic model в pandas
def converter_to_pd(item: Item):
    new_row = {
                'name': item.name,
                'year': item.year,
                'km_driven': item.km_driven,
                'fuel': item.fuel,
                'seller_type': item.seller_type,
                'transmission': item.transmission,
                'owner': item.owner,
                'mileage': item.mileage,
                'engine': item.engine,
                'max_power': item.max_power,
                'torque': item.torque,
                'seats': item.seats
              }

    return pd.DataFrame([new_row])


# функция для предобработки данных
def preprocessing_data(df):
    # регулярное выражение для чисел
    reg_num = r'([0-9]*[.,]?[0-9]+)'

    # удаляем столбец selling price если он есть
    if 'selling_price' in df.columns:
        df = df.drop('selling_price', axis=1)

    # вытаскиваем из названия машины бренд
    df['name'] = pd.DataFrame(get_brand_car(df))

    if df.year.dtype == 'object':
        df['year'] = df['year'].str.extract(reg_num).apply(pd.to_numeric).astype(int)

    if df.km_driven.dtype == 'object':
        df['km_driven'] = df['km_driven'].str.extract(reg_num).apply(pd.to_numeric).astype(int)

    if df.seats.dtype == 'object':
        df['seats'] = df['seats'].str.extract(reg_num).apply(pd.to_numeric)

    df['mileage'] = df['mileage'].str.extract(reg_num).apply(pd.to_numeric)
    df['engine'] = df['engine'].str.extract(reg_num).apply(pd.to_numeric)
    df['max_power'] = df['max_power'].str.extract(reg_num).apply(pd.to_numeric)
    
    # формируем из torque два столбца
    pre_torque, pre_max_torque_rpm = parsing_torque(df)

    df['torque'] = pd.DataFrame(pre_torque)
    df['max_torque_rpm'] = pd.DataFrame(pre_max_torque_rpm)

    # заполняем пропуски медианой
    df = df.fillna(df.median())

    # используем квадрат года
    df['year'] = df['year'].apply(lambda x: x ** 2)

    # используем более подходящий тип
    df['engine'] = df['engine'].astype(int)
    df['seats'] = df['seats'].astype(int).apply(str)

    # логарифмируем столбцы
    df['max_torque_rpm'] = df['max_torque_rpm'].apply(np.log)
    df['engine'] = df['engine'].apply(np.log)

    # добавляем доп столбец для обучения
    df['bhp_cc'] = df['max_power'] * df['engine']

    return df


# функция для one hot кодирования
def ohe_encode(df):
    col_cat = ['name', 'transmission', 'seats', 'fuel', 'seller_type', 'owner']

    X_encoded = pd.DataFrame(ohe.transform(df[col_cat]))
    X_encoded.columns = ohe.get_feature_names_out(col_cat)

    X_test = pd.concat([df.drop(col_cat, axis=1), X_encoded], axis=1)

    return X_test


dir = './weights/'
ohe_filename = 'ohe_weights.pkl'
scaler_filename = 'scaler_weights.pkl'
model_filename = 'model_weights.pkl'

with open(dir + ohe_filename, 'rb') as file: 
    ohe = pickle.load(file)

with open(dir + scaler_filename, 'rb') as file: 
    scaler = pickle.load(file) 

with open(dir + model_filename, 'rb') as file: 
    model = pickle.load(file) 

app = FastAPI()


@app.post("/predict_item")
def predict_item(item: Item) -> float:

    df = converter_to_pd(item)
    df = preprocessing_data(df)

    x = ohe_encode(df)
    x = scaler.transform(x)

    response = model.predict(x)[0]

    return response



@app.post("/predict_items")
def predict_items(upload_file: UploadFile = File(...)):
    csvReader = csv.DictReader(codecs.iterdecode(upload_file.file, 'utf-8'))

    df = pd.DataFrame()
    for row in csvReader:   
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    upload_file.file.close()

    df_res = df
    
    df = preprocessing_data(df)
    x = ohe_encode(df)
    x = scaler.transform(x)

    predict = model.predict(x)

    df_res['predict_selling_price'] = pd.DataFrame(predict)

    outFileAsStr = StringIO()
    df_res.to_csv(outFileAsStr, index = False)
    response = StreamingResponse(
        iter([outFileAsStr.getvalue()]),
        media_type='text/csv',
        headers={
            'Content-Disposition': 'attachment;filename=dataset.csv',
            'Access-Control-Expose-Headers': 'Content-Disposition'
        }
    )

    return response
