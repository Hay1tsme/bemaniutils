import copy
import random
import struct
from typing import Optional, Dict, Any, List, Tuple
import time

from bemani.backend.bst.base import BSTBase

from bemani.common import ValidatedDict, VersionConstants, Time, ID, intish
from bemani.backend.ess import EventLogHandler
from bemani.data import Data, UserID, Score
from bemani.protocol import Node

class Beatstream(EventLogHandler, BSTBase):
    name = "BeatStream"
    version = VersionConstants.BEATSTREAM
    #TODO: Beatstream 1 support