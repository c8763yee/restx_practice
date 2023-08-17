from time import sleep
import celery
from config import BaseCeleryConfig as CeleryConfig

Celery = celery.Celery
celery_app = Celery(
    __name__,
    broker=CeleryConfig.broker_url,
    backend=CeleryConfig.backend_url,
)


# 其中一隻 task 需能取得執行進度
@celery_app.task(bind=True)
def pow_(self, x: float, n: int) -> int:
    x = 1 / x if n < 0 else x
    val = 1
    n = abs(n)

    for i in range(n):
        val = x * i
        # update state
        self.update_state(
            state="PROGRESS",
            meta={"current": i + 1, "total": n, "value": val},  # 1-indexed
        )
        sleep(1)

    return val


class FibTask(celery.Task):
    def run(self, n):
        if n <= 1:
            return int(n == 1)
        a, b, c = 0, 1, 1
        for i in range(2, n + 1):
            c = a + b
            a = b
            b = c
            self.update_state(
                state="PROGRESS", meta={"current": i, "total": n, "value": c}
            )
            sleep(1)
        return c


AsyncResult = celery_app.AsyncResult
fib_task = celery_app.register_task(FibTask())
