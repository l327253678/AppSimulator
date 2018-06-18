# coding=utf-8
import os

PAGE_SIZE = 20

REDIS_SERVER = 'redis://' + os.environ["REDIS_SERVER_IP"] + '/11'  # 'redis://172.16.55.155'
# REDIS_SERVER = 'redis://192.168.187.13/11'
REDIS_SERVER_RESULT = 'redis://' + os.environ["REDIS_SERVER_IP"] + '/10'

MONGODB_SERVER_IP = os.environ["MONGODB_SERVER_IP"]  # "172.16.55.155"
# MONGODB_SERVER = "192.168.16.223"
MONGODB_SERVER_PORT = int(os.environ["MONGODB_SERVER_PORT"])
# MONGODB_PORT = 37017


STATUS_RPC_TIMEOUT = 'rpc_timeout'
STATUS_UNKOWN = 'unkown'
STATUS_WAIT = 'wait'
STATUS_RUNNING = 'running'
STATUS_SUSPEND = 'suspend'

SCOPE_TIMES = 1 * 60

# RPC_CLIENT = "http://192.168.31.227:8003/"
# RPC_CLIENT = "http://172.16.253.36:8003/"
# RPC_PORT = 8003
RPC_SERVER_TIMEOUT = 5
