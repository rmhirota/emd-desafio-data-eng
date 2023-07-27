import prefect
from prefect import task
from requests import get
import pandas as pd
from datetime import datetime
import os
import psycopg2


@task
def get_brt_data():
    logger = prefect.context.get("logger")
    logger.info("Coletando dados BRT...")
    res = get("https://dados.mobilidade.rio/gps/brt")
    df = pd.DataFrame.from_dict(res.json())
    df = pd.json_normalize(df["veiculos"])
    return df


@task
def write_brt_partial(df, dir):
    dir_exists = os.path.exists(dir)
    if not dir_exists:
        os.makedirs(dir)
    time = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = "{}/brt_partial_{}.csv".format(dir, time)
    df.to_csv(path)


@task
def check_files(dir):
    files = os.listdir(dir)
    files_names = []
    for file in files:
        files_names = files_names + [os.path.join(dir, file)]
    if len(files_names) < 10:
        return False
    else:
        return True


@task
def aggregate_brt(dir_origin):
    logger = prefect.context.get("logger")
    logger.info("Agregando dados BRT...")
    files = os.listdir(dir_origin)
    files_names = []
    for file in files:
        files_names = files_names + [os.path.join(dir_origin, file)]
    files_names.sort()
    files_names = files_names[0:10]
    brt_data = pd.concat(map(pd.read_csv, files_names))
    return brt_data


@task
def agg_file_name(dir_origin):
    files = os.listdir(dir_origin)
    files_names = []
    for file in files:
        files_names = files_names + [os.path.join(dir_origin, file)]
    files_names.sort()
    file_name = files_names[10][-21:]
    for file in files_names[0:10]:
        os.remove(file)
    return file_name


@task
def write_brt_agg(df, file_name, dir_save):
    logger = prefect.context.get("logger")
    logger.info("Salvando CSV agregado BRT...")
    dir_exists = os.path.exists(dir_save)
    if not dir_exists:
        os.makedirs(dir_save)
    df.to_csv("{}/brt_agg_{}".format(dir_save, file_name))


@task
def upload_brt_db(df, conn):
    db = psycopg2.connect(
        host=conn["HOST"],
        database=conn["DB"],
        user=conn["USER"],
        password=conn["PASSWORD"],
    )
    df.to_sql("brt_data", con=db, if_exists="append", index=False)
