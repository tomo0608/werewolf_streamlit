# werewolf_streamlit/tests/test_player.py
import pytest

# テスト対象と関連モジュールを import (絶対パスで)
from game.player import Player
from game.role import Role, 村人, 人狼 # テスト用にいくつか Role をインポート

# --- Player クラスのテスト ---

def test_player_initialization():
    """プレイヤー初期化時の属性を確認"""
    player = Player("Alice")
    assert player.name == "Alice"
    assert player.alive is True
    assert player.role is None
    assert player.id is None

def test_player_assign_role():
    """役職割り当てが正しく行われるか"""
    player = Player("Bob")
    villager_role = 村人(0) # インスタンス化して渡す
    player.assign_role(villager_role, 0) # ID も渡す

    assert isinstance(player.role, Role)
    assert player.role.name == "村人"
    assert player.id == 0

def test_player_kill():
    """kill メソッドで生存状態が変わるか"""
    player = Player("Charlie")
    assert player.alive is True
    player.kill()
    assert player.alive is False

def test_player_str_representation():
    """__str__ メソッドの出力を確認"""
    player_alive = Player("Dave")
    player_dead = Player("Eve")
    player_dead.kill()

    # 役職割り当て前
    assert str(player_alive) == "Dave (生存)"
    assert str(player_dead) == "Eve (死亡)"

    # 役職割り当て後 (村人)
    villager_role = 村人(1)
    player_alive.assign_role(villager_role, 1)
    assert str(player_alive) == "Dave (生存)" # 通常時は役職非表示
    assert player_alive.__str__(reveal_role=True) == "Dave [村人] (生存)"

    # 役職割り当て後 (人狼、死亡)
    werewolf_role = 人狼(2)
    player_dead.assign_role(werewolf_role, 2)
    assert str(player_dead) == "Eve (死亡)"
    assert player_dead.__str__(reveal_role=True) == "Eve [人狼] (死亡)" 