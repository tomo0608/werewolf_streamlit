# werewolf_streamlit/tests/test_role.py
import pytest

# テスト対象のモジュールを import (絶対パスで)
from game.role import Role, 村人, 人狼, 占い師, 偽占い師, 霊媒師, 騎士, 狂人, 狂信者, 妖狐, 背徳者

# --- 各役職の基本的な属性テスト ---

def test_villager_attributes():
    role = 村人(0)
    assert role.name == "村人"
    assert role.team == "村人"
    assert role.species() == "村人"
    assert role.seer_result() == "村人"
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == ""
    assert role.has_night_action(1) is False
    assert role.has_night_action(2) is False

def test_werewolf_attributes():
    role = 人狼(1)
    assert role.name == "人狼"
    assert role.team == "人狼"
    assert role.species() == "人狼"
    assert role.seer_result() == "人狼"
    assert role.medium_result() == "人狼"
    assert role.action_description() == "襲撃対象"
    assert role.has_night_action(1) is False # 初日はアクションなし
    assert role.has_night_action(2) is True

def test_seer_attributes():
    role = 占い師(2)
    assert role.name == "占い師"
    assert role.team == "村人"
    assert role.species() == "村人"
    assert role.seer_result() == "村人" # 自分を占った場合など
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == "占う対象"
    assert role.has_night_action(1) is True
    assert role.has_night_action(2) is True

def test_fake_seer_attributes():
    role = 偽占い師(3)
    assert role.name == "偽占い師"
    assert role.team == "村人" # team は村人
    assert role.species() == "村人"
    assert role.seer_result() == "村人"
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == "占う対象（偽）"
    assert role.has_night_action(1) is True
    assert role.has_night_action(2) is True

def test_medium_attributes():
    role = 霊媒師(4)
    assert role.name == "霊媒師"
    assert role.team == "村人"
    assert role.species() == "村人"
    assert role.seer_result() == "村人"
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == ""
    assert role.has_night_action(1) is False # アクションUIは不要
    assert role.has_night_action(2) is False

def test_knight_attributes():
    role = 騎士(5)
    assert role.name == "騎士"
    assert role.team == "村人"
    assert role.species() == "村人"
    assert role.seer_result() == "村人"
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == "守る対象"
    assert role.has_night_action(1) is False # 初日はアクションなし
    assert role.has_night_action(2) is True

def test_madman_attributes():
    role = 狂人(6)
    assert role.name == "狂人"
    assert role.team == "人狼" # 陣営は人狼
    assert role.species() == "村人" # 種族は村人
    assert role.seer_result() == "村人"
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == ""
    assert role.has_night_action(1) is False
    assert role.has_night_action(2) is False

def test_fanatic_attributes():
    role = 狂信者(7)
    assert role.name == "狂信者"
    assert role.team == "人狼"
    assert role.species() == "村人"
    assert role.seer_result() == "村人"
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == ""
    assert role.has_night_action(1) is False
    assert role.has_night_action(2) is False

def test_fox_attributes():
    role = 妖狐(8)
    assert role.name == "妖狐"
    assert role.team == "妖狐"
    assert role.species() == "妖狐"
    assert role.seer_result() == "村人" # 占われたら死亡
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == ""
    assert role.has_night_action(1) is False
    assert role.has_night_action(2) is False

def test_immoralist_attributes():
    role = 背徳者(9)
    assert role.name == "背徳者"
    assert role.team == "妖狐"
    assert role.species() == "村人" # 種族は村人
    assert role.seer_result() == "村人"
    assert role.medium_result() == "人狼ではない"
    assert role.action_description() == ""
    assert role.has_night_action(1) is False
    assert role.has_night_action(2) is False

# --- (オプション) より詳細なテストケース ---
# 例: 占い結果や霊媒結果が他の役職に対して正しく機能するかなど
# def test_seer_results_on_others():
#     seer = 占い師(0)
#     wolf = 人狼(1)
#     fox = 妖狐(2)
#     # 実際には Player オブジェクト経由で role を取得することになるが、
#     # Role クラス単体のテストとしてはこれで十分
#     assert seer.seer_result() == "村人" # 自分自身 (あるいは別の村人)
#     # assert wolf.seer_result() == "人狼" # Roleクラスのメソッド呼び出しなので、上記 werewolf_attributes でカバーされている
#     # assert fox.seer_result() == "村人" # 上記 fox_attributes でカバーされている 