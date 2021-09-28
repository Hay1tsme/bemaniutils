import base64
import time
from typing import Optional

from bemani.client.base import BaseClient
from bemani.protocol import Node

class Beatstream2Client(BaseClient):
    name = 'TEST'
