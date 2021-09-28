from bemani.common import Profile
from bemani.backend.base import Base
from bemani.backend.core import CoreHandler, CardManagerHandler, PASELIHandler
from bemani.common import ValidatedDict, Model, GameConstants, Time
from bemani.data import Data, Score, Machine, UserID
from bemani.protocol import Node

class BSTBase(CoreHandler, CardManagerHandler, PASELIHandler, Base):
    game = GameConstants.BST

    # Helper method that enables events based on the server config
    def get_events(self) -> Node:
        root = Node.void('event_ctrl')
        # Enable everything until I can understand what each event is
        for x in range(41):
            for y in range(26):
                data = Node.void('data')
                data.add_child(Node.s32('type', x))
                data.add_child(Node.s32('phase', y))
                root.add_child(data)
        return root
        # TODO: Add events

    def update_score(self, extid, songid, chartid, loc, points, gauge, 
    max_combo, grade, medal, fanta_count, great_count, fine_count, miss_count) -> None:
        butils_userid = self.data.local.user.from_extid(self.game, self.version, extid)
        old_score = self.data.local.music.get_score(self.game, self.version, butils_userid, songid, chartid)

        if old_score is not None: 
            new_record = old_score.points < points
        else:
             new_record = True
        new_points = max(old_score.points, points)

        new_loc = loc
        # Only update the location if it's a new high score
        if not new_record: 
            new_loc = old_score.location

        new_data = old_score.data

        new_gauge = max(new_data.get_float('gauge'), gauge)
        new_data.replace_float('gauge', new_gauge)

        new_max_combo = max(new_data.get_int('max_combo'), max_combo)
        new_data.replace_float('max_combo', new_max_combo)

        # Grades get better as their value decreases
        new_grade = min(new_data.get_int('grade'), grade)
        new_data.replace_int('grade', new_grade)

        new_medal = max(new_data.get_int('medal'))
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

    def unformat_player_profile(self, profile: Node) -> Profile:
        return None

    def format_player_profile(self, profile: Profile) -> Node:
        return None