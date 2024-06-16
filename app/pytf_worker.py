from celery import Celery

app = Celery('celery_worker',
             broker='pyamqp://guest:guest@my_rabbitmq_c//',
             backend='db+postgresql://cloe:cloe@my_postgres_c/cloedb')


def fib(n: int) -> int:
    if n > 1:
        return fib(n - 1) + fib(n - 2)
    elif n == 1:
        return 1
    elif n == 0:
        return 1


# def fib_dp(n: int) -> int:
#
#     if n == 0 or n == 1:
#         return n
#
#     a, b, c = 1, 1, 0
#
#     for i in range(1, n):
#         c = a + b
#         a = b
#         b = c
#     return c


@app.task(name='celery.fib_task')
def fib_task(n):
    return fib(n)


# @app.task(name='celery.fib_dp_task')
# def fib_dp_task(n):
#     return fib_dp(n)
