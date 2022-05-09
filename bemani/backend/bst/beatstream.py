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

    def get_events(self) -> Node:
        root = super().get_events()
        """
        # Campaign, duno how to get the final phase to show up
        data = Node.void('data')
        data.add_child(Node.s32('type', 0))
        data.add_child(Node.s32('phase', 18))
        root.add_child(data)
        
        # Beast crissis
        data = Node.void('data')
        data.add_child(Node.s32('type', 1))
        data.add_child(Node.s32('phase', 4))
        root.add_child(data)
        
        # Unknown
        data = Node.void('data')
        data.add_child(Node.s32('type', 2))
        data.add_child(Node.s32('phase', 8)) 
        root.add_child(data)

        # Controls weather the 5th KAC screen is shown during the demo reel
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 1))
        root.add_child(data)
        
        # Eamuse app screenshots
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 2))
        root.add_child(data)
        
        # Unknown
        # data = Node.void('data')
        # data.add_child(Node.s32('type', 3))
        # data.add_child(Node.s32('phase', 3))
        # root.add_child(data)
        
        # Unknown
        # data = Node.void('data')
        # data.add_child(Node.s32('type', 3))
        # data.add_child(Node.s32('phase', 7))
        # root.add_child(data)
        
        # Controlls floor infection on attract screen, but does NOT disable the event
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 8))
        root.add_child(data)        
        
        # Unknown
        # data = Node.void('data')
        # data.add_child(Node.s32('type', 3))
        # data.add_child(Node.s32('phase', 12))
        # root.add_child(data)

        # Unknown
        # data = Node.void('data')
        # data.add_child(Node.s32('type', 3))
        # data.add_child(Node.s32('phase', 13))
        # root.add_child(data)

        # Unknown
        # data = Node.void('data')
        # data.add_child(Node.s32('type', 3))
        # data.add_child(Node.s32('phase', 16))
        # root.add_child(data)
        
        # A bunch of different stuff, including quaver and other notifs
        for x in range(0,40):
            data = Node.void('data')
            data.add_child(Node.s32('type', 4))
            data.add_child(Node.s32('phase', x))
            root.add_child(data)
        
        # Unknown
        # data = Node.void('data')
        # data.add_child(Node.s32('type', 5))
        # data.add_child(Node.s32('phase', 31))
        # root.add_child(data)
        
        # One of these values lets you pick courses
        for x in range(0,5):
            data = Node.void('data')
            data.add_child(Node.s32('type', 7))
            data.add_child(Node.s32('phase', x))
            root.add_child(data)
        
        # Beast Hacker
        data = Node.void('data')
        data.add_child(Node.s32('type', 8))
        data.add_child(Node.s32('phase', 10)) # Phase 1 - 9, plus unused 10th
        root.add_child(data)
        
        # Unknown
        data = Node.void('data')
        data.add_child(Node.s32('type', 100))
        data.add_child(Node.s32('phase', 0))
        root.add_child(data)
        
        # Unknown, only shows up in the code as &phases->byte6C + 1
        data = Node.void('data')
        data.add_child(Node.s32('type', 200))
        data.add_child(Node.s32('phase', 0))
        root.add_child(data)
        
        # First play free
        data = Node.void('data')
        data.add_child(Node.s32('type', 1000))
        data.add_child(Node.s32('phase', 2))
        root.add_child(data)
        """
        # First play free
        data = Node.void('data')
        data.add_child(Node.s32('type', 1100))
        data.add_child(Node.s32('phase', 2))
        root.add_child(data)
        
        return root

    def handle_pcb_boot_request(self, request: Node) -> Node:
        machine = self.data.local.machine.get_machine(self.config['machine']['pcbid'])
        arcade = self.data.local.machine.get_arcade(machine.arcade)
        pcb2 = Node.void('pcb')
        pcb2.set_attribute('status', '0')
        sinfo = Node.void('sinfo')
        pcb2.add_child(sinfo)
        
        sinfo_nm = Node.string('nm', arcade.name)
        sinfo_cl_enbl = Node.bool('cl_enbl', False)
        sinfo_cl_h = Node.u8('cl_h', 0)
        sinfo_cl_m = Node.u8('cl_m', 0)
        sinfo_shop_flag = Node.bool('shop_flag', True)

        sinfo.add_child(sinfo_nm)
        sinfo.add_child(sinfo_cl_enbl)
        sinfo.add_child(sinfo_cl_h)
        sinfo.add_child(sinfo_cl_m)
        sinfo.add_child(sinfo_shop_flag)

        return pcb2
    
    def handle_info_common_request(self, request: Node) -> Node:
        info2 = Node.void('info')
        info2.set_attribute('status', '0')

        event_ctrl = self.get_events()
        info2.add_child(event_ctrl)

        return info2

    # Called after settings_write, not sure what it does
    def handle_info_music_count_read_request(self, request: Node) -> Node:
        info2 = Node.void('info2')
        record = Node.void('record')
        record.add_child(Node.void('rec'))
        record.add_child(Node.void('rate'))
        info2.add_child(record)
        return info2
    
    # Called after music_count_read. Might have something to do with song popularity?
    def handle_info_music_ranking_read_request(self, Request: Node) -> Node:
        info2 = Node.void('info2')
        ranking = Node.void('ranking')
        ranking.add_child(Node.void('count'))
        info2.add_child(ranking)
        return info2

    # First call when somebody cards in, returns the status of a few crossover events
    def handle_player_start_request(self, request: Node) -> Node:
        userid = self.data.local.user.from_refid(self.game, self.version, request.child_value('rid'))
        profile = self.data.local.user.get_profile(self.game, self.version, userid)
        player2 = Node.void('player')

        plytime = Node.s32('plyid', 0)
        if profile is not None:
            plytime = Node.s32('plyid', profile.get_int("plyid", 1))
            
        player2.add_child(plytime)

        start_time = Node.u64('start_time', Time.now() * 1000)
        player2.add_child(start_time)

        return player2