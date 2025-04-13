# werewolf_streamlit/tests/test_player.py
import pytest

# テスト対象と関連モジュールを import (絶対パスで)
from game.player import Player
from game.role import Role, 村人, 人狼, 騎士, 妖狐 # テスト用にいくつか Role をインポート

# --- Player クラスのテスト ---

def test_player_initialization():
    """プレイヤー初期化時の属性を確認"""
    player = Player("Alice")
    assert player.name == "Alice"
    assert player.alive is True
    assert player.role is None
    assert player.id is None
    assert player.death_info is None # death_info も確認

def test_player_assign_role():
    """プレイヤーへの役職割り当てを確認"""
    player = Player("Bob")
    role_instance = 村人(id=1)
    player.assign_role(role_instance, id=1)
    assert player.role == role_instance
    assert player.id == 1
    # 既に役職がある場合にエラーが出るか
    with pytest.raises(ValueError):
        player.assign_role(人狼(id=2), id=2)

def test_player_kill():
    """プレイヤーを死亡させる処理を確認"""
    player = Player("Charlie")
    assert player.is_alive() is True
    player.kill(turn=1, reason="attack") # 1日目
    assert player.is_alive() is False
    assert player.death_info == {"turn": 1, "reason": "attack"} # 1日目
    # 既に死んでいるプレイヤーを再度 kill しても状態は変わらない
    death_info_before = player.death_info
    player.kill(turn=2, reason="execute") # 2日目
    assert player.is_alive() is False
    assert player.death_info == death_info_before # death_info は上書きされない

def test_player_str_representation():
    """プレイヤーの文字列表現を確認"""
    player_alive = Player("Dave")
    player_alive.assign_role(騎士(id=3), id=3)
    player_dead = Player("Eve")
    player_dead.assign_role(妖狐(id=4), id=4)
    player_dead.kill(turn=1, reason="curse") # 1日目

    # 通常時 (役職非表示)
    assert str(player_alive) == "Dave (生存)"
    assert str(player_dead) == "Eve (1日目 呪殺)" # 1日目

    # 役職表示時
    assert player_alive.__str__(reveal_role=True) == "Dave [騎士] (生存)"
    assert player_dead.__str__(reveal_role=True) == "Eve [妖狐] (1日目 呪殺)" # 1日目 