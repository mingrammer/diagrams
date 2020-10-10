# do nothing but just import providers in case syntax error
# it usually caused by wrong settings in config.py
from diagrams.tencentcloud.compute import CVM
from diagrams.tencentcloud.network import CLB
from diagrams.tencentcloud.database import CDB
from diagrams.tencentcloud.storage import CBS
from diagrams.tencentcloud.middleware import CMQ
from diagrams.tencentcloud.container import TKE
from diagrams.tencentcloud.serverless import SCF
