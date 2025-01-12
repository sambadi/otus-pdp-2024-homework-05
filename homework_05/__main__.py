import logging
from http.server import HTTPServer

import argparse

from homework_05.api import MainHTTPHandler
from homework_05.store import RedisStore

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", action="store", type=int, default=8080)
    parser.add_argument("-l", "--log", action="store", default=None)
    parser.add_argument(
        "-rh", "--redis-host", action="store", type=str, default="localhost"
    )
    parser.add_argument("-rp", "--redis-port", action="store", type=int, default=6379)
    args = parser.parse_args()
    logging.basicConfig(
        filename=args.log,
        level=logging.INFO,
        format="[%(asctime)s] %(levelname).1s %(message)s",
        datefmt="%Y.%m.%d %H:%M:%S",
    )
    logging.info(
        "RedisStore configured to connect to host=%s, port=%d",
        args.redis_host,
        args.redis_port,
    )
    MainHTTPHandler.store = RedisStore(args.redis_host, args.redis_port)
    server = HTTPServer(("localhost", args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    logging.info("Stopping server")
    server.server_close()
