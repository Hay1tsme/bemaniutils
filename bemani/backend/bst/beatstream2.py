from bemani.data.mysql.machine import MachineData
from bemani.data.mysql.user import UserData
from bemani.common import Profile, ValidatedDict
from bemani.backend.bst.base import BSTBase
from bemani.common import VersionConstants, Time
from bemani.backend.ess import EventLogHandler
from bemani.protocol import Node

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

    def supports_paseli(self) -> bool:
        if self.model.dest != 'J':
            return False
        else:
            return True    

    # Helper method to formay a player profile as a Node that the game will accept
    def format_player_profile(self, profile: Profile) -> Node:
        userid = self.data.local.user.from_extid(self.game, self.version, profile.get_dict('account').get_int('usrid'))
        root = Node.void("player2")
        root.set_attribute('status', '0')
        pdata = Node.void('pdata')
        root.add_child(pdata)
        
        account = Node.void('account')
        account.add_child(Node.s32('usrid', profile.get_dict('account').get_int('usrid')))
        account.add_child(Node.s32('is_takeover', profile.get_dict('account').get_int('is_takeover')))
        account.add_child(Node.s32('plyid', profile.get_dict('account').get_int('plyid')))
        account.add_child(Node.s32('continue_cnt', profile.get_dict('account').get_int('continue_cnt')))
        account.add_child(Node.s32('tpc', profile.get_dict('account').get_int('tpc')))
        account.add_child(Node.s32('dpc', profile.get_dict('account').get_int('dpc')))
        account.add_child(Node.s32('crd', profile.get_dict('account').get_int('crd')))
        account.add_child(Node.s32('brd', profile.get_dict('account').get_int('brd')))
        account.add_child(Node.s32('tdc', profile.get_dict('account').get_int('tdc')))
        account.add_child(Node.string('rid', profile.get_dict('account').get_str('rid')))
        account.add_child(Node.string('lid', profile.get_dict('account').get_str('lid')))
        account.add_child(Node.u8('mode', profile.get_dict('account').get_int('mode')))
        account.add_child(Node.s16('ver', profile.get_dict('account').get_int('ver')))
        account.add_child(Node.bool('pp', profile.get_dict('account').get_bool('pp')))
        account.add_child(Node.bool('ps', profile.get_dict('account').get_bool('ps')))
        account.add_child(Node.s16('pay', profile.get_dict('account').get_int('pay')))
        account.add_child(Node.s16('pay_pc', profile.get_dict('account').get_int('pay_pc')))
        account.add_child(Node.u64('st', profile.get_dict('account').get_int('st')))
        account.add_child(Node.s32('intrvld',0))
        account.add_child(Node.u64('pst', 0))
        account.add_child(Node.bool('ea', 1))
        pdata.add_child(account)

        base = Node.void('base')
        base.add_child(Node.string('name', profile.get_dict('base').get_str('name')))
        base.add_child(Node.s8('brnk', profile.get_dict('base').get_int('brnk')))
        base.add_child(Node.s8('bcnum', profile.get_dict('base').get_int('bcnum')))
        base.add_child(Node.s8('lcnum', profile.get_dict('base').get_int('lcnum')))
        base.add_child(Node.s32('volt', profile.get_dict('base').get_int('volt')))
        base.add_child(Node.s32('gold', profile.get_dict('base').get_int('gold')))
        base.add_child(Node.s32('lmid', profile.get_dict('base').get_int('lmid')))
        base.add_child(Node.s8('lgrd', profile.get_dict('base').get_int('lgrd')))
        base.add_child(Node.s8('lsrt', profile.get_dict('base').get_int('lsrt')))
        base.add_child(Node.s8('ltab', profile.get_dict('base').get_int('ltab')))        
        base.add_child(Node.s8('splv', profile.get_dict('base').get_int('splv')))
        base.add_child(Node.s8('pref', profile.get_dict('base').get_int('pref')))
        base.add_child(Node.s32('lcid', profile.get_dict('base').get_int('lcid')))
        base.add_child(Node.s32('hat', profile.get_dict('base').get_int('hat')))
        pdata.add_child(base)

        survey = Node.void('survey')
        survey.add_child(Node.s8('motivate', 0))
        pdata.add_child(survey)

        pdata.add_child(Node.void('opened'))
        
        item = Node.void('item')
        achievements = self.data.local.game.get_achievements(self.game, userid)
        for i in achievements:
            if i.type[:5] == "type_":
                info = Node.void('info')
                info.add_child(Node.s32('type', i.type[5:]))
                info.add_child(Node.s32('id', i.id))
                info.add_child(Node.s32('param', i.data.get_int('param', 0)))
                info.add_child(Node.s32('count', i.data.get_int('count', 0)))
                item.add_child(info)
        pdata.add_child(item)

        customize = Node.void('customize')
        customize.add_child(Node.u16_array('custom', profile.get_int_array('customize', 16)))
        pdata.add_child(customize)

        tips = Node.void('tips')
        tips.add_child(Node.s32('last_tips', profile.get_int('last_tips')))
        pdata.add_child(tips)

        hacker = Node.void('hacker') 
        info = Node.void('info')
        info.add_child(Node.s32('id', -2))
        info.add_child(Node.s8('state0', 1))
        info.add_child(Node.s8('state1', 25))
        info.add_child(Node.s8('state2', 0))
        info.add_child(Node.s8('state3', 0))
        info.add_child(Node.s8('state4', 0))
        info.add_child(Node.u64('update_time', 0))
        hacker.add_child(info) 
        pdata.add_child(hacker)

        play_log = Node.void('play_log')
        pdata.add_child(play_log)

        bisco = Node.void('bisco')
        pinfo = Node.void('pinfo')
        pinfo.add_child(Node.s32('bnum', 0))
        pinfo.add_child(Node.s32('jbox', 0))
        bisco.add_child(pinfo)
        pdata.add_child(bisco)

        record = Node.void('record')
        scores = self.data.local.music.get_scores(self.game, 2, userid)
        for i in scores:
            rec = Node.void('rec')
            rec.add_child(Node.s32('music_id', i.id))
            rec.add_child(Node.s32('note_level', 0))
            rec.add_child(Node.s32('play_count', i.plays))
            rec.add_child(Node.s32('clear_count', i.data.get_int('clear_count')))
            rec.add_child(Node.s32('best_gauge', i.data.get_int('best_gauge')))
            rec.add_child(Node.s32('best_score', i.points))
            rec.add_child(Node.s32('best_grade', i.data.get_int('best_grade')))
            rec.add_child(Node.s32('best_medal', i.data.get_int('best_medal')))
            record.add_child(rec)
        pdata.add_child(record)

        pdata.add_child(Node.void('course')) # TODO: Figure out what kind of data the game wants from courses
        print(root)

        return root

    # Helper method to unformat the player profile into a ValidatedDict for the DB
    def unformat_player_profile(self, profile: Node) -> Profile:
        userid = self.data.local.user.from_extid(self.game, self.version, profile.child_value('account/usrid'))
        ret = Profile(self.game, self.version, profile.child_value('account/rid'), profile.child_value('account/usrid'))

        # Name handled seperatly for the frontend
        ret.replace_str('name', profile.child_value('base/name')) #ＨＡＹ１ＴＳＭＥ

        # Account
        ret.get_dict('account').replace_int('usrid', profile.child_value('account/usrid'))
        ret.get_dict('account').replace_int('is_takeover', profile.child_value('account/is_takeover'))
        ret.get_dict('account').replace_int('plyid', profile.child_value('account/plyid'))
        ret.get_dict('account').replace_int('continue_cnt', profile.child_value('account/continue_cnt'))
        ret.get_dict('account').replace_int('tpc', profile.child_value('account/tpc'))
        ret.get_dict('account').replace_int('crd', profile.child_value('account/crd'))
        ret.get_dict('account').replace_int('brd', profile.child_value('account/brd'))
        ret.get_dict('account').replace_int('tdc', profile.child_value('account/tdc'))
        ret.get_dict('account').replace_str('rid', profile.child_value('account/rid'))
        ret.get_dict('account').replace_str('lid', profile.child_value('account/lid'))
        ret.get_dict('account').replace_int('mode', profile.child_value('account/mode'))
        ret.get_dict('account').replace_int('ver', profile.child_value('account/ver'))
        ret.get_dict('account').replace_bool('pp', profile.child_value('account/pp'))
        ret.get_dict('account').replace_bool('ps', profile.child_value('account/ps'))
        ret.get_dict('account').replace_int('pay', profile.child_value('account/pay'))
        ret.get_dict('account').replace_int('pay_pc', profile.child_value('account/pay_pc'))
        ret.get_dict('account').replace_int('st', profile.child_value('account/st'))

        # Base
        ret.get_dict('base').replace_int('brnk', profile.child_value('base/brnk'))
        ret.get_dict('base').replace_int('bcnum', profile.child_value('base/bcnum'))
        ret.get_dict('base').replace_int('lcnum', profile.child_value('base/lcnum'))
        ret.get_dict('base').replace_int('volt', profile.child_value('base/volt'))
        ret.get_dict('base').replace_int('gold', profile.child_value('base/gold'))
        ret.get_dict('base').replace_int('lmid', profile.child_value('base/lmid'))
        ret.get_dict('base').replace_int('lgrd', profile.child_value('base/lgrd'))
        ret.get_dict('base').replace_int('lsrt', profile.child_value('base/lsrt'))
        ret.get_dict('base').replace_int('ltab', profile.child_value('base/ltab'))
        ret.get_dict('base').replace_int('splv', profile.child_value('base/splv'))
        ret.get_dict('base').replace_int('pref', profile.child_value('base/pref'))
        ret.get_dict('base').replace_int('lcid', profile.child_value('base/lcid'))
        ret.get_dict('base').replace_int('hat', profile.child_value('base/hat'))

        # Items stored as achievements
        items = profile.child('item')
        #if items is not None:
        #    for i in items.children:
        #        self.data.local.game.put_achievement(self.game, userid, i.child_value('info/id'), 
        #        f"item_{i.child_value('info/type')}", {"param": i.child_value('info/param'), "count": i.child_value('info/count')})

        # Customize
        custom = profile.child_value('customize/custom')
        if custom is not None:
            customize = []
            for i in custom:
                customize.append(i)
            ret.replace_int_array('customize', 16, custom)

        # Tips
        ret.replace_int('last_tips', profile.child_value('tips/last_tips'))

        # Courses
        courses = profile.child('course')
        if courses is not None:
            course = []
            for i in courses.children:
                course.append(i.child_value('info/course_id'))
            ret.replace_int_array('course', course)
        
        # Hacker and playlog aren't supported for now
        return ret

    # First call when somebody cards in, returns the status of a few crossover events
    def handle_player2_start_request(self, request: Node) -> Node:
        player2 = Node.void('player2')

        plytime = Node.s32('plyid', 0)
        player2.add_child(plytime)

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
        is_play_museca =  Node.bool('is_play_museca', 1)
        museca.add_child(is_play_museca)

        return player2
    
    # Called when carding in to get the player profile
    def handle_player2_read_request(self, request: Node) -> Node:
        refid = request.child_value('rid')
        userid = self.data.remote.user.from_refid(self.game, self.version, refid)
        profile = self.get_profile(userid)
        return self.format_player_profile(profile)

    # Called either when carding out or creating a new profile
    def handle_player2_write_request(self, request: Node) -> Node: # TODO: Test changes here
        refid = request.child_value('pdata/account/rid')
        extid = request.child_value('pdata/account/usrid')
        pdata = request.child('pdata')
        reply = Node.void('player2')        

        profile = self.unformat_player_profile(pdata)
        userid = self.data.remote.user.from_refid(self.game, self.version, refid) # Get the userid for the refid
        self.put_profile(userid, profile) # Save the profile

        # The game always wants the extid sent back, so we only have to look it up if it's 0
        if extid == 0:            
            extid = self.data.local.user.get_extid(self.game, self.version, userid) # Get the extid for the profile we just saved
            profile.get_dict('account').replace_int('usrid', extid) # Replace the extid in the profile with the one generated by butils
            self.put_profile(userid, profile) # Save the profile with the new extid
        
        node_uid = Node.s32('uid', extid) # Send it back as a node
        reply.add_child(node_uid)

        return reply

    # Called whenever some kind of error happens. 
    def handle_pcb2_error_request(self, request: Node) -> Node:
        pcb2 = Node.void('pcb2')
        pcb2.set_attribute('status', '0')
        return pcb2

    # BST2 has to be special and have it's own boot method
    def handle_pcb2_boot_request(self, request: Node) -> Node:
        machine = self.data.local.machine.get_machine(self.config['machine']['pcbid'])
        arcade = self.data.local.machine.get_arcade(machine.arcade)
        pcb2 = Node.void('pcb2')
        pcb2.set_attribute('status', '0')
        sinfo = Node.void('sinfo')
        pcb2.add_child(sinfo)
        
        sinfo_nm = Node.string('nm', arcade.name) # TODO: Send saved shop name
        sinfo_cl_enbl = Node.bool('cl_enbl', True)
        sinfo_cl_h = Node.u8('cl_h', 0)
        sinfo_cl_m = Node.u8('cl_m', 0)

        sinfo.add_child(sinfo_nm)
        sinfo.add_child(sinfo_cl_enbl)
        sinfo.add_child(sinfo_cl_h)
        sinfo.add_child(sinfo_cl_m)

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
        player2 = Node.void('player2')
        return player2

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
        return Node.void('player2')
    
    # Called after finishing a course
    def handle_player2_course_data_write_request(self, request: Node) -> Node:
        return Node.void('player2')

    # Called frequently to see who's playing what I think.
    def handle_lobby2_get_lobby_list_request(self, request: Node) -> Node:
        return Node.void('lobby2')

    # Called when matching starts
    def handle_lobby2_entry_request(self, request: Node) -> Node:
        return Node.void('lobby2')
    
    # Called when a player tries to continue another credit 
    def handle_player2_continue_request(self, request: Node) -> Node:
        return self.handle_player2_start_request(request) #It just wants the start request.
        # Hoping this won't cause issues
        