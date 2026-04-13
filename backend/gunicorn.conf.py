import os


bind = "0.0.0.0:8080"

workers = 2
worker_class = "sync"

timeout = 60
graceful_timeout = 30
keepalive = 5

max_requests = 1000
max_request_jitter = 100

accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s "%(r)s" %(s)s %(b)s %(D)sµs'


def post_fork(server, worker):
    server.log.info(
        f"Worker {worker.pid}: reinitializing Neo4j connection pool"
    )
    try:
        from neomodel import reset_config
        reset_config()
        server.log.info(f"Worker {worker.pid}: Neo4j pool reinitialized")
    except Exception as e:
        server.log.error(
            f"Worker {worker.pid}: failed to reinitialize Neo4j: {e}"
        )


def on_starting(server):
    server.log.info("Gunicorn master starting — LOTR Wiki Backend")


def worker_exit(server, worker):
    server.log.info(f"Worker {worker.pid} exited")
