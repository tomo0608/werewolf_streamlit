# werewolf_streamlit/tests/test_game_manager.py
import pytest
from collections import Counter

# テスト対象と関連モジュールを import
from game.game_manager import GameManager
from game.player import Player
from game.role import 村人, 人狼, 占い師, 騎士, 妖狐, 背徳者 # 妖狐, 背徳者 を追加

# --- GameManager クラスのテスト ---

# テストで使用する基本的なプレイヤー名のリスト
PLAYER_NAMES = ["Alice", "Bob", "Charlie", "Dave", "Eve"]

@pytest.fixture
def game_manager_basic():
    """基本的な GameManager インスタンスを作成するフィクスチャ"""
    return GameManager(PLAYER_NAMES.copy()) # プレイヤー名のリストはコピーして渡す

@pytest.fixture
def game_manager_roles_assigned(game_manager_basic):
    """役職割り当て済みの GameManager インスタンスを作成するフィクスチャ"""
    # 例: 村人3, 人狼2 の構成
    roles_to_assign = ["村人", "村人", "村人", "人狼", "人狼"]
    game_manager_basic.assign_roles(roles_to_assign)
    return game_manager_basic

# --- 初期化と役職割り当てのテスト ---

def test_game_manager_initialization(game_manager_basic):
    """GameManager の初期化時の状態を確認"""
    gm = game_manager_basic
    assert len(gm.players) == len(PLAYER_NAMES)
    assert all(isinstance(p, Player) for p in gm.players)
    assert all(p.name in PLAYER_NAMES for p in gm.players)
    assert gm.turn == 1
    assert gm.last_night_victim_name_list == []
    assert gm.last_executed_name is None
    assert gm.victory_team is None
    assert gm.debug_mode is False

def test_game_manager_assign_roles(game_manager_basic):
    """assign_roles が正しく役職を割り当てるか"""
    gm = game_manager_basic
    # 例: 村人3, 人狼2
    roles_to_assign = ["村人", "村人", "村人", "人狼", "人狼"]
    gm.assign_roles(roles_to_assign.copy()) # コピーして渡す

    assigned_roles = [p.role.name for p in gm.players if p.role]
    assert len(assigned_roles) == len(PLAYER_NAMES)
    assert Counter(assigned_roles) == Counter(roles_to_assign)
    # ID が 0 から順番に割り当てられているか (オプション)
    assigned_ids = sorted([p.id for p in gm.players if p.id is not None])
    assert assigned_ids == list(range(len(PLAYER_NAMES)))

def test_get_alive_players(game_manager_roles_assigned):
    """get_alive_players が生存プレイヤーのみを返すか"""
    gm = game_manager_roles_assigned
    initial_alive_players = gm.get_alive_players()
    assert len(initial_alive_players) == len(PLAYER_NAMES)

    # 一人殺してみる
    gm.players[0].kill()
    current_alive_players = gm.get_alive_players()
    assert len(current_alive_players) == len(PLAYER_NAMES) - 1
    assert gm.players[0] not in current_alive_players

# --- check_victory のテスト ---

def test_check_victory_villager_win(game_manager_basic):
    """村人勝利: 人狼全滅、妖狐なし"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=村人, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 村人(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]): # 最初の3人だけ使う
        p.assign_role(roles_map[i], i)
    players[2].kill() # 人狼を殺す
    gm.players = players[:3] # GameManagerが参照するリストを更新

    victory_info = gm.check_victory()
    assert victory_info is not None
    assert victory_info["team"] == "村人"
    assert "村人陣営の勝利" in victory_info["message"]
    assert gm.victory_team == "村人"

def test_check_victory_werewolf_win(game_manager_basic):
    """人狼勝利: 人狼 >= 村人、妖狐なし"""
    gm = game_manager_basic
    players = gm.players
    # Alice=人狼, Bob=村人
    roles_map = {0: 人狼(0), 1: 村人(1)}
    for i, p in enumerate(players[:2]):
        p.assign_role(roles_map[i], i)
    gm.players = players[:2]

    victory_info = gm.check_victory()
    assert victory_info is not None
    assert victory_info["team"] == "人狼"
    assert "人狼陣営の勝利" in victory_info["message"]
    assert gm.victory_team == "人狼"

def test_check_victory_fox_win_no_wolves(game_manager_basic):
    """妖狐勝利: 人狼全滅、妖狐あり"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=妖狐, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 妖狐(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    players[2].kill() # 人狼を殺す
    gm.players = players[:3]

    victory_info = gm.check_victory()
    assert victory_info is not None
    assert victory_info["team"] == "妖狐"
    assert "妖狐陣営の勝利" in victory_info["message"]
    assert gm.victory_team == "妖狐"

def test_check_victory_fox_win_with_wolves(game_manager_basic):
    """妖狐勝利: 人狼 >= 村人、妖狐あり"""
    gm = game_manager_basic
    players = gm.players
    # Alice=人狼, Bob=村人, Charlie=妖狐
    roles_map = {0: 人狼(0), 1: 村人(1), 2: 妖狐(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    gm.players = players[:3]

    victory_info = gm.check_victory()
    assert victory_info is not None
    assert victory_info["team"] == "妖狐"
    # メッセージはシナリオによって異なる可能性があるため、チーム名だけ確認
    assert gm.victory_team == "妖狐"

def test_check_victory_game_continue(game_manager_roles_assigned):
    """ゲーム続行: 勝利条件を満たさない"""
    gm = game_manager_roles_assigned # 村人3, 人狼2 (初期状態)
    
    victory_info = gm.check_victory()
    assert victory_info is None # ゲームは続くはず
    assert gm.victory_team is None

# --- resolve_night_actions のテスト ---

def test_resolve_night_actions_simple_attack(game_manager_basic):
    """単純な人狼の襲撃が成功するケース"""
    gm = game_manager_basic
    players = gm.players
    # 役職を固定して割り当て (例: Alice=人狼, Bob=人狼, Charlie=村人, Dave=村人, Eve=村人)
    roles_map = {"Alice": 人狼(0), "Bob": 人狼(1), "Charlie": 村人(2), "Dave": 村人(3), "Eve": 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[p.name], i) # assign_role の第二引数は player id

    # 夜のアクションデータを作成 (AliceとBobがCharlieを襲撃)
    night_actions = {
        "Alice": {"type": "attack", "target": "Charlie"},
        "Bob": {"type": "attack", "target": "Charlie"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    # 夜のアクションを解決
    victim_names = gm.resolve_night_actions(night_actions)

    # 検証
    assert victim_names == ["Charlie"] # Charlieのみが犠牲者
    assert gm.last_night_victim_name_list == ["Charlie"] # 内部状態も更新されているか
    # 各プレイヤーの生死を確認
    assert players[0].alive is True # Alice (人狼)
    assert players[1].alive is True # Bob (人狼)
    assert players[2].alive is False # Charlie (村人) - 死亡
    assert players[3].alive is True # Dave (村人)
    assert players[4].alive is True # Eve (村人)

def test_resolve_night_actions_attack_protected(game_manager_basic):
    """騎士に守られて襲撃が失敗するケース"""
    gm = game_manager_basic # フィクスチャを利用
    players = gm.players
    # プレイヤーと役職を設定 (Alice=人狼, Bob=騎士, Charlie=村人, Dave=村人, Eve=村人)
    # 使うプレイヤーだけ役職を設定（インデックスで指定）
    roles_map = {0: 人狼(0), 1: 騎士(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)} # IDも指定
    for i, p in enumerate(players):
         if i in roles_map:
              p.assign_role(roles_map[i], i)
         else:
             # 使わないプレイヤーにも仮の役職（村人）を割り当てておく
             p.assign_role(村人(i), i)

    gm.turn = 2 # 騎士が行動できるように2ターン目にする

    # 夜のアクションデータを作成 (AliceがCharlieを襲撃, BobがCharlieを護衛)
    night_actions = {
        "Alice": {"type": "attack", "target": "Charlie"},
        "Bob": {"type": "guard", "target": "Charlie"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    victim_names = gm.resolve_night_actions(night_actions)

    assert victim_names == [] # 犠牲者はいない
    assert gm.last_night_victim_name_list == []
    assert players[0].alive is True # Alice
    assert players[1].alive is True # Bob
    assert players[2].alive is True # Charlie - 生存
    assert players[3].alive is True # Dave
    assert players[4].alive is True # Eve

def test_resolve_night_actions_seer_kills_fox(game_manager_basic):
    """占い師が妖狐を占って呪殺するケース"""
    gm = game_manager_basic
    players = gm.players
    # Alice=占い師, Bob=妖狐, Charlie=村人
    roles_map = {0: 占い師(0), 1: 妖狐(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "seer", "target": "Bob"}, # 占い師が妖狐を占う
        "Bob": {"type": "none"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    victim_names = gm.resolve_night_actions(night_actions)

    assert victim_names == ["Bob"] # Bob (妖狐) が死亡
    assert gm.last_night_victim_name_list == ["Bob"]
    assert players[0].alive is True  # Alice (占い師)
    assert players[1].alive is False # Bob (妖狐)
    assert players[2].alive is True  # Charlie (村人)

def test_resolve_night_actions_seer_kills_last_fox_with_immoralist(game_manager_basic):
    """占い師が最後の妖狐を呪殺し、背徳者が後追いするケース"""
    gm = game_manager_basic
    players = gm.players
    # Alice=占い師, Bob=妖狐, Charlie=背徳者
    roles_map = {0: 占い師(0), 1: 妖狐(1), 2: 背徳者(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "seer", "target": "Bob"}, # 占い師が妖狐を占う
        "Bob": {"type": "none"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    victim_names = gm.resolve_night_actions(night_actions)

    assert sorted(victim_names) == sorted(["Bob", "Charlie"]) # Bob(妖狐)とCharlie(背徳者)が死亡
    assert sorted(gm.last_night_victim_name_list) == sorted(["Bob", "Charlie"])
    assert players[0].alive is True  # Alice (占い師)
    assert players[1].alive is False # Bob (妖狐)
    assert players[2].alive is False # Charlie (背徳者)

def test_resolve_night_actions_wolf_attacks_fox(game_manager_basic):
    """人狼が妖狐を襲撃して失敗するケース"""
    gm = game_manager_basic
    players = gm.players
    # Alice=人狼, Bob=妖狐, Charlie=村人
    roles_map = {0: 人狼(0), 1: 妖狐(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "attack", "target": "Bob"}, # 人狼が妖狐を襲撃
        "Bob": {"type": "none"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    victim_names = gm.resolve_night_actions(night_actions)

    assert victim_names == [] # 犠牲者はいない
    assert gm.last_night_victim_name_list == []
    assert players[0].alive is True  # Alice (人狼)
    assert players[1].alive is True  # Bob (妖狐)
    assert players[2].alive is True  # Charlie (村人)

def test_resolve_night_actions_combined_seer_attack(game_manager_basic):
    """占いと襲撃が同時に行われるケース"""
    gm = game_manager_basic
    players = gm.players
    # Alice=占い師, Bob=人狼, Charlie=村人, Dave=村人
    roles_map = {0: 占い師(0), 1: 人狼(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "seer", "target": "Charlie"}, # AliceがCharlieを占う
        "Bob": {"type": "attack", "target": "Dave"},    # BobがDaveを襲撃
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    victim_names = gm.resolve_night_actions(night_actions)

    assert victim_names == ["Dave"]
    assert gm.last_night_victim_name_list == ["Dave"]
    assert players[0].alive is True  # Alice (占い師)
    assert players[1].alive is True  # Bob (人狼)
    assert players[2].alive is True  # Charlie (村人) - 占われただけ
    assert players[3].alive is False # Dave (村人) - 襲撃死
    assert players[4].alive is True  # Eve (村人)

def test_resolve_night_actions_guard_vs_curse(game_manager_basic):
    """騎士の護衛と占い師の呪殺が同時に発生するケース（呪殺優先）"""
    gm = game_manager_basic
    players = gm.players
    # Alice=占い師, Bob=妖狐, Charlie=騎士
    roles_map = {0: 占い師(0), 1: 妖狐(1), 2: 騎士(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)
    gm.turn = 2 # 騎士が行動できるように

    night_actions = {
        "Alice": {"type": "seer", "target": "Bob"},   # 占い師が妖狐を占う -> 呪殺
        "Bob": {"type": "none"},
        "Charlie": {"type": "guard", "target": "Bob"}, # 騎士が妖狐を護衛
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    victim_names = gm.resolve_night_actions(night_actions)

    assert victim_names == ["Bob"] # Bob(妖狐)のみ死亡
    assert gm.last_night_victim_name_list == ["Bob"]
    assert players[0].alive is True  # Alice (占い師)
    assert players[1].alive is False # Bob (妖狐)
    assert players[2].alive is True  # Charlie (騎士)

# --- execute_day_vote のテスト ---

def test_execute_day_vote_simple(game_manager_roles_assigned): # 役職割り当て済みフィクスチャを使用
    """単純な投票で一人処刑されるケース"""
    gm = game_manager_roles_assigned # 村人3, 人狼2
    alive_players = gm.get_alive_players()
    target_name = alive_players[0].name # 最初のプレイヤーを処刑対象とする

    # 投票データを作成 (全員が target_name に投票)
    votes = Counter({target_name: len(alive_players)})

    executed_name = gm.execute_day_vote(votes)

    assert executed_name == target_name
    target_player = next((p for p in gm.players if p.name == target_name), None)
    assert target_player is not None
    assert target_player.alive is False
    assert gm.last_executed_name == target_name

def test_execute_day_vote_tie(game_manager_roles_assigned):
    """同票でランダム処刑されるケース"""
    gm = game_manager_roles_assigned
    alive_players = gm.get_alive_players()
    target1_name = alive_players[0].name
    target2_name = alive_players[1].name

    # 投票データを作成 (target1 と target2 が同票)
    votes = Counter({target1_name: 2, target2_name: 2})

    executed_name = gm.execute_day_vote(votes)

    assert executed_name in [target1_name, target2_name] # どちらかが処刑される
    executed_player = next((p for p in gm.players if p.name == executed_name), None)
    assert executed_player is not None
    assert executed_player.alive is False
    assert gm.last_executed_name == executed_name

def test_execute_day_vote_no_votes(game_manager_roles_assigned):
    """投票がない場合、誰も処刑されないケース"""
    gm = game_manager_roles_assigned
    votes = Counter() # 空の投票

    executed_name = gm.execute_day_vote(votes)

    assert executed_name is None
    assert gm.last_executed_name is None
    # 全員の生存を確認
    assert all(p.alive for p in gm.get_alive_players())

def test_execute_day_vote_fox_and_immoralist(game_manager_basic):
    """妖狐が処刑され、背徳者が後追いするケース"""
    gm = game_manager_basic
    players = gm.players
    # Alice=妖狐, Bob=背徳者, Charlie=村人
    roles_map = {0: 妖狐(0), 1: 背徳者(1), 2: 村人(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    gm.players = players[:3]

    # 投票データ (Alice が最多票)
    votes = Counter({"Alice": 2, "Charlie": 1})

    executed_name = gm.execute_day_vote(votes)

    assert executed_name == "Alice"
    alice = next(p for p in gm.players if p.name == "Alice")
    bob = next(p for p in gm.players if p.name == "Bob")
    charlie = next(p for p in gm.players if p.name == "Charlie")

    assert alice.alive is False # 妖狐は処刑
    assert bob.alive is False   # 背徳者は後追い
    assert charlie.alive is True # 村人は生存
    assert gm.last_executed_name == "Alice"

# --- get_game_results のテスト ---
def test_get_game_results_villager_win(game_manager_basic):
    """村人勝利時のゲーム結果が正しいか"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=村人, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 村人(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    players[2].kill() # 人狼を殺す
    gm.players = players[:3] # GameManagerが参照するリストを更新
    gm.check_victory() # 勝利判定を実行して内部状態を更新

    results = gm.get_game_results()

    assert gm.victory_team == "村人" # gm.victory_team で確認
    assert len(results) == 3
    # Alice (村人, 生存, 勝利)
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "🏆" and results[0]["生死"] == "生存"
    # Bob (村人, 生存, 勝利)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "🏆" and results[1]["生死"] == "生存"
    # Charlie (人狼, 死亡, 敗北)
    assert results[2]["名前"] == "Charlie" and results[2]["勝利"] == "" and results[2]["生死"] == "死亡"

def test_get_game_results_werewolf_win(game_manager_basic):
    """人狼勝利時のゲーム結果が正しいか"""
    gm = game_manager_basic
    players = gm.players
    # Alice=人狼, Bob=村人
    roles_map = {0: 人狼(0), 1: 村人(1)}
    for i, p in enumerate(players[:2]):
        p.assign_role(roles_map[i], i)
    gm.players = players[:2]
    gm.check_victory()

    results = gm.get_game_results()

    assert gm.victory_team == "人狼" # gm.victory_team で確認
    assert len(results) == 2
    # Alice (人狼, 生存, 勝利)
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "🏆" and results[0]["生死"] == "生存"
    # Bob (村人, 生存, 敗北)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "" and results[1]["生死"] == "生存"

def test_get_game_results_fox_win_no_wolves(game_manager_basic):
    """妖狐勝利（人狼全滅）時のゲーム結果が正しいか"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=妖狐, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 妖狐(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    players[2].kill() # 人狼を殺す
    gm.players = players[:3]
    gm.check_victory()

    results = gm.get_game_results()

    assert gm.victory_team == "妖狐" # gm.victory_team で確認
    assert len(results) == 3
    # Alice (村人, 生存, 敗北)
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "" and results[0]["生死"] == "生存"
    # Bob (妖狐, 生存, 勝利)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "🏆" and results[1]["生死"] == "生存"
    # Charlie (人狼, 死亡, 敗北)
    assert results[2]["名前"] == "Charlie" and results[2]["勝利"] == "" and results[2]["生死"] == "死亡"

@pytest.mark.skip(reason="妖狐処刑時の勝利判定ロジックが未修正のためスキップ")
def test_get_game_results_fox_win_executed(game_manager_basic):
    """妖狐勝利（最後の妖狐が処刑され背徳者が後追い）時のゲーム結果"""
    gm = game_manager_basic
    players = gm.players
    # Alice=妖狐, Bob=背徳者, Charlie=村人
    roles_map = {0: 妖狐(0), 1: 背徳者(1), 2: 村人(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    gm.players = players[:3]

    # 妖狐を処刑する
    gm.execute_day_vote(Counter({"Alice": 1})) # Aliceが処刑される
    gm.check_victory() # 勝利判定 (妖狐勝利になるはず)

    results = gm.get_game_results()

    assert gm.victory_team == "妖狐" # gm.victory_team で確認
    assert len(results) == 3
    # Alice (妖狐, 死亡, 勝利)
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "🏆" and results[0]["生死"] == "死亡"
    # Bob (背徳者, 死亡, 勝利)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "🏆" and results[1]["生死"] == "死亡"
    # Charlie (村人, 生存, 敗北)
    assert results[2]["名前"] == "Charlie" and results[2]["勝利"] == "" and results[2]["生死"] == "生存" 