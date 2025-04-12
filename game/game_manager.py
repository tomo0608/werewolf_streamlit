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
        """
        alive_players = self.get_alive_players()
        wolves = [player for player in alive_players if player.role.species() == "人狼"]
        villagers = [player for player in alive_players if player.role.species() == "村人"]
        foxes = [player for player in alive_players if player.role.species() == "妖狐"]

        victory_team: Optional[str] = None
        victory_message: Optional[str] = None

        # 人狼全滅時の判定
        if len(wolves) == 0:
            if len(foxes) == 0:
                victory_team = "村人"
                victory_message = "人狼は全滅しました。村人陣営の勝利です！"
            else:
                victory_team = "妖狐"
                victory_message = "人狼は全滅しました。妖狐陣営の勝利です！"
        # 人狼が村人以上になった時の判定
        elif len(wolves) >= len(villagers):
            if len(foxes) == 0:
                victory_team = "人狼"
                victory_message = "人狼が村人の人数以上となりました。人狼陣営の勝利です！"
            else:
                victory_team = "妖狐"
                victory_message = "人狼が村人の人数以上となりました。妖狐陣営の勝利です！"

        # 勝利条件が満たされた場合
        if victory_team and victory_message:
            self.victory_team = victory_team # 内部状態も更新
            # print(victory_message) # print は不要
            return {"team": victory_team, "message": victory_message}
        
        # ゲーム続行の場合
        return None

    def get_game_results(self) -> List[Dict[str, Any]]:
        """ゲーム終了時の結果情報をリストとして返す。"""
        results = []
        # 勝利チームが確定しているか確認 (check_victory で設定される)
        has_winner = self.victory_team is not None
        
        for player in self.players:
            is_winner = has_winner and player.role.team == self.victory_team
            results.append({
                "名前": player.name,
                "役職": player.role.name,
                "生死": "生存" if player.alive else "死亡",
                "陣営": player.role.team,
                "勝利": "🏆" if is_winner else "", # 絵文字で表現
                # "勝利": is_winner # bool値で返す場合
            })
        return results

    def _run_discussion(self):
        """議論時間を実行し、関連するメッセージを表示する。(Streamlit ではタイマー表示などに変更)"""
        # 議論時間は仮で1秒 (元は1秒 * 1 = 1秒)
        discussion_time_seconds = 1 # 本来はもっと長い時間 (例: 120)
        print(f"議論タイムです。制限時間は{discussion_time_seconds}秒です。") # st.write
        # time.sleep は Streamlit では使えない (UI が固まる)
        # for remaining_time in range(discussion_time_seconds, 0, -1):
        #     # 頻繁な表示を避けるため、残り10秒以下または特定のタイミングでのみ表示
        #     if remaining_time <= 10 or remaining_time % 30 == 0:
        #         print(f"残り時間: {remaining_time}秒")
        #     time.sleep(1)
        print("議論タイムが終了しました！") # st.write
        input("Enterキーを押して投票フェーズに移行してください...") # 不要
        # clear_screen() # 不要

    def _conduct_voting(self, alive_players: List[Player]) -> Counter:
        """各プレイヤーから投票を受け付け、集計結果を返す。(Streamlit では UI で投票を受け付ける)"""
        votes = Counter()
        alive_player_names = [p.name for p in alive_players]
        # このループは Streamlit の UI で代替される
        # for player in alive_players:
        #     print("\n=== 投票フェーズ ===")
        #     while True:
        #         print(f"{player.name} さん、誰に投票しますか？")
        #         print("生存者名: ", alive_player_names)
        #         vote = input("名前を入力してください: ") # st.selectbox などで選択
        #         if vote in alive_player_names:
        #             votes[vote] += 1
        #             # clear_screen() # 不要
        #             break
        #         else:
        #             print("無効な名前です。生存者から選んでください。") # st.warning
        # return votes # Streamlit から集計結果を渡す形になる

    def _execute_player(self, votes: Counter, alive_players: List[Player]):
        """投票結果に基づき処刑対象を決定し、実行する。(Streamlit で結果を表示)"""
        print("\n投票結果:") # st.write
        for name, count in votes.items():
            print(f"{name}: {count}票") # st.write

        if not votes:
            print("投票が行われませんでした。本日の処刑はありません。") # st.info
            self.last_executed_name = None
            return

        max_votes = max(votes.values())
        candidates = [name for name, count in votes.items() if count == max_votes]

        if len(candidates) > 1:
            print("投票が同数で決まりませんでした。ランダムで処刑対象を選びます。") # st.warning
            executed_name = random.choice(candidates)
        else:
            executed_name = candidates[0]

        # executed_player = next(player for player in alive_players if player.name == executed_name)
        # `next` は要素が見つからない場合に StopIteration を送出する可能性があるため、より安全な方法に変更
        executed_player = None
        for p in alive_players:
            if p.name == executed_name:
                executed_player = p
                break

        if executed_player:
            executed_player.kill() # Playerクラスにkillメソッドがあると仮定（なければ alive = False のまま）
            input(f"{executed_name} さんが処刑されました。") # st.error などで表示、input は不要
            self.last_executed_name = executed_name

            # 妖狐が処刑された場合の背徳者の後追い処理
            if executed_player.role.name == "妖狐":
                fox_players = [p for p in self.get_alive_players() if p.role.name == "妖狐"]
                if not fox_players: # 最後の妖狐が処刑された
                    immoral_players = [p for p in self.get_alive_players() if p.role.name == "背徳者"]
                    for immoral_player in immoral_players:
                        immoral_player.kill()
                        input(f"妖狐が全滅したため、{immoral_player.name} さんが自殺しました。") # st.warning, input 不要
        else:
             # 基本的にここには到達しないはずだが、念のため
            print(f"エラー: 処刑対象プレイヤー '{executed_name}' が見つかりませんでした。") # st.error
            self.last_executed_name = None

    def day_phase(self)->None:
        """
        昼のフェーズを実行する関数。(Streamlit では段階的に実行)
        - 議論 (UI表示)
        - 投票 (UIで受付)
        - 処刑 (結果表示)
        """
        alive_players = self.get_alive_players()

        # 議論 (Streamlit UI で時間を表示)
        # self._run_discussion()

        # 投票 (Streamlit UI で受け付け、結果を votes 変数に格納する)
        # votes = self._conduct_voting(alive_players) # UIからの結果を受け取る

        # 処刑 (投票結果を元に実行し、結果を表示)
        # self._execute_player(votes, alive_players)

    def execute_day_vote(self, votes: Counter) -> Optional[str]:
        """
        昼の投票結果に基づき、処刑を実行する。
        プレイヤーの状態を更新し、処刑されたプレイヤー名を返す。

        Args:
            votes: プレイヤー名をキー、得票数を値とする Counter オブジェクト。

        Returns:
            処刑されたプレイヤーの名前。処刑がなかった場合は None。
        """
        if not votes:
            if self.debug_mode: print("DEBUG: 投票なしのため処刑なし")
            self.last_executed_name = None
            return None

        max_votes = max(votes.values())
        candidates = [name for name, count in votes.items() if count == max_votes]

        if len(candidates) > 1:
            if self.debug_mode: print(f"DEBUG: 同票のためランダム処刑: {candidates}")
            executed_name = random.choice(candidates)
        else:
            executed_name = candidates[0]

        if self.debug_mode: print(f"DEBUG: 処刑対象は {executed_name}")
        executed_player = next((p for p in self.players if p.name == executed_name), None)

        if executed_player and executed_player.alive:
            executed_player.kill()
            self.last_executed_name = executed_name
            if self.debug_mode: print(f"DEBUG: {executed_name} を処刑しました")

            # 妖狐処刑時の後追い処理
            if executed_player.role.name == "妖狐":
                alive_foxes = [p for p in self.get_alive_players() if p.role.name == "妖狐"]
                if not alive_foxes:
                    if self.debug_mode: print("DEBUG: 最後の妖狐が処刑されたため、背徳者の後追い処理を開始")
                    immoral_players = [p for p in self.get_alive_players() if p.role.name == "背徳者"]
                    for immoral in immoral_players:
                        if immoral.alive:
                            immoral.kill()
                            if self.debug_mode: print(f"DEBUG: {immoral.name}(背徳者) が後追い自殺")
            return executed_name
        elif executed_player and not executed_player.alive:
             if self.debug_mode: print(f"DEBUG: 処刑対象 {executed_name} は既に死亡しています")
             self.last_executed_name = None
             return None
        else:
            print(f"ERROR: 処刑対象プレイヤー '{executed_name}' が見つかりません") # エラーログは残す
            self.last_executed_name = None
            return None

    def _initialize_night_state(self) -> dict:
        """夜フェーズで使用する変数を初期化して辞書として返す。"""
        return {
            "wolf_choices": [],      # 人狼が選択した襲撃対象名のリスト
            "protected_players": [], # 騎士が守護したプレイヤー名のリスト
            "night_victims": [],     # 夜フェーズ中に確定した犠牲者名のリスト（呪殺など）
            "seer_results": {},      # 占い師/偽占い師の結果 {target_name: result_string}
            "medium_results": None   # 霊媒師の結果 (文字列)
        }

    def _execute_player_night_action(self, player: Player, alive_players: List[Player], night_state: dict):
        """個々のプレイヤーの夜のアクションを実行し、night_stateを更新する。(Streamlit UI で実行)"""
        # clear_screen() # 不要
        print(f"{player.name} さんの番です。") # st.write など
        input("Enterキーを押して操作を続行してください...") # 不要

        # 偽占い師の場合は表示上「占い師」とする
        display_role = "占い師" if player.role.name == "偽占い師" else player.role.name
        print(f"{player.name} さん、あなたの役職は {display_role} です。") # st.write

        alive_player_names = [p.name for p in alive_players]
        # 人狼以外の生存者リスト（人狼の襲撃対象候補）
        non_wolf_alive_players = [p.name for p in alive_players if p.role.species() != "人狼"]

        # --- 役職ごとのアクション (Streamlit UI で選択させる) ---
        if player.role.name in ["村人", "妖狐", "狂人", "狂信者", "背徳者"]:
            # 特定の役職の追加情報表示や状態更新
            if player.role.name == "妖狐":
                night_state["protected_players"].append(player.name) # 妖狐は占いで死ぬが、襲撃は受けない
            # elif player.role.name == "狂信者": # 情報表示は Streamlit で行う
            # elif player.role.name == "背徳者": # 情報表示は Streamlit で行う

            # アクション自体は何もしないが、入力は促す (Streamlit UI では不要か、「確認」ボタン程度)
            input(f"{player.name} さん、夜のアクションはありません。怪しいと思う人の名前を入力してください（ゲーム進行には影響しません）: ") # 不要

        elif player.role.name == "人狼":
            print(f"{player.name} さんは人狼です。")
            if self.turn == 1:
                print("初日は襲撃できません。")
                input("怪しいと思う人の名前を入力してください（ゲーム進行には影響しません）: ") # 不要
            else:
                print("誰を襲撃しますか？") # st.write
                while True: # UI で選択させるのでループ不要
                    print("襲撃可能な対象: ", non_wolf_alive_players) # st.selectbox の選択肢
                    target_name = input("襲撃対象の名前を入力してください: ") # UI から取得
                    if target_name in non_wolf_alive_players:
                        night_state["wolf_choices"].append(target_name)
                        break # ループ不要
                    else:
                        print("無効な名前です。人狼ではない生存者から選んでください。") # st.warning

        elif player.role.name == "占い師" or player.role.name == "偽占い師":
            print("誰を占いますか？") # st.write
            while True: # UI で選択させるのでループ不要
                print("占う対象の候補: ", alive_player_names) # st.selectbox の選択肢
                target_name = input("占う対象の名前を入力してください: ") # UI から取得
                target_player = next((p for p in alive_players if p.name == target_name), None)

                if target_player:
                    result_message = ""
                    if player.role.name == "偽占い師":
                        result_message = f"{target_name} さんの役職は 村人 です。"
                        night_state["seer_results"][target_name] = "村人"
                    else: # 本物の占い師
                        role_result = target_player.role.seer_result()
                        result_message = f"{target_name} さんの役職は {role_result} です。"
                        night_state["seer_results"][target_name] = role_result
                        # 妖狐を占った場合の呪殺処理
                        if target_player.role.name == "妖狐":
                            target_player.kill()
                            night_state["night_victims"].append(target_name)
                            # print(f"(debug mode) {target_name} さんを呪殺しました。") # st.warning など
                            # 最後の妖狐が死んだ場合、背徳者も後追い自殺
                            if not [p for p in self.get_alive_players() if p.role.name == "妖狐"]:
                                for immoral_player in [p for p in alive_players if p.role.name == "背徳者"]:
                                    if immoral_player.alive: # まだ生きている背徳者のみ
                                        immoral_player.kill()
                                        night_state["night_victims"].append(immoral_player.name)
                                        # print(f"妖狐が全滅したため、背徳者 {immoral_player.name} さんが後を追いました。") # st.warning など
                    print(result_message) # st.info などで表示
                    break # ループ不要
                else:
                    print("無効な名前です。生存者から選んでください。") # st.warning

        elif player.role.name == "霊媒師":
            print("霊媒師です。") # st.write
            if self.last_executed_name:
                # 前日に処刑されたプレイヤーオブジェクトを探す
                executed_player = next((p for p in self.players if p.name == self.last_executed_name), None)
                if executed_player:
                    medium_result = executed_player.role.medium_result()
                    result_message = f"昨日処刑された {self.last_executed_name} さんの役職は {medium_result} でした。"
                    night_state["medium_results"] = medium_result # 結果を保存
                    print(result_message) # st.info などで表示
                else:
                    print(f"昨日処刑された {self.last_executed_name} さんの情報が見つかりません。") # st.warning
            else:
                print("昨日は誰も処刑されませんでした。") # st.info
            input("怪しいと思う人の名前を入力してください（ゲーム進行には影響しません）: ") # 不要

        elif player.role.name == "騎士":
            print("騎士です。") # st.write
            if self.turn == 1:
                print("初日は守ることができません。") # st.info
                input("怪しいと思う人の名前を入力してください（ゲーム進行には影響しません）: ") # 不要
            else:
                print("誰を守りますか？") # st.write
                while True: # UI で選択させるのでループ不要
                    # 自分以外の生存者を候補とする
                    protectable_players = [p.name for p in alive_players if p.name != player.name]
                    print("守る対象の候補: ", protectable_players) # st.selectbox の選択肢
                    target_name = input("守る対象の名前を入力してください: ") # UI から取得
                    if target_name == player.name:
                        print("自分自身を守ることはできません。") # st.warning
                    elif target_name in protectable_players:
                        night_state["protected_players"].append(target_name)
                        print(f"{target_name} さんを守ることにしました。") # st.success
                        break # ループ不要
                    else:
                        print("無効な名前です。自分以外の生存者から選んでください。") # st.warning
        else:
            # 未知の役職があればエラー
            raise ValueError(f"未定義の役職です: {player.role.name}")

        input("Enterキーを押して次のプレイヤーに進みます...") # 不要
        # clear_screen() # 不要

    def _resolve_night_attacks(self, night_state: dict, alive_players: List[Player]) -> List[str]:
        """人狼の襲撃と騎士の守護を解決し、最終的な犠牲者リストを返す。"""
        wolf_attack_victim_name = None
        if night_state["wolf_choices"]:
            # 多数決で襲撃対象を決定
            victim_candidate = Counter(night_state["wolf_choices"]).most_common(1)[0][0]

            # 守られていないか、かつ妖狐でないか確認
            if victim_candidate not in night_state["protected_players"]:
                victim_player = next((p for p in alive_players if p.name == victim_candidate), None)
                if victim_player and victim_player.role.name != "妖狐": # 妖狐は襲撃では死なない
                    wolf_attack_victim_name = victim_candidate
                    victim_player.kill()
                    # print(f"人狼による襲撃の結果、{victim_player.name} さんが犠牲になりました。") # 結果は後でまとめて表示
                elif victim_player and victim_player.role.name == "妖狐":
                    # print(f"人狼は {victim_player.name} さんを襲撃しましたが、妖狐だったため失敗しました。") # 結果は後でまとめて表示
                    pass # 何もしないことを明示
                # else: victim_player が None のケースは基本的に起こらないはず
            elif victim_candidate in night_state["protected_players"]:
                # print(f"人狼は {victim_candidate} さんを襲撃しましたが、騎士に守られていました。") # 結果は後でまとめて表示
                pass # 何もしないことを明示
            # else: 守られていて、かつ妖狐の場合（通常、騎士は妖狐を守らない想定だが念のため）

        # 夜フェーズ中に発生した犠牲者（呪殺など）と襲撃犠牲者を合わせる
        final_victims = night_state["night_victims"]
        if wolf_attack_victim_name:
            final_victims.append(wolf_attack_victim_name)

        # 重複削除とソート
        return sorted(list(set(final_victims)))

    def night_phase(self)->None:
        """
        夜のフェーズを実行する関数。(Streamlit では UI で各プレイヤーのアクションを促す)
        """
        print("\n=== 夜のフェーズ ===") # st.header など
        alive_players = self.get_alive_players()
        random.shuffle(alive_players) # 行動順をランダムにする

        # 1. 夜の状態を初期化
        night_state = self._initialize_night_state()

        # 2. 各プレイヤーの夜アクションを実行 (Streamlit UI で順に実行させる)
        # for player in alive_players:
        #     self._execute_player_night_action(player, alive_players, night_state)

        # 3. 夜の襲撃などを解決し、犠牲者を決定 (全プレイヤーのアクション完了後に実行)
        # final_victim_names = self._resolve_night_attacks(night_state, alive_players)

        # 4. 結果をゲームマネージャーの状態に反映
        # self.last_night_victim_name_list = final_victim_names

        # 夜フェーズ終了 (Streamlit では昼フェーズへの遷移処理)
        print("夜のフェーズが終了しました。全員目を開けてください。") # 不要

    def resolve_night_actions(self, night_actions: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        収集された夜のアクションデータを元に、夜の結果（占い、守護、襲撃、死亡）を解決する。
        プレイヤーの状態 (alive) を直接更新し、最終的な犠牲者の名前リストを返す。

        Args:
            night_actions: プレイヤー名をキーとし、アクション内容 ({'type': str, 'target': Optional[str]})
                           を値とする辞書。

        Returns:
            この夜の最終的な犠牲者の名前のリスト。
        """
        seer_actions = {}
        guard_targets = set()
        attack_targets = []
        night_victims = set()
        alive_players = self.get_alive_players()

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
                        result = target_player.role.seer_result()
                        seer_actions[player_name] = {"target": target_name, "result": result}
                        if target_player.role.name == "妖狐":
                            target_player.kill()
                            night_victims.add(target_name)
                            if self.debug_mode: print(f"DEBUG: {player_name}が{target_name}(妖狐)を呪殺")
                            alive_foxes = [p for p in self.get_alive_players() if p.role.name == "妖狐"]
                            if not alive_foxes:
                                immoral_players = [p for p in self.get_alive_players() if p.role.name == "背徳者"]
                                for immoral in immoral_players:
                                    if immoral.alive:
                                        immoral.kill()
                                        night_victims.add(immoral.name)
                                        if self.debug_mode: print(f"DEBUG: 妖狐全滅により{immoral.name}(背徳者)が後追い")
                    elif player.role.name == "偽占い師":
                        seer_actions[player_name] = {"target": target_name, "result": "村人"}

            elif action_type == "guard" and target_name:
                guard_targets.add(target_name)
                if self.debug_mode: print(f"DEBUG: {player_name}が{target_name}を護衛")

            elif action_type == "attack" and target_name:
                attack_targets.append(target_name)
                if self.debug_mode: print(f"DEBUG: {player_name}が{target_name}を襲撃対象に選択")

        # 2. 人狼の襲撃対象を決定
        wolf_attack_victim_name = None
        if attack_targets:
            target_counts = Counter(attack_targets)
            most_common_target = target_counts.most_common(1)[0][0]
            wolf_attack_victim_name = most_common_target
            if self.debug_mode: print(f"DEBUG: 人狼の最終襲撃対象は {wolf_attack_victim_name}")

        # 3. 襲撃の解決 (守護、妖狐耐性を考慮)
        if wolf_attack_victim_name:
            victim_player = next((p for p in alive_players if p.name == wolf_attack_victim_name), None)
            if victim_player:
                is_protected = wolf_attack_victim_name in guard_targets
                is_fox = victim_player.role.name == "妖狐"
                if not is_protected and not is_fox:
                    victim_player.kill()
                    night_victims.add(wolf_attack_victim_name)
                    if self.debug_mode: print(f"DEBUG: 襲撃成功: {wolf_attack_victim_name} が死亡")
                elif is_protected:
                    if self.debug_mode: print(f"DEBUG: 襲撃失敗: {wolf_attack_victim_name} は守られていた")
                elif is_fox:
                    if self.debug_mode: print(f"DEBUG: 襲撃失敗: {wolf_attack_victim_name} は妖狐だった")
            else:
                if self.debug_mode: print(f"DEBUG: 襲撃対象 {wolf_attack_victim_name} は既に死亡していた")

        # 4. 最終的な犠牲者リストを作成し、状態を更新
        final_victim_names = sorted(list(set(night_victims)))
        self.last_night_victim_name_list = final_victim_names

        if self.debug_mode: print(f"DEBUG: 今夜の最終犠牲者リスト: {final_victim_names}")
        return final_victim_names
        