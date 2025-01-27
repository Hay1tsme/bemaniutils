from typing import Dict, Any

from bemani.common import Profile, ValidatedDict, VersionConstants, ID, Time
from bemani.backend.bst.base import BSTBase
from bemani.common import VersionConstants, Time
from bemani.backend.ess import EventLogHandler
from bemani.common.constants import BroadcastConstants
from bemani.common.validateddict import ValidatedDict
from bemani.data.types import UserID
from bemani.protocol import Node
from bemani.data import Song

class Beatstream2(EventLogHandler, BSTBase):
    name = "BeatStream アニムトライヴ"
    version = VersionConstants.BEATSTREAM_2

    GRADE_AAA_RED = 0
    GRADE_AAA = 1
    GRADE_AA = 2
    GRADE_A = 3
    GRADE_B = 4
    GRADE_C = 5
    GRADE_D = 6

    MEDAL_NOPLAY = 0
    MEDAL_FAILED = 1
    MEDAL_SAVED = 2
    MEDAL_CLEAR = 3
    MEDAL_FC = 4
    MEDAL_PERFECT = 5

    @classmethod
    def get_settings(cls) -> Dict[str, Any]:
        """
        Return all of our front-end modifiably settings.
        """
        return {
            'bools': [
                {
                    'name': 'Disable Local Matching',
                    'tip': 'Disable local matching between games.',
                    'category': 'game_config',
                    'setting': 'disable_local_match',
                },
                {
                    'name': 'Disable Global Matching',
                    'tip': 'Disable global matching between games.',
                    'category': 'game_config',
                    'setting': 'disable_global_match',
                },
            ]
        }
    
    def get_events(self) -> Node:
        root = super().get_events()
        game_config = self.get_game_config()
        
        # Campaign
        data = Node.void('data')
        data.add_child(Node.s32('type', 0))
        data.add_child(Node.s32('phase', 18))
        root.add_child(data)
        
        # Beast crissis
        data = Node.void('data')
        data.add_child(Node.s32('type', 1))
        data.add_child(Node.s32('phase', 4))
        root.add_child(data)

        # 5th KAC screen on the demo reel
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 1))
        root.add_child(data)
        
        # Eamuse app screenshots
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 2))
        root.add_child(data)
        
        # Enables continues
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 3))
        root.add_child(data)

        # Allows 3 stage with paseli
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 4))
        root.add_child(data)
        
        # Local matching at start of credit enable
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 7))
        if not game_config.get_bool('enable_local_match'):
            root.add_child(data)
        
        # Controlls floor infection on attract screen ONLY
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 8))
        root.add_child(data)
        
        # Global matching during song loading enable
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 12))
        if not game_config.get_bool('enable_global_match'):
            root.add_child(data)

        # Unlocks the bemani rockin fes songs
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 13))
        root.add_child(data) 

        # Enables Illil partner addition
        data = Node.void('data')
        data.add_child(Node.s32('type', 3))
        data.add_child(Node.s32('phase', 16))
        root.add_child(data)

        # Controls notifs when carding in      
        data = Node.void('data')
        data.add_child(Node.s32('type', 4))
        data.add_child(Node.s32('phase', 31))
        root.add_child(data)
        
        # Courses
        # 1 = 1-12, 2 = 13 and 14, 3 = 15, 4 = kami
        # any other value disables courses
        # need to set 1-4 to enable all courses
        for x in range(1,5):
            data = Node.void('data')
            data.add_child(Node.s32('type', 7))
            data.add_child(Node.s32('phase', x))
            root.add_child(data)
        
        # Beast Hacker
        data = Node.void('data')
        data.add_child(Node.s32('type', 8))
        data.add_child(Node.s32('phase', 10)) # Phase 1 - 9, plus unused 10th
        root.add_child(data)
        
        # First play free
        data = Node.void('data')
        data.add_child(Node.s32('type', 1100))
        data.add_child(Node.s32('phase', 2))
        root.add_child(data)

        return root

    def update_score(self, extid, songid, chartid, loc, points, gauge, 
    max_combo, grade, medal, fanta_count, great_count, fine_count, miss_count) -> None:
        butils_userid = self.data.local.user.from_extid(self.game, self.version, extid)
        if butils_userid is None:
            return None

        old_score = self.data.local.music.get_score(self.game, self.version, butils_userid, songid, chartid)

        if old_score is not None: 
            new_record = old_score.points < points
            new_points = max(old_score.points, points)
            new_data = old_score.data
        else:
            new_record = True
            new_points = points
            new_data = ValidatedDict()

        new_loc = loc
        # Only update the location if it's a new high score
        if not new_record: 
            new_loc = old_score.location

        new_gauge = max(new_data.get_int('gauge'), gauge)
        new_data.replace_int('gauge', new_gauge)

        new_max_combo = max(new_data.get_int('max_combo'), max_combo)
        new_data.replace_int('max_combo', new_max_combo)

        # Grades get better as their value decreases
        if "grade" in new_data:
            new_grade = min(new_data.get_int('grade'), grade)
            new_data.replace_int('grade', new_grade)
        else:
            new_data.replace_int('grade', grade)

        new_medal = max(new_data.get_int('medal'), medal)
        new_data.replace_int('medal', new_medal)

        # Only replace notecoutns if we upscored
        if new_record:
            new_data.replace_int('fanta_count', fanta_count)
            new_data.replace_int('great_count', great_count)
            new_data.replace_int('fine_count', fine_count)
            new_data.replace_int('miss_count', miss_count)

        data = {
            "gauge": gauge,
            "max_combo": max_combo,
            "grade": grade,
            "medal" : medal,
            "fanta_count": fanta_count,
            "great_count": great_count,
            "fine_count": fine_count,
            "miss_count": miss_count
        }
        
        self.data.local.music.put_attempt(
            self.game, 
            self.version, 
            butils_userid,
            songid,
            chartid,
            loc,
            points,
            data,
            new_record,
            Time.now())

        self.data.local.music.put_score(self.game, 
            self.version, 
            butils_userid,
            songid,
            chartid,
            new_loc,
            new_points,
            new_data,
            new_record,
            Time.now())

    # Helper method to formay a player profile as a Node that the game will accept
    def format_player_profile(self, profile: Profile) -> Node:
        userid = self.data.local.user.from_refid(self.game, self.version, profile.refid)
        root = Node.void("player2")
        pdata = Node.void('pdata')
        root.add_child(pdata)
        
        account = Node.void('account')
        account.add_child(Node.s32('usrid', profile.get_int("usrid")))
        account.add_child(Node.s32('is_takeover', profile.get_int("is_takeover")))
        account.add_child(Node.s32('tpc', profile.get_int("tpc")))
        account.add_child(Node.s32('dpc', profile.get_int("dpc")))
        account.add_child(Node.s32('crd', profile.get_int("crd")))
        account.add_child(Node.s32('brd', profile.get_int("brd")))
        account.add_child(Node.s32('tdc', profile.get_int("tdc")))
        account.add_child(Node.s32('intrvld', profile.get_int("intrvld")))
        account.add_child(Node.s16('ver', profile.get_int("ver")))
        account.add_child(Node.u64('pst', profile.get_int("pst")))
        account.add_child(Node.u64('st', Time.now() * 1000))
        account.add_child(Node.bool('ea', profile.get_int("ea", True)))
        pdata.add_child(account)

        base = Node.void('base')
        base.add_child(Node.string('name', profile.get_str('name')))
        base.add_child(Node.s8('brnk', profile.get_int('brnk')))
        base.add_child(Node.s8('bcnum', profile.get_int('bcnum')))
        base.add_child(Node.s8('lcnum', profile.get_int('lcnum')))
        base.add_child(Node.s32('volt', profile.get_int('volt')))
        base.add_child(Node.s32('gold', profile.get_int('gold')))
        base.add_child(Node.s32('lmid', profile.get_int('lmid')))
        base.add_child(Node.s8('lgrd', profile.get_int('lgrd')))
        base.add_child(Node.s8('lsrt', profile.get_int('lsrt')))
        base.add_child(Node.s8('ltab', profile.get_int('ltab')))        
        base.add_child(Node.s8('splv', profile.get_int('splv')))
        base.add_child(Node.s8('pref', profile.get_int('pref')))
        base.add_child(Node.s32('lcid', profile.get_int('lcid')))
        base.add_child(Node.s32('hat', profile.get_int('hat')))
        pdata.add_child(base)

        survey = Node.void('survey')
        survey.add_child(Node.s8('motivate', 0)) # Needs testing
        pdata.add_child(survey)
        
        item = Node.void('item')
        hacker = Node.void('hacker')
        course = Node.void('course')
        play_log = Node.void('play_log')        

        achievements = self.data.local.user.get_achievements(self.game, self.version, userid)
        for i in achievements:
            if i.type[:4] == "item":
                info = Node.void('info')
                info.add_child(Node.s32('id', i.id))
                info.add_child(Node.s32('type', i.data.get_int('type')))
                info.add_child(Node.s32('param', i.data.get_int('param')))
                info.add_child(Node.s32('count', i.data.get_int('count')))
                item.add_child(info)

            elif i.type == "hacker":
                info = Node.void('info')
                info.add_child(Node.s32('id', i.id))
                info.add_child(Node.s8('state0', i.data.get_int("state0")))
                info.add_child(Node.s8('state1', i.data.get_int("state1")))
                info.add_child(Node.s8('state2', i.data.get_int("state2")))
                info.add_child(Node.s8('state3', i.data.get_int("state3")))
                info.add_child(Node.s8('state4', i.data.get_int("state4")))
                info.add_child(Node.u64('update_time', Time.now() * 1000)) # update_time is required or the profile will fail
                hacker.add_child(info) 

            elif i.type == "course":
                info = Node.void('record')
                info.add_child(Node.s32('course_id', i.data.get_int("course_id")))
                info.add_child(Node.s32('play', i.data.get_int("clear"))) # Play_id?
                info.add_child(Node.bool('is_touch', i.data.get_bool("is_touch", False))) # ???
                info.add_child(Node.s32('clear', i.data.get_int("clear"))) # Not sure what it wants here...
                info.add_child(Node.s32('gauge', i.data.get_int("gauge")))
                info.add_child(Node.s32('score', i.data.get_int("score")))
                info.add_child(Node.s32('grade', i.data.get_int("grade")))
                info.add_child(Node.s32('medal', i.data.get_int("medal")))
                info.add_child(Node.s32('combo', i.data.get_int("combo")))
                course.add_child(info)

                rate = Node.void('rate')
                rate.add_child(Node.s32('course_id', i.data.get_int("course_id")))
                rate.add_child(Node.s32('play_count', i.data.get_int("play_count")))
                rate.add_child(Node.s32('clear_count', i.data.get_int("clear_count")))
                course.add_child(rate)
            
            elif i.type == "crysis":
                crysis = Node.void('crysis')
                crysis.add_child(Node.s32('id', i.id))
                crysis.add_child(Node.s8('step', i.data.get_int("step")))
                crysis.add_child(Node.s32('r_gauge', i.data.get_int("r_gauge")))
                crysis.add_child(Node.s8('r_state', i.data.get_int("r_state")))
                play_log.add_child(crysis)

        pdata.add_child(item)
        pdata.add_child(course)
        pdata.add_child(hacker)
        pdata.add_child(play_log)

        customize = Node.void('customize')
        customize.add_child(Node.u16_array('custom', profile.get_int_array('custom', 16)))
        pdata.add_child(customize)

        tips = Node.void('tips')
        tips.add_child(Node.s32('last_tips', profile.get_int('last_tips')))
        pdata.add_child(tips)

        record = Node.void('record')
        scores = self.data.local.music.get_scores(self.game, self.version, userid)
        for i in scores:
            rec = Node.void('rec')
            rec.add_child(Node.s32('music_id', i.id))
            rec.add_child(Node.s32('note_level', i.chart))
            rec.add_child(Node.s32('play_count', i.plays))
            rec.add_child(Node.s32('clear_count', i.data.get_int('clear_count')))
            rec.add_child(Node.s32('best_gauge', i.data.get_int('gauge')))
            rec.add_child(Node.s32('best_score', i.points))
            rec.add_child(Node.s32('best_grade', i.data.get_int('grade')))
            rec.add_child(Node.s32('best_medal', i.data.get_int('medal')))
            record.add_child(rec)
        pdata.add_child(record)

        return root

    # Helper method to unformat the player profile into a ValidatedDict for the DB
    def unformat_player_profile(self, profile: Node) -> Profile:
        userid = self.data.local.user.from_extid(self.game, self.version, profile.child_value('account/usrid'))
        ret = Profile(self.game, self.version, profile.child_value('account/rid'), profile.child_value('account/usrid'))

        # Account
        next_tpc = int(profile.child_value('account/tpc')) + 1
        ret.replace_int('usrid', int(profile.child_value('account/usrid')))
        ret.replace_int('is_takeover', int(profile.child_value('account/is_takeover')))
        ret.replace_int('tpc', next_tpc)
        ret.replace_int('dpc', int(profile.child_value('account/dpc')))
        ret.replace_int('crd', int(profile.child_value('account/crd')))
        ret.replace_int('brd', int(profile.child_value('account/brd')))
        ret.replace_int('tdc', int(profile.child_value('account/tdc')))
        ret.replace_str('lid', profile.child_value('account/lid'))
        ret.replace_int('ver', int(profile.child_value('account/ver')))
        ret.replace_int('st', int(profile.child_value('account/st')))

        # Base
        ret.replace_str('name', profile.child_value('base/name'))
        ret.replace_int('brnk', int(profile.child_value('base/brnk')))
        ret.replace_int('bcnum', int(profile.child_value('base/bcnum')))
        ret.replace_int('lcnum', int(profile.child_value('base/lcnum')))
        ret.replace_int('volt', int(profile.child_value('base/volt')))
        ret.replace_int('gold', int(profile.child_value('base/gold')))
        ret.replace_int('lmid', int(profile.child_value('base/lmid')))
        ret.replace_int('lgrd', int(profile.child_value('base/lgrd')))
        ret.replace_int('lsrt', int(profile.child_value('base/lsrt')))
        ret.replace_int('ltab', int(profile.child_value('base/ltab')))
        ret.replace_int('splv', int(profile.child_value('base/splv')))
        ret.replace_int('pref', int(profile.child_value('base/pref')))
        ret.replace_int('lcid', int(profile.child_value('base/lcid')))
        ret.replace_int('hat', int(profile.child_value('base/hat')))

        # Items stored as achievements
        items = profile.child('item')
        if items is not None:
            for i in items.children:
                self.data.local.user.put_achievement(self.game, self.version, userid, i.child_value('id'), 
                f"item_{i.child_value('type')}", {"type": i.child_value('type'), "param": i.child_value('param'), 
                "count": i.child_value('count')})

        # Customize
        custom = profile.child_value('customize/custom')
        if custom is not None:
            customize = []
            for i in custom:
                customize.append(i)
            ret.replace_int_array('custom', 16, custom)
        
        # Beast Crysis and multiplayer data
        play_log = profile.child('play_log')

        if play_log is not None:
            for i in play_log.children:
                if i.name == "crysis":
                    self.data.local.user.put_achievement(self.game, self.version, userid, i.child_value('id'), 
                    "crysis", {"step": i.child_value('step'), "r_gauge": i.child_value('r_gauge'), 
                    "r_state": i.child_value('r_state')})

                elif i.name == "onmatch":
                    pass

        # Tips
        ret.replace_int('last_tips', profile.child_value('tips/last_tips'))

        # Beast hacker
        hacker = profile.child("hacker")
        for x in hacker.children:
            self.data.local.user.put_achievement(self.game, self.version, userid, x.child_value("id"), "hacker", {
                "state0": x.child_value("state0"), "state1": x.child_value("state1"), "state2": x.child_value("state2"), 
                "state3": x.child_value("state3"), "state4": x.child_value("state4")
            })
        return ret

    # First call when somebody cards in, returns the status of a few crossover events
    def handle_player2_start_request(self, request: Node, is_continue: bool = False) -> Node:
        userid = self.data.local.user.from_refid(self.game, self.version, request.child_value('rid'))
        player2 = Node.void('player2')
        play_id = 0

        if userid is not None:
            if not is_continue:
                self.data.local.lobby.put_play_session_info(
                    self.game,
                    self.version,
                    userid,
                    {
                        'ga': request.child_value('ga'),
                        'gp': request.child_value('gp'),
                        'la': request.child_value('la'),
                    },                    
                    "".join(str(e) + "." for e in request.child_value('ga'))[:-1],
                    request.child_value('gp'),
                    "".join(str(e) + "." for e in request.child_value('la'))[:-1],
                )

            info = self.data.local.lobby.get_play_session_info(
                self.game,
                self.version,
                userid,
            )
            
            if info is not None:
                play_id = info.get_int('id')

        # Session stuff, and resend global defaults
        player2.add_child(Node.s32('plyid', play_id))

        start_time = Node.u64('start_time', Time.now() * 1000)
        player2.add_child(start_time)

        # Crossover events
        # HAPPY☆SUMMER CAMPAIGN possibly?
        reflec_collabo = Node.bool('reflec_collabo', True)
        player2.add_child(reflec_collabo)

        # BeaSt pop'n tanabata matsuri possibly?
        pop_collabo = Node.bool('pop_collabo', True)
        player2.add_child(pop_collabo)

        # Floor Infection Part 20
        floor_infection = Node.void('floor_infection')
        player2.add_child(floor_infection)
        fi_event = Node.void('event')
        floor_infection.add_child(fi_event)
        infection_id = Node.s32('infection_id', 20)
        music_list = Node.s32('music_list', 7)
        is_complete = Node.bool('is_complete', True)
        fi_event.add_child(infection_id)
        fi_event.add_child(music_list)
        fi_event.add_child(is_complete)

        # If you played Museca 1+1/2 at launch you got rewards in BST and other games
        museca = Node.void('museca')
        player2.add_child(museca)
        is_play_museca =  Node.bool('is_play_museca', True)
        museca.add_child(is_play_museca)

        return player2
    
    # Called when carding in to get the player profile
    def handle_player2_read_request(self, request: Node) -> Node:
        refid = request.child_value('rid')
        userid = self.data.remote.user.from_refid(self.game, self.version, refid)
        profile = self.get_profile(userid)
        return self.format_player_profile(profile)

    # Called either when carding out or creating a new profile
    def handle_player2_write_request(self, request: Node) -> Node:
        refid = request.child_value('pdata/account/rid')
        extid = request.child_value('pdata/account/usrid')
        pdata = request.child('pdata')
        reply = Node.void('player2')        

        profile = self.unformat_player_profile(pdata)
        userid = self.data.remote.user.from_refid(self.game, self.version, refid) # Get the userid for the refid

        # The game always wants the extid sent back, so we only have to look it up if it's 0
        if extid == 0:            
            extid = self.data.local.user.get_extid(self.game, self.version, userid) # Get the extid for the profile we just saved
            profile.replace_int('usrid', extid) # Replace the extid in the profile with the one generated by butils
        
        self.put_profile(userid, profile) # Save the profile
        
        node_uid = Node.s32('uid', extid) # Send it back as a node
        reply.add_child(node_uid)

        return reply

    # Called whenever some kind of error happens. 
    def handle_pcb2_error_request(self, request: Node) -> Node:
        return Node.void('pcb2')

    # BST2 has to be special and have it's own boot method
    def handle_pcb2_boot_request(self, request: Node) -> Node:
        shop_id = ID.parse_machine_id(request.child_value('lid'))
        pcbid = self.data.local.machine.from_machine_id(shop_id)

        if pcbid is not None:
            machine = self.data.local.machine.get_machine(pcbid)
            machine_name = machine.name
            close = machine.data.get_bool('close')
            hour = machine.data.get_int('hour')
            minute = machine.data.get_int('minute')
        else:
            return None

        pcb2 = Node.void('pcb2')
        sinfo = Node.void('sinfo')
        pcb2.add_child(sinfo)

        sinfo.add_child(Node.string('nm', machine_name))
        sinfo.add_child(Node.bool('cl_enbl', close))
        sinfo.add_child(Node.u8('cl_h', hour))
        sinfo.add_child(Node.u8('cl_m', minute))

        return pcb2

    # Send a list of events and phases
    def handle_info2_common_request(self, request: Node) -> Node:
        info2 = Node.void('info2')
        info2.set_attribute('status', '0')

        event_ctrl = self.get_events()
        info2.add_child(event_ctrl)

        return info2

    # Called when a player registeres a new profile when they have an account
    def handle_player2_succeed_request(self, request: Node) -> Node:
        player2 = Node.void('player2')

        play = Node.bool('play', False)
        player2.add_child(play)

        data = Node.void('data')
        player2.add_child(data)        

        name = Node.string('name', "")
        data.add_child(name)

        record = Node.void('record')
        player2.add_child(record)

        hacker = Node.void('hacker')
        player2.add_child(hacker)

        phantom = Node.void('phantom')
        player2.add_child(phantom)
        return player2

    # Called during boot
    def handle_shop2_setting_write_request(self, request: Node) -> Node:
        shop2 = Node.void('shop2')
        #TODO: shop settings saving
        return shop2

    # Called after settings_write, not sure what it does
    def handle_info2_music_count_read_request(self, request: Node) -> Node:
        info2 = Node.void('info2')
        record = Node.void('record')
        record.add_child(Node.void('rec'))
        record.add_child(Node.void('rate'))
        info2.add_child(record)
        return info2
    
    # Called after music_count_read. Might have something to do with song popularity?
    def handle_info2_music_ranking_read_request(self, Request: Node) -> Node:
        info2 = Node.void('info2')
        ranking = Node.void('ranking')
        ranking.add_child(Node.void('count'))
        info2.add_child(ranking)
        return info2

    # Called on card out
    def handle_player2_end_request(self, request: Node) -> Node:
        self.data.local.lobby.destroy_play_session_info(self.game, self.version, 
            self.data.local.user.from_refid(self.game, self.version, request.child_value("rid")))
        return Node.void('player2')

    # Called after finishing a song
    def handle_player2_stagedata_write_request(self, request: Node) -> Node:
        userid = request.child_value('user_id')
        musicid = request.child_value('select_music_id')
        chartid = request.child_value('select_grade')
        location = self.get_machine_id()
        points = request.child_value('result_score')
        gauge = request.child_value('result_clear_gauge')
        max_combo = request.child_value('result_max_combo')
        grade = request.child_value('result_grade')
        medal = request.child_value('result_medal')
        fantastic_count = request.child_value('result_fanta')
        great_count = request.child_value('result_great')
        fine_count = request.child_value('result_fine')
        miss_count = request.child_value('result_miss')

        self.update_score(userid, musicid, chartid, location, points, gauge, 
        max_combo, grade, medal, fantastic_count, great_count, fine_count, miss_count)
        
        return Node.void('player2')

    # Called after finishing a song in a course
    def handle_player2_course_stage_data_write_request(self, request: Node) -> Node:
        userid = request.child_value('user_id')
        musicid = request.child_value('select_music_id')
        chartid = request.child_value('select_grade')
        location = self.get_machine_id()
        points = request.child_value('result_score')
        gauge = request.child_value('result_clear_gauge')
        max_combo = request.child_value('result_max_combo')
        grade = request.child_value('result_grade')
        medal = request.child_value('result_medal')
        fantastic_count = request.child_value('result_fanta')
        great_count = request.child_value('result_great')
        fine_count = request.child_value('result_fine')
        miss_count = request.child_value('result_miss')

        self.update_score(userid, musicid, chartid, location, points, gauge, 
        max_combo, grade, medal, fantastic_count, great_count, fine_count, miss_count)

        return Node.void('player2')
    
    # Called after finishing a course
    def handle_player2_course_data_write_request(self, request: Node) -> Node:
        return Node.void('player2')

    # Called frequently to see who's playing
    def handle_lobby2_get_lobby_list_request(self, request: Node) -> Node:
        lobby2 =  Node.void('lobby2')
        lobby2.add_child(Node.s32('interval_sec', 10))
        lobbies = self.data.local.lobby.get_all_lobbies(self.game, self.version)

        if lobbies is not None:
            for (user, lobby) in lobbies:
                e = Node.void('e')
                lobby2.add_child(e)
                e.add_child(Node.u16('mid', lobby.get_int('mid')))
                e.add_child(Node.u64('eatime', lobby.get_int('eatime')))

        return lobby2

    # Called to destroy a lobby after it's use
    def handle_lobby2_delete_request(self, request: Node) -> Node:
        self.data.local.lobby.destroy_lobby(request.child_value("eid"))
        return Node.void('lobby2')

    # Called when matching starts
    def handle_lobby2_entry_request(self, request: Node) -> Node:
        lobby2 = Node.void('lobby2')
        lobby2.add_child(Node.s32('interval', 120))
        lobby2.add_child(Node.s32('interval_p', 120))

        global_ip = "".join(str(e) + "." for e in request.child_value('e/ga'))[:-1],
        local_ip = "".join(str(e) + "." for e in request.child_value('e/la'))[:-1],
        session = self.data.local.lobby.get_play_session_info_by_ip(self.game, self.version, global_ip, local_ip)
        userid = 0
        requested_lobby_id = request.child_value('e/eid')
        lobby = None
        
        if userid is not None:            
            userid = session.get_int("userid")            

        if requested_lobby_id > 0:
            # Get the detales of the requested lobby
            lobby = self.data.local.lobby.get_lobby_by_id(self.game, self.version, requested_lobby_id)

        if lobby is None:
            # Make a new lobby
            self.data.local.lobby.put_lobby(
                self.game,
                self.version,
                userid,
                {
                    'ver': request.child_value('e/ver'),
                    'mid': request.child_value('e/mid'),
                    'rest': request.child_value('e/rest'),
                    'uid': request.child_value('e/uid'),
                    'mmode': request.child_value('e/mmode'),
                    'mg': request.child_value('e/mg'),
                    'mopt': request.child_value('e/mopt'),
                    'lid': request.child_value('e/lid'),
                    'sn': request.child_value('e/sn'),
                    'pref': request.child_value('e/pref'),
                    'eatime': request.child_value('e/eatime'),
                    'ga': request.child_value('e/ga'),
                    'gp': request.child_value('e/gp'),
                    'la': request.child_value('e/la'),
                }
            )

            lobby = self.data.local.lobby.get_lobby(self.game, self.version, userid)

        lobby2.add_child(Node.s32('eid', lobby.get_int('id')))
        e = Node.void('e')
        lobby2.add_child(e)
        e.add_child(Node.s32('eid', lobby.get_int('id')))
        e.add_child(Node.u8('ver', lobby.get_int('ver')))
        e.add_child(Node.u16('mid', lobby.get_int('mid')))
        e.add_child(Node.u8('rest', lobby.get_int('rest')))
        e.add_child(Node.s32('uid', lobby.get_int('mmode')))
        e.add_child(Node.s32('mmode', lobby.get_int('mmode')))
        e.add_child(Node.s16('mg', lobby.get_int('mg')))
        e.add_child(Node.s32('mopt', lobby.get_int('mopt')))        
        e.add_child(Node.string('lid', lobby.get_str('lid')))
        e.add_child(Node.string('sn', lobby.get_str('sn')))
        e.add_child(Node.u8('pref', lobby.get_int('pref')))
        e.add_child(Node.s16('eatime', lobby.get_int('eatime')))
        e.add_child(Node.u8_array('ga', lobby.get_int_array('ga', 4)))
        e.add_child(Node.u16('gp', lobby.get_int('gp')))
        e.add_child(Node.u8_array('la', lobby.get_int_array('la', 4)))
        
        return lobby2
    
    # Called when a player tries to continue another credit 
    def handle_player2_continue_request(self, request: Node) -> Node:
        return self.handle_player2_start_request(request, True)
    
    # Called when a user request an eamuse app screenshot
    def handle_info2_result_image_write_request(self, request: Node) -> Node:
        song: Song = self.data.local.music.get_song(self.game, self.version, request.child_value("music_id"),
        request.child_value("music_level"))

        diff_num = song.data.get_int("difficulty")
        
        grades = ["Red AAA", "AAA", "AA", "A", "B", "C", "D"]
        medals = ["No Play", "Failed", "Saved", "Cleared", "Full Combo", "Perfect"]

        card_data = {
            BroadcastConstants.PLAYER_NAME: request.child_value("player_name"),
            BroadcastConstants.SONG_NAME: request.child_value("music_title"),
            BroadcastConstants.ARTIST_NAME: request.child_value("artist_name"),
            BroadcastConstants.DIFFICULTY: request.child_value("music_level"),
            BroadcastConstants.DIFFICULTY_LEVEL: diff_num,
            BroadcastConstants.BEAST_RANK: request.child_value("beast_rank"),

            BroadcastConstants.SCORE: request.child_value("score"),
            BroadcastConstants.BEST_SCORE: request.child_value("best_score"),
            BroadcastConstants.GAUGE: float(request.child_value("gauge") / 10),
            BroadcastConstants.MEDAL: medals[request.child_value("medal")],
            BroadcastConstants.GRADE: grades[request.child_value("grade")],

            BroadcastConstants.MAX_COMBO: request.child_value("max_combo"),
            BroadcastConstants.FANTASTIC: request.child_value("fanta"),
            BroadcastConstants.GREAT: request.child_value("great"),
            BroadcastConstants.FINE: request.child_value("fine"),
            BroadcastConstants.MISS: request.child_value("miss"),            
        }

        self.data.triggers.broadcast_score(card_data, self.game, song)
        return Node.void("info2")
    
    # Called when matching
    def handle_player2_matching_data_load_request(self, request: Node) -> Node:
        root = Node.void('player_matching')
        data = Node.void('data')
        data.add_child(Node.s32('id', 0)) # player id?
        data.add_child(Node.bool('fl', False)) # First Local
        data.add_child(Node.bool('fo', False)) # First Online
        root.add_child(root)
        