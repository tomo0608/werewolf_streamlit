import random
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from collections import Counter

# werewolf_streamlit 内の Player と Role を import
from .player import Player
from .role import role_dict, Role # role_dict と Role クラス自体も使う可能性あり

class GameManager:
    def __init__(self, player_names:List[str], debug_mode: bool = False):
        """
        ゲーム管理クラスの初期化
        - プレイヤーを初期化
        - ゲーム状態を初期化
        - デバッグモードを設定
        """

        # プレイヤーの初期化 (streamlit 内の Player を使用)
        self.players = [Player(name) for name in player_names]
        self.debug_mode = debug_mode # デバッグモードフラグを保持

        # ゲーム状態
        self.turn = 1  # 現在のターン数
        self.last_night_victim_name_list:List[str] = [] # 昨晩の犠牲者
        self.last_executed_name:Optional[str] = None  # 昨日処刑されたプレイヤー
        self.victory_team:Optional[str] = None  # 勝利チーム

    def assign_roles(self, roles: List[str]):
        """
        プレイヤーに役職を割り当てる
        """
        random.shuffle(roles)
        for id, (player, role_name) in enumerate(zip(self.players, roles)):
            # streamlit 内の role_dict を使用
            player.assign_role(role_dict[role_name](id), id)

    def get_alive_players(self) -> List[Player]: # 戻り値の型を修正
        """
        生存しているプレイヤーのリストを取得
        """
        return [player for player in self.players if player.alive]

    def check_victory(self) -> Optional[Dict[str, str]]:
        """
        勝利条件をチェックし、ゲームが終了したか判定する。
        ゲームが終了していれば、勝利チーム名とメッセージを含む辞書を返す。
        ゲームが続いていれば None を返す。
        ルール：村人or人狼勝利時に生存妖狐がいれば妖狐勝利。
        """
        alive_players = self.get_alive_players()
        wolves = [player for player in alive_players if player.role.species() == "人狼"]
        villagers = [player for player in alive_players if player.role.species() == "村人"]
        foxes = [player for player in alive_players if player.role.species() == "妖狐"]

        determined_victory_team: Optional[str] = None
        determined_victory_message: Optional[str] = None

        # 1. 村人陣営の勝利条件チェック (人狼全滅)
        villager_win_condition_met = len(wolves) == 0

        # 2. 人狼陣営の勝利条件チェック (人狼数 >= 村人陣営数)
        werewolf_win_condition_met = len(wolves) >= len(villagers)

        # 3. 勝利条件が満たされた場合の処理
        if villager_win_condition_met or werewolf_win_condition_met:
            # 3a. 生存している妖狐がいるか？
            if len(foxes) > 0:
                determined_victory_team = "妖狐"
                if villager_win_condition_met:
                    determined_victory_message = "人狼は全滅しましたが、妖狐が生き残ったため妖狐陣営の勝利です！"
                else: # werewolf_win_condition_met
                    determined_victory_message = "人狼が村人の人数以上となりましたが、妖狐が生き残ったため妖狐陣営の勝利です！"
            # 3b. 生存している妖狐がいない場合
            else:
                if villager_win_condition_met:
                    determined_victory_team = "村人"
                    determined_victory_message = "人狼は全滅しました。村人陣営の勝利です！"
                elif werewolf_win_condition_met:
                    determined_victory_team = "人狼"
                    determined_victory_message = "人狼が村人の人数以上となりました。人狼陣営の勝利です！"

        # 勝利条件が満たされた場合、内部状態を更新して結果を返す
        if determined_victory_team and determined_victory_message:
            self.victory_team = determined_victory_team
            return {"team": determined_victory_team, "message": determined_victory_message}
        
        # ゲーム続行の場合
        return None

    def get_game_results(self) -> List[Dict[str, Any]]:
        """ゲーム終了時の結果情報をリストとして返す。"""
        results = []
        has_winner = self.victory_team is not None
        
        # 死因を日本語に変換する辞書
        reason_map = {
            "attack": "襲撃",
            "execute": "処刑",
            "curse": "呪殺",
            "suicide": "後追死",
            "retaliation": "道連れ"
        }
        
        for player in self.players:
            # 勝利プレイヤーかどうかを判定
            is_winner = False
            if has_winner:
                if player.role.team == self.victory_team:
                    is_winner = True
            
            # 生死情報の生成
            status = "最終日生存" # デフォルト
            if not player.alive:
                if player.death_info:
                    turn = player.death_info.get("turn", "?")
                    reason_en = player.death_info.get("reason", "unknown")
                    reason_ja = reason_map.get(reason_en, "不明")
                    status = f"{turn}日目 {reason_ja}により死亡"
                else:
                    status = "死亡(詳細不明)"
            
            results.append({
                "名前": player.name,
                "役職": player.role.name,
                "生死": status, # 詳細な生死情報を使用
                "陣営": player.role.team,
                "勝利": "🏆" if is_winner else "", 
            })
        return results

    def execute_day_vote(self, votes: Counter) -> Dict[str, Any]:
        """
        昼の投票結果に基づき、処刑を実行する。
        プレイヤーの状態を更新し、処刑結果に関する情報を辞書で返す。

        Args:
            votes: プレイヤー名をキー、得票数を値とする Counter オブジェクト。

        Returns:
            結果情報を含む辞書:
            {
                "executed": 処刑されたプレイヤー名 (Optional[str]),
                "immoral_suicides": 後追い自殺した背徳者の名前リスト (List[str]),
                "error": エラーメッセージ (Optional[str]),
                "debug": デバッグ情報 (Optional[str])
            }
        """
        result: Dict[str, Any] = {
            "executed": None,
            "immoral_suicides": [],
            "error": None,
            "debug": None
        }
        debug_info_list = [] if self.debug_mode else None

        if not votes:
            if self.debug_mode: 
                debug_info_list.append("投票なしのため処刑なし")
                result["debug"] = "; ".join(debug_info_list)
            self.last_executed_name = None
            # result["executed"] は None のまま
            return result

        max_votes = max(votes.values())
        candidates = [name for name, count in votes.items() if count == max_votes]

        if len(candidates) > 1:
            executed_name = random.choice(candidates)
            if self.debug_mode: 
                debug_info_list.append(f"同票のためランダム処刑: {candidates} -> {executed_name}")
        else:
            executed_name = candidates[0]

        if self.debug_mode: 
            debug_info_list.append(f"処刑対象は {executed_name}")
            
        executed_player = next((p for p in self.players if p.name == executed_name), None)

        if executed_player and executed_player.alive:
            executed_player.kill(self.turn, "execute")
            self.last_executed_name = executed_name
            result["executed"] = executed_name
            if self.debug_mode: 
                debug_info_list.append(f"{executed_name} を処刑しました")

            # 妖狐処刑時の後追い処理
            if executed_player.role.name == "妖狐":
                if self.debug_mode: 
                    debug_info_list.append("最後の妖狐が処刑されたため、背徳者の後追い処理を開始")
                immoral_players_to_kill = [p for p in self.get_alive_players() if p.role.name == "背徳者"]
                for immoral in immoral_players_to_kill:
                    immoral.kill(self.turn, "suicide")
                    result["immoral_suicides"].append(immoral.name)
                    if self.debug_mode: 
                        debug_info_list.append(f"{immoral.name}(背徳者) が後追い自殺")
            
            # ★★★ 猫又処刑時の道連れ処理 ★★★
            elif executed_player.role.name == "猫又":
                # 猫又自身を除いた生存者リストを作成
                other_alive_players = [p for p in self.get_alive_players() if p.alive and p.id != executed_player.id]
                if other_alive_players:
                    player_to_retaliate = random.choice(other_alive_players)
                    player_to_retaliate.kill(self.turn, "retaliation")
                    result["retaliation_victim"] = player_to_retaliate.name # 道連れにした相手を記録
                    if self.debug_mode: 
                        debug_info_list.append(f"{executed_name}(猫又)が処刑されたため、{player_to_retaliate.name}を道連れにしました")
                else:
                     if self.debug_mode: 
                         debug_info_list.append(f"{executed_name}(猫又)が処刑されましたが、道連れにする生存者がいません")
            
            # 共通の終了処理
            if self.debug_mode:
                result["debug"] = "; ".join(debug_info_list)
            return result
        elif executed_player and not executed_player.alive:
             if self.debug_mode: 
                 debug_info_list.append(f"処刑対象 {executed_name} は既に死亡しています")
                 result["debug"] = "; ".join(debug_info_list)
             self.last_executed_name = None
             # result["executed"] は None のまま
             return result
        else:
            # エラー情報を返す
            result["error"] = f"処刑対象プレイヤー '{executed_name}' が見つかりません"
            self.last_executed_name = None
            return result

    def _initialize_night_state(self) -> dict:
        """夜フェーズで使用する変数を初期化して辞書として返す。"""
        return {
            "wolf_choices": [],      # 人狼が選択した襲撃対象名のリスト
            "protected_players": [], # 騎士が守護したプレイヤー名のリスト
            "night_victims": [],     # 夜フェーズ中に確定した犠牲者名のリスト（呪殺など）
            "seer_results": {},      # 占い師/偽占い師の結果 {target_name: result_string}
            "medium_results": None   # 霊媒師の結果 (文字列)
        }

    def resolve_night_actions(self, night_actions: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        収集された夜のアクションデータを元に、夜の結果（占い、守護、襲撃、死亡）を解決する。
        プレイヤーの状態 (alive) を直接更新し、最終的な犠牲者と関連情報を辞書で返す。

        Args:
            night_actions: プレイヤー名をキーとし、アクション内容 ({\'type\': str, \'target\': Optional[str]})
                           を値とする辞書。

        Returns:
            結果情報を含む辞書:
            {
                "victims": この夜の最終的な犠牲者の名前リスト (List[str]),
                "immoral_suicides": 妖狐呪殺による後追い自殺者リスト (List[str]),
                "debug": デバッグ情報リスト (Optional[List[str]])
            }
        """
        result: Dict[str, Any] = {
            "victims": [],
            "immoral_suicides": [],
            "debug": [] if self.debug_mode else None
        }
        seer_actions = {}
        guard_targets = set()
        attack_targets = []
        night_victims = set()
        alive_players = self.get_alive_players()
        # debug_info = [] if self.debug_mode else None # result["debug"] を直接使う

        # 1. 各プレイヤーのアクションを分類・処理
        for player_name, action_data in night_actions.items():
            player = next((p for p in self.players if p.name == player_name), None)
            if not player or not player.alive:
                continue

            action_type = action_data.get("type")
            target_name = action_data.get("target")

            if action_type == "seer" and target_name:
                target_player = next((p for p in alive_players if p.name == target_name), None)
                if target_player:
                    if player.role.name == "占い師":
                        seer_result = target_player.role.seer_result()
                        seer_actions[player_name] = {"target": target_name, "result": seer_result}
                        if target_player.role.name == "妖狐":
                            target_player.kill(self.turn, "curse")
                            night_victims.add(target_name)
                            if self.debug_mode: 
                                result["debug"].append(f"{player_name}が{target_name}(妖狐)を呪殺")
                            # 最後の妖狐かチェックし、背徳者後追い処理
                            remaining_alive_foxes = [p for p in self.get_alive_players() if p.role.name == "妖狐" and p.alive]
                            if not remaining_alive_foxes:
                                immoral_players_to_kill = [p for p in self.get_alive_players() if p.role.name == "背徳者" and p.alive]
                                for immoral in immoral_players_to_kill:
                                    immoral.kill(self.turn, "suicide")
                                    night_victims.add(immoral.name) 
                                    result["immoral_suicides"].append(immoral.name)
                                    if self.debug_mode: 
                                        result["debug"].append(f"妖狐全滅により{immoral.name}(背徳者)が後追い")
                    elif player.role.name == "偽占い師":
                        seer_actions[player_name] = {"target": target_name, "result": "村人"}

            elif action_type == "guard" and target_name:
                guard_targets.add(target_name)
                if self.debug_mode: 
                    result["debug"].append(f"{player_name}が{target_name}を護衛")

            elif action_type == "attack" and target_name:
                attack_targets.append(target_name)
                if self.debug_mode: 
                    result["debug"].append(f"{player_name}が{target_name}を襲撃対象に選択")

        # 2. 人狼の襲撃対象を決定
        wolf_attack_victim_name = None
        if attack_targets:
            target_counts = Counter(attack_targets)
            most_common_target = target_counts.most_common(1)[0][0]
            wolf_attack_victim_name = most_common_target
            if self.debug_mode: 
                result["debug"].append(f"人狼の最終襲撃対象は {wolf_attack_victim_name}")

        # 3. 襲撃の解決 (守護、妖狐耐性、猫又道連れを考慮)
        if wolf_attack_victim_name:
            victim_player = next((p for p in alive_players if p.name == wolf_attack_victim_name), None)
            if victim_player:
                is_protected = wolf_attack_victim_name in guard_targets
                is_fox = victim_player.role.name == "妖狐"
                if not is_protected and not is_fox:
                    # 襲撃成功
                    victim_player.kill(self.turn, "attack")
                    night_victims.add(wolf_attack_victim_name)
                    if self.debug_mode: 
                        result["debug"].append(f"襲撃成功: {wolf_attack_victim_name} が死亡")
                    
                    # ★★★ 猫又の道連れ処理 ★★★
                    if victim_player.role.name == "猫又":
                        alive_wolves = [p for p in self.get_alive_players() if p.role.species() == "人狼" and p.alive]
                        if alive_wolves:
                            wolf_to_kill = random.choice(alive_wolves)
                            wolf_to_kill.kill(self.turn, "retaliation") # 死因は "retaliation" とする
                            night_victims.add(wolf_to_kill.name)
                            if self.debug_mode:
                                result["debug"].append(f"{wolf_attack_victim_name}(猫又)が襲撃されたため、{wolf_to_kill.name}(人狼)を道連れにしました")
                        else:
                            if self.debug_mode:
                                result["debug"].append(f"{wolf_attack_victim_name}(猫又)が襲撃されましたが、道連れにする生存人狼がいません")
                elif is_protected:
                    if self.debug_mode: 
                        result["debug"].append(f"襲撃失敗: {wolf_attack_victim_name} は守られていた")
                elif is_fox:
                    if self.debug_mode: 
                        result["debug"].append(f"襲撃失敗: {wolf_attack_victim_name} は妖狐だった")
            else:
                if self.debug_mode: 
                    result["debug"].append(f"襲撃対象 {wolf_attack_victim_name} は既に死亡していた")

        # 4. 最終的な犠牲者リストを作成し、状態を更新
        final_victim_names = sorted(list(set(night_victims)))
        self.last_night_victim_name_list = final_victim_names # これは夜の結果発表用なので残す
        result["victims"] = final_victim_names

        if self.debug_mode: 
            result["debug"].append(f"今夜の最終犠牲者リスト: {final_victim_names}")
            # result["debug"] はリストのまま返す
        elif not result["debug"]: # デバッグモードOFFならNoneにする
             result["debug"] = None
        
        return result
        