from typing import Dict, Type

# Roleクラス
class Role:
    def __init__(self, id: int, name: str, team: str):
        self.id = id
        self.name = name
        self.team = team
    
    def species(self) -> str:
        # 基本はチームと同じだが、狂人などはオーバーライドする
        return self.team

    def seer_result(self) -> str:
        # 基本はチームと同じだが、人狼や妖狐などはオーバーライドする
        return "村人" # デフォルトは村人判定

    def medium_result(self) -> str:
        # 霊媒結果は基本的に「人狼」か「人狼ではない」
        return "人狼ではない"

    def action_description(self) -> str:
        # 夜アクション時の選択肢ラベル。なければ空文字
        return ""

    def has_night_action(self, turn: int) -> bool:
        # Streamlit UI でアクション選択が必要か
        return False # デフォルトは不要

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
        return turn > 1 # 初日以外はアクションあり

class 占い師(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="占い師", team="村人")

    def action_description(self) -> str:
        return "占う対象"

    def has_night_action(self, turn: int) -> bool:
        return True # 常にアクションあり

class 偽占い師(Role):
    def __init__(self, id: int):
        # team は村人だが、実際は人狼陣営として扱われることもあるので注意
        super().__init__(id=id, name="偽占い師", team="村人")

    def action_description(self) -> str:
        return "占う対象（偽）"

    def has_night_action(self, turn: int) -> bool:
        return True # 常にアクションあり

class 霊媒師(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="霊媒師", team="村人")
    # 霊媒師は結果を見るだけで、能動的なアクション選択はUI上不要なため
    # has_night_action は False のまま

class 騎士(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="騎士", team="村人")

    def action_description(self) -> str:
        return "守る対象"

    def has_night_action(self, turn: int) -> bool:
        return turn > 1 # 初日以外はアクションあり

class 狂人(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="狂人", team="人狼")
    
    def species(self):
        return "村人" # 狂人は村人として数える
    def seer_result(self):
        return "村人" # 狂人は村人判定

class 狂信者(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="狂信者", team="人狼")
    
    def species(self):
        return "村人" # 狂信者は村人として数える
    def seer_result(self):
        return "村人" # 狂信者は村人判定

class 妖狐(Role):
    def __init__(self, id: int):
        super().__init__(id=id, name="妖狐", team="妖狐")
    def seer_result(self) -> str:
        return "村人" # 実際は呪殺される

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
    "狂人": 狂人,
    "狂信者": 狂信者,
    "妖狐": 妖狐,
    "背徳者": 背徳者,
    "偽占い師": 偽占い師,
}
