from typing import Optional, Type, Dict, Any
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
        self.death_info: Optional[Dict[str, Any]] = None # 死亡情報を追加

    def assign_role(self, role: Role, id: int):
        """
        プレイヤーに役職を割り当てる
        """
        if self.role is not None:
            raise ValueError(f"{self.name} さんには既に役職 {self.role} が割り当てられています。")
        self.role = role
        self.id = id

    def kill(self, turn: int, reason: str):
        """
        プレイヤーを死亡させ、死亡情報を記録する。
        reason: "attack", "execute", "curse", "suicide"
        """
        if self.alive:
            self.alive = False
            self.death_info = {"turn": turn, "reason": reason}
            # print(f"DEBUG - Player.kill: {self.name} killed at turn {turn} by {reason}") # デバッグ用

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
        # 死因を取得 (表示用)
        status = "生存"
        if not self.alive and self.death_info:
            reason_ja = {
                "attack": "襲撃",
                "execute": "処刑",
                "curse": "呪殺",
                "suicide": "後追死"
            }.get(self.death_info["reason"], "不明")
            status = f"{self.death_info['turn']}日目 {reason_ja}"
        elif not self.alive:
            status = "死亡(詳細不明)"
            
        if reveal_role and self.role:
            return f"{self.name} [{self.role.name}] ({status})"
        else:
            return f"{self.name} ({status})"