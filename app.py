from flask import Flask, request
from flask_restx import Api, Resource, fields

from config import BaseFlaskConfig as FlaskConfig
from tasks import AsyncResult, fib_task, pow_

# 用 flask 做一個後端
app = Flask(__name__)
app.config.from_object(FlaskConfig)


# TODO:
# 1. find diff between celery broker and backend
# 2. use docker-compose to build redis and celery

# 及用 flask-restx 套件建立 restful API 及 swagger 頁面
api = Api(
    app,
    title="HW-0807",
    description="HW-0807",
    version="1.0.0",
    doc="/api/docs",
)

# 並用 Celery 建立 task 並用 redis 作為 broker

DEFAULT_INT = 10


fib_input = api.model(
    name="fib(input)",
    model={
        "n": fields.Integer(default=DEFAULT_INT, description="get nth fibonacci number")
    },
)

status_input = api.model(
    name="status(input)",
    model={"task_id": fields.String},
)


@api.route("/pow")
class pow(Resource):
    @api.doc(params={"x": "float", "n": "int"})
    def get(self):
        try:
            x = float(request.args.get("x"))
            n = int(request.args.get("n"))
        except ValueError:
            return dict(error="x must be float and n must be integer"), 400

        task_id = pow_.delay(x, n).id
        return dict(task_id=task_id)


# POST /fib
@api.route("/fib")
class Fib(Resource):
    @api.expect(fib_input)
    def post(self):
        try:
            n = int(api.payload.get("n"))
        except ValueError:
            return dict(error="n must be integer"), 400

        task_id = fib_task.delay(n).id
        return dict(task_id=task_id)


# 並能用另一隻 API 取得執行進度 or 執行結果
@api.route("/status")
class Status(Resource):
    @api.expect(status_input)
    def post(self):
        task_id = api.payload.get("task_id")
        if task_id == "":
            return dict(error="task_id is required"), 400

        result = AsyncResult(task_id)
        return_dict = dict(task_id=task_id, state=result.state, meta=result.info)

        if result.state == "SUCCESS":
            return_dict.update(val=result.get())

        return return_dict


# if __name__ == "__main__":
#     app.run(host=FlaskConfig.HOST, port=FlaskConfig.PORT)
