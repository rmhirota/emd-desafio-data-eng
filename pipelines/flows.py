from prefect import Flow, Parameter
from datetime import timedelta
from prefect.schedules import IntervalSchedule
from prefect.run_configs import DockerRun
from prefect.executors import DockerExecutor


schedule_brt = IntervalSchedule(interval=timedelta(minutes=1))
schedule_db = IntervalSchedule(interval=timedelta(minutes=10))

conn = {
    "DB": "db",
    "USER": "user",
    "PASSWORD": "password",
    "PORT": 5432,
    "HOST": "localhost",
}


with Flow("brt_flow", schedule=schedule_brt) as brt_flow:
    dir = Parameter("dir", default="brt_partial")
    brt_data = collect_brt()
    write_brt_partial(brt_data, dir)
brt_flow.register(project_name="pref")
brt_flow.run_config = DockerRun()
brt_flow.executor = DockerExecutor()


with Flow("db_flow", schedule=schedule_db) as db_flow:
    dir_origin = Parameter("dir_origin", default="brt_partial")
    dir_save = Parameter("dir_save", default="brt_agg")

    if check_files(dir_origin):
        file_name = agg_file_name(dir_origin)
        brt_data = aggregate_brt(dir_origin)
        write_brt_agg(brt_data, file_name, dir_save)
        upload_brt_db(brt_data, conn)
db_flow.register(project_name="pref")
db_flow.run_config = DockerRun()
db_flow.executor = DockerExecutor()
