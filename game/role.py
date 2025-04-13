from typing import Dict, Type
import random

# Roleクラス
class Role:
    def __init__(self, id: int, name: str, team: str):
        self.id = id
        self.name = name
        self.team = team
    
    def species(self) -> str:
        return self.team

    def seer_result(self) -> str:
        return "村人"

    def medium_result(self) -> str:
        return "人狼ではない"

    def action_description(self) -> str:
        return ""

    def has_night_action(self, turn: int) -> bool:
        return False

    def __str__(self):
        return self.name
    
# 役職クラス
class 村人(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="村人", team="村人")

class 人狼(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="人狼", team="人狼")

    def seer_result(self) -> str:
        return "人狼"

    def medium_result(self) -> str:
        return "人狼"

    def action_description(self) -> str:
        return "襲撃対象"

    def has_night_action(self, turn: int) -> bool:
        return turn > 1

class 占い師(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="占い師", team="村人")

    def action_description(self) -> str:
        return "占う対象"

    def has_night_action(self, turn: int) -> bool:
        return True

class 偽占い師(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="偽占い師", team="村人")

    def action_description(self) -> str:
        return "占う対象"

    def has_night_action(self, turn: int) -> bool:
        return True

    def fake_seer_result(self) -> str:
        return random.choice(["人狼", "人狼ではない"])

class 霊媒師(Role):
    def __init__(self, id: int):
        super().__init__(id, "霊媒師", "村人")

    def seer_result(self) -> str:
        return "村人"

    def medium_result(self) -> str:
        return "人狼ではない"

    def has_night_action(self, turn: int) -> bool:
        return turn > 1

class 騎士(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="騎士", team="村人")

    def action_description(self) -> str:
        return "守る対象"

    def has_night_action(self, turn: int) -> bool:
        return turn > 1

class 猫又(Role):
    """猫又の役職クラス"""
    def __init__(self, id: int):
        super().__init__(id=id, name="猫又", team="村人")

class 狂人(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="狂人", team="人狼")
    
    def species(self):
        return "村人"
    def seer_result(self):
        return "村人"

class 狂信者(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="狂信者", team="人狼")
    
    def species(self):
        return "村人"
    def seer_result(self):
        return "村人"

class 妖狐(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="妖狐", team="妖狐")
    def seer_result(self) -> str:
        return "村人"

class 背徳者(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="背徳者", team="妖狐")
    def species(self):
        return "村人"
    def seer_result(self) -> str:
        return "村人"

# 役職を生成するための辞書
role_dict: Dict[str, Type[Role]] = {
    "村人": 村人,
    "人狼": 人狼,
    "占い師": 占い師,
    "霊媒師": 霊媒師,
    "騎士": 騎士,
    "猫又": 猫又,
    "狂人": 狂人,
    "狂信者": 狂信者,
    "妖狐": 妖狐,
    "背徳者": 背徳者,
    "偽占い師": 偽占い師,
}
