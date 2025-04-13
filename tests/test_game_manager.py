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
    gm.players[0].kill(turn=1, reason="test")
    alive_players_after_kill = gm.get_alive_players()
    assert len(alive_players_after_kill) == len(PLAYER_NAMES) - 1
    assert gm.players[0] not in alive_players_after_kill

# --- check_victory のテスト ---

def test_check_victory_villager_win(game_manager_basic):
    """村人勝利: 人狼全滅、妖狐なし"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=村人, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 村人(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]): # 最初の3人だけ使う
        p.assign_role(roles_map[i], i)
    players[2].kill(turn=1, reason="test")
    gm.players = players[:3] # GameManagerが参照するリストを更新
    gm.check_victory() # 勝利判定を実行して内部状態を更新
    assert gm.victory_team == "村人"

def test_check_victory_werewolf_win(game_manager_basic):
    """人狼勝利: 村人と人狼が同数、妖狐なし"""
    gm = game_manager_basic
    players = gm.players
    # Alice=人狼, Bob=村人
    roles_map = {0: 人狼(0), 1: 村人(1)}
    for i, p in enumerate(players[:2]): # 最初の2人だけ使う
        p.assign_role(roles_map[i], i)
    gm.players = players[:2]
    gm.check_victory()
    assert gm.victory_team == "人狼"

def test_check_victory_fox_win_no_wolves(game_manager_basic):
    """妖狐勝利: 人狼全滅、妖狐あり"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=妖狐, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 妖狐(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    players[2].kill(turn=1, reason="test")
    gm.players = players[:3]
    gm.check_victory()
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
        p.assign_role(roles_map[p.name], i)

    night_actions = {
        "Alice": {"type": "attack", "target": "Charlie"},
        "Bob": {"type": "attack", "target": "Charlie"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    # 夜のアクションを解決
    results = gm.resolve_night_actions(night_actions)
    victim_names = results.get("victims", [])

    # 検証
    assert victim_names == ["Charlie"] # Charlieのみが犠牲者
    assert gm.last_night_victim_name_list == ["Charlie"] # 内部状態も更新されているか
    assert results.get("immoral_suicides") == [] # 後追い自殺はなし
    assert players[0].alive is True 
    assert players[1].alive is True 
    assert players[2].alive is False # Charlie (村人) - 死亡
    assert players[2].death_info == {"turn": 1, "reason": "attack"} # ★ death_info を確認
    assert players[3].alive is True 
    assert players[4].alive is True 

def test_resolve_night_actions_attack_protected(game_manager_basic):
    """騎士に守られて襲撃が失敗するケース"""
    gm = game_manager_basic
    players = gm.players
    roles_map = {0: 人狼(0), 1: 騎士(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
         if i in roles_map:
              p.assign_role(roles_map[i], i)
         else:
             p.assign_role(村人(i), i)

    gm.turn = 2 

    night_actions = {
        "Alice": {"type": "attack", "target": "Charlie"},
        "Bob": {"type": "guard", "target": "Charlie"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    results = gm.resolve_night_actions(night_actions)
    victim_names = results.get("victims", [])

    assert victim_names == [] # 犠牲者はいない
    assert gm.last_night_victim_name_list == []
    assert results.get("immoral_suicides") == []
    assert players[0].alive is True
    assert players[1].alive is True
    assert players[2].alive is True # Charlie - 生存
    assert players[3].alive is True
    assert players[4].alive is True

def test_resolve_night_actions_seer_kills_fox(game_manager_basic):
    """占い師が妖狐を占って呪殺するケース"""
    gm = game_manager_basic
    players = gm.players
    roles_map = {0: 占い師(0), 1: 妖狐(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "seer", "target": "Bob"}, 
        "Bob": {"type": "none"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    results = gm.resolve_night_actions(night_actions)
    victim_names = results.get("victims", [])

    assert victim_names == ["Bob"] # Bob (妖狐) が死亡
    assert gm.last_night_victim_name_list == ["Bob"]
    assert results.get("immoral_suicides") == []
    assert players[0].alive is True  
    assert players[1].alive is False # Bob (妖狐)
    assert players[1].death_info == {"turn": 1, "reason": "curse"} # ★ death_info を確認
    assert players[2].alive is True  

def test_resolve_night_actions_seer_kills_last_fox_with_immoralist(game_manager_basic):
    """占い師が最後の妖狐を呪殺し、背徳者が後追いするケース"""
    gm = game_manager_basic
    players = gm.players
    roles_map = {0: 占い師(0), 1: 妖狐(1), 2: 背徳者(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "seer", "target": "Bob"}, 
        "Bob": {"type": "none"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    results = gm.resolve_night_actions(night_actions)
    victim_names = results.get("victims", [])
    immoral_suicides = results.get("immoral_suicides", [])

    assert sorted(victim_names) == sorted(["Bob", "Charlie"]) # Bob(妖狐)とCharlie(背徳者)が死亡
    assert sorted(gm.last_night_victim_name_list) == sorted(["Bob", "Charlie"])
    assert sorted(immoral_suicides) == sorted(["Charlie"]) # 後追い自殺者リストを確認
    assert players[0].alive is True  
    assert players[1].alive is False # Bob (妖狐)
    assert players[1].death_info == {"turn": 1, "reason": "curse"} # ★ death_info を確認
    assert players[2].alive is False # Charlie (背徳者)
    assert players[2].death_info == {"turn": 1, "reason": "suicide"} # ★ death_info を確認

def test_resolve_night_actions_wolf_attacks_fox(game_manager_basic):
    """人狼が妖狐を襲撃して失敗するケース"""
    gm = game_manager_basic
    players = gm.players
    roles_map = {0: 人狼(0), 1: 妖狐(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "attack", "target": "Bob"}, 
        "Bob": {"type": "none"},
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    results = gm.resolve_night_actions(night_actions)
    victim_names = results.get("victims", [])

    assert victim_names == [] # 犠牲者はいない
    assert gm.last_night_victim_name_list == []
    assert results.get("immoral_suicides") == []
    assert players[0].alive is True  
    assert players[1].alive is True  # Bob (妖狐)
    assert players[2].alive is True  

def test_resolve_night_actions_combined_seer_attack(game_manager_basic):
    """占いと襲撃が同時に行われるケース"""
    gm = game_manager_basic
    players = gm.players
    roles_map = {0: 占い師(0), 1: 人狼(1), 2: 村人(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)

    night_actions = {
        "Alice": {"type": "seer", "target": "Charlie"}, 
        "Bob": {"type": "attack", "target": "Dave"},    
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    results = gm.resolve_night_actions(night_actions)
    victim_names = results.get("victims", [])

    assert victim_names == ["Dave"] # Daveのみ死亡
    assert gm.last_night_victim_name_list == ["Dave"]
    assert results.get("immoral_suicides") == []
    assert players[0].alive is True  # Alice
    assert players[1].alive is True  # Bob
    assert players[2].alive is True  # Charlie
    assert players[3].alive is False # Dave
    assert players[3].death_info == {"turn": 1, "reason": "attack"} # ★ death_info を確認
    assert players[4].alive is True  # Eve

def test_resolve_night_actions_guard_vs_curse(game_manager_basic):
    """騎士が妖狐を守ろうとするが、占い師に呪殺されるケース"""
    gm = game_manager_basic
    players = gm.players
    # Alice=占い師, Bob=騎士, Charlie=妖狐
    roles_map = {0: 占い師(0), 1: 騎士(1), 2: 妖狐(2), 3: 村人(3), 4: 村人(4)}
    for i, p in enumerate(players):
        p.assign_role(roles_map[i], i)
    gm.turn = 2 # 騎士が動けるように

    night_actions = {
        "Alice": {"type": "seer", "target": "Charlie"},  # AliceがCharlie(妖狐)を占う
        "Bob": {"type": "guard", "target": "Charlie"},   # BobがCharlieを守る
        "Charlie": {"type": "none"},
        "Dave": {"type": "none"},
        "Eve": {"type": "none"},
    }

    results = gm.resolve_night_actions(night_actions)
    victim_names = results.get("victims", [])

    assert victim_names == ["Charlie"] # Charlie(妖狐)は呪殺される
    assert gm.last_night_victim_name_list == ["Charlie"]
    assert results.get("immoral_suicides") == []
    assert players[0].alive is True  # Alice
    assert players[1].alive is True  # Bob
    assert players[2].alive is False # Charlie
    assert players[2].death_info == {"turn": 2, "reason": "curse"} # ★ death_info を確認 (turn=2)

# --- execute_day_vote のテスト ---

def test_execute_day_vote_simple(game_manager_roles_assigned):
    """単純な処刑が成功するケース"""
    gm = game_manager_roles_assigned 
    votes = Counter({"Alice": 3, "Bob": 1}) # Aliceが最多票

    result = gm.execute_day_vote(votes)
    executed_name = result.get("executed")

    assert executed_name == "Alice"
    assert gm.last_executed_name == "Alice"
    assert result.get("immoral_suicides") == []
    assert result.get("error") is None
    # Alice の生存状態を確認
    alice = next(p for p in gm.players if p.name == "Alice")
    assert alice.alive is False
    assert alice.death_info == {"turn": 1, "reason": "execute"} # ★ death_info を確認

def test_execute_day_vote_tie(game_manager_roles_assigned):
    """同票の場合、ランダムで処刑されるケース（どちらかが処刑される）"""
    gm = game_manager_roles_assigned
    votes = Counter({"Alice": 2, "Bob": 2, "Charlie": 1})
    possible_executed = ["Alice", "Bob"]

    result = gm.execute_day_vote(votes)
    executed_name = result.get("executed")

    assert executed_name in possible_executed
    assert gm.last_executed_name == executed_name
    assert result.get("immoral_suicides") == []
    assert result.get("error") is None
    executed_player = next(p for p in gm.players if p.name == executed_name)
    assert executed_player.alive is False
    assert executed_player.death_info == {"turn": 1, "reason": "execute"} # ★ death_info を確認

def test_execute_day_vote_no_votes(game_manager_roles_assigned):
    """投票がない場合、誰も処刑されないケース"""
    gm = game_manager_roles_assigned
    votes = Counter() 

    result = gm.execute_day_vote(votes)
    executed_name = result.get("executed")

    assert executed_name is None
    assert gm.last_executed_name is None
    assert result.get("immoral_suicides") == []
    assert result.get("error") is None
    # 全員の生存を確認
    assert all(p.alive for p in gm.get_alive_players())

def test_execute_day_vote_fox_and_immoralist(game_manager_basic):
    """妖狐が処刑され、背徳者が後追いするケース"""
    gm = game_manager_basic
    players = gm.players
    roles_map = {0: 妖狐(0), 1: 背徳者(1), 2: 村人(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    gm.players = players[:3]

    votes = Counter({"Alice": 2, "Charlie": 1})

    result = gm.execute_day_vote(votes)
    executed_name = result.get("executed")
    immoral_suicides = result.get("immoral_suicides", [])

    assert executed_name == "Alice"
    assert sorted(immoral_suicides) == sorted(["Bob"]) # Bobが後追い
    assert gm.last_executed_name == "Alice"
    assert result.get("error") is None
    alice = next(p for p in gm.players if p.name == "Alice")
    bob = next(p for p in gm.players if p.name == "Bob")
    charlie = next(p for p in gm.players if p.name == "Charlie")

    assert alice.alive is False # 妖狐は処刑
    assert alice.death_info == {"turn": 1, "reason": "execute"} # ★ death_info を確認
    assert bob.alive is False   # 背徳者は後追い
    assert bob.death_info == {"turn": 1, "reason": "suicide"} # ★ death_info を確認
    assert charlie.alive is True # 村人は生存

# --- get_game_results のテスト ---
def test_get_game_results_villager_win(game_manager_basic):
    """村人勝利時のゲーム結果が正しいか"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=村人, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 村人(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    players[2].kill(turn=1, reason="test") # ★ kill に引数追加
    gm.players = players[:3] # GameManagerが参照するリストを更新
    gm.check_victory() # 勝利判定を実行して内部状態を更新

    results = gm.get_game_results()

    assert gm.victory_team == "村人" # gm.victory_team で確認
    assert len(results) == 3
    # Alice (村人, 生存, 勝利)
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "🏆" and results[0]["生死"] == "最終日生存"
    # Bob (村人, 生存, 勝利)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "🏆" and results[1]["生死"] == "最終日生存"
    # Charlie (人狼, 死亡, 敗北)
    assert results[2]["名前"] == "Charlie" and results[2]["勝利"] == "" and results[2]["生死"] == "1日目 不明により死亡" # 理由を "不明" に戻す

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
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "🏆" and results[0]["生死"] == "最終日生存"
    # Bob (村人, 生存, 敗北)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "" and results[1]["生死"] == "最終日生存"

def test_get_game_results_fox_win_no_wolves(game_manager_basic):
    """妖狐勝利（人狼全滅）時のゲーム結果が正しいか"""
    gm = game_manager_basic
    players = gm.players
    # Alice=村人, Bob=妖狐, Charlie=人狼(死亡)
    roles_map = {0: 村人(0), 1: 妖狐(1), 2: 人狼(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    players[2].kill(turn=1, reason="test") # ★ kill に引数追加 (仮で処刑死)
    gm.players = players[:3]
    gm.check_victory()

    results = gm.get_game_results()

    assert gm.victory_team == "妖狐" # gm.victory_team で確認
    assert len(results) == 3
    # Alice (村人, 生存, 敗北)
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "" and results[0]["生死"] == "最終日生存"
    # Bob (妖狐, 生存, 勝利)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "🏆" and results[1]["生死"] == "最終日生存"
    # Charlie (人狼, 死亡, 敗北)
    assert results[2]["名前"] == "Charlie" and results[2]["勝利"] == "" and results[2]["生死"] == "1日目 不明により死亡" # 理由を "不明" に戻す

def test_get_game_results_fox_win_executed(game_manager_basic):
    """妖狐処刑後の勝利判定（村人勝利）をテストする。
    新しいルールでは、妖狐処刑時は妖狐チームの勝利にはならない。
    """
    gm = game_manager_basic
    players = gm.players
    # Alice=妖狐, Bob=背徳者, Charlie=村人
    roles_map = {0: 妖狐(0), 1: 背徳者(1), 2: 村人(2)}
    for i, p in enumerate(players[:3]):
        p.assign_role(roles_map[i], i)
    gm.players = players[:3]

    # 妖狐を処刑する
    gm.execute_day_vote(Counter({"Alice": 1})) # Alice(妖狐)が処刑され、Bob(背徳者)も後追い
    # 勝利判定（人狼も妖狐もいないので村人勝利になるはず）
    victory_info = gm.check_victory()

    assert victory_info is not None
    assert victory_info["team"] == "村人" 
    assert gm.victory_team == "村人"

    results = gm.get_game_results()

    assert len(results) == 3
    # Alice (妖狐, 死亡, 敗北)
    assert results[0]["名前"] == "Alice" and results[0]["勝利"] == "" and results[0]["生死"] == "1日目 処刑により死亡" # これは正しい
    # Bob (背徳者, 死亡, 敗北)
    assert results[1]["名前"] == "Bob" and results[1]["勝利"] == "" and results[1]["生死"] == "1日目 後追死により死亡" # これは正しい
    # Charlie (村人, 生存, 勝利)
    assert results[2]["名前"] == "Charlie" and results[2]["勝利"] == "🏆" and results[2]["生死"] == "最終日生存" # これは正しい 