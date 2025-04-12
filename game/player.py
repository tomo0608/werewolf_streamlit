from typing import Optional, Type
from .role import Role

class Player:
    def __init__(self, name: str):
        """
        プレイヤーを初期化する
        """
        self.name: str = name
        self.role: Optional[Role] = None
        self.alive: bool = True
        self.id: Optional[int] = None # ID を初期化

    def assign_role(self, role: Role, id: int): # 引数の型ヒントを修正 (Type[Role] -> Role)
        """
        プレイヤーに役職を割り当てる
        """
        if self.role is not None:
            raise ValueError(f"{self.name} さんには既に役職 {self.role} が割り当てられています。")
        self.role = role # インスタンスをそのまま代入
        self.id = id # ID もここで設定

    def kill(self):
        """
        プレイヤーを死亡させる
        """
        self.alive = False

    def is_alive(self) -> bool:
        """
        プレイヤーが生存しているかを確認する
        """
        return self.alive

    def __str__(self, reveal_role: bool = False) -> str:
        """
        プレイヤーの情報を文字列として返す
        - reveal_role: True の場合、役職を表示する
        """
        status = "生存" if self.alive else "死亡" # 日本語に変更
        if reveal_role and self.role:
            return f"{self.name} [{self.role.name}] ({status})" # 役職表示形式を修正
        else:
            return f"{self.name} ({status})" # 通常時の形式を修正