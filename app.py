# Streamlit 人狼ゲーム アプリ
import streamlit as st
import sys
import os # os モジュールを追加
import random
import time

# プロジェクトルートを Python パスに追加
# app.py の場所に基づいて動的にパスを設定
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# game, config モジュールをインポート (パス追加後に実行)
try:
    from game.game_manager import GameManager # GameManager は後で使う
    from game.player import Player
    from game.role import role_dict # role_dict は役職設定で使う
    import config.settings as settings
except ImportError as e:
    st.error(f"モジュールのインポートに失敗しました: {e}")
    st.error("プロジェクト構造を確認し、必要なファイルが存在するか確認してください。")
    st.stop() # エラー時はアプリを停止

# --- 定数 ---
# 本来は main.py や config に定義すべきだが、一旦ここに置く
AVAILABLE_ROLES = list(role_dict.keys())
MIN_PLAYERS = 3

# --- セッション状態の初期化 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'initial_setup'
    st.session_state.player_count = 0
    st.session_state.player_names = []
    st.session_state.role_counts = {}
    st.session_state.error_message = "" # エラー表示用

# --- アプリケーションのタイトル ---
st.title("人狼ゲーム🐺")

# --- ゲーム設定 (プレイヤー数・名前) ---
if st.session_state.stage == 'initial_setup':
    st.header("ゲーム設定")
    st.session_state.error_message = "" # ステージ開始時にエラーをクリア

    # --- プレイヤー数設定 ---
    st.subheader("プレイヤー人数")

    # デフォルト設定の使用
    use_default_count = False
    default_count = getattr(settings, "DEFAULT_PLAYER_COUNT", 0)
    if default_count >= MIN_PLAYERS:
        if st.button(f"デフォルトの {default_count} 人で設定"):
            st.session_state.player_count = default_count
            use_default_count = True
            st.rerun() # 数値を反映させるために再実行

    # 数値入力
    current_player_count = st.session_state.player_count if st.session_state.player_count >= MIN_PLAYERS else MIN_PLAYERS
    num_input = st.number_input(
        f"人数を入力してください（{MIN_PLAYERS}人以上）",
        min_value=MIN_PLAYERS,
        value=current_player_count,
        step=1,
        key="player_count_input", # キーを固定
        disabled=use_default_count # デフォルト使用時は無効化
    )
    # number_input の値が変更されたら session_state に反映
    if not use_default_count and num_input != st.session_state.player_count:
         st.session_state.player_count = num_input
         st.session_state.player_names = [""] * num_input # 名前入力欄をリセット
         st.rerun()

    # --- プレイヤー名設定 ---
    if st.session_state.player_count >= MIN_PLAYERS:
        st.subheader("プレイヤー名")

        # デフォルト名の使用
        use_default_names = False
        default_names = getattr(settings, "DEFAULT_PLAYER_NAMES", [])
        if len(default_names) == st.session_state.player_count:
             if st.button(f"デフォルト名 {default_names} を使用"):
                 st.session_state.player_names = list(default_names) # コピーして設定
                 use_default_names = True
                 st.rerun() # 名前を反映させるために再実行

        # 名前入力欄を動的に生成
        # player_names が player_count と一致しない場合は初期化
        if len(st.session_state.player_names) != st.session_state.player_count:
             st.session_state.player_names = [""] * st.session_state.player_count

        input_names = []
        cols = st.columns(3) # 3列で表示
        for i in range(st.session_state.player_count):
            container = cols[i % 3]
            # デフォルト値を設定: session_state の値が空なら f"プレイヤー{i + 1}" を使う
            default_value = st.session_state.player_names[i] or f"プレイヤー{i + 1}"
            name = container.text_input(
                f"プレイヤー{i + 1}",
                value=default_value, # 修正箇所
                key=f"player_name_{i}",
                disabled=use_default_names
            )
            input_names.append(name)
        
        # 名前が変更されたら session_state に反映 (ボタン押下時ではなく入力の都度)
        # デフォルト値「プレイヤーN」が入力された場合も session_state に反映させる
        if not use_default_names and input_names != st.session_state.player_names:
             st.session_state.player_names = input_names
             # ここでは rerun しない（入力途中で消えないように）

        # --- 設定確定ボタン ---
        if st.button("役職設定へ進む"):
            # 入力チェック
            valid = True
            if not st.session_state.player_names: # player_names が空の場合
                st.session_state.error_message = "プレイヤー名が設定されていません。"
                valid = False
            elif "" in st.session_state.player_names:
                st.session_state.error_message = "すべてのプレイヤー名を入力してください。"
                valid = False
            elif len(set(st.session_state.player_names)) != st.session_state.player_count:
                st.session_state.error_message = "プレイヤー名が重複しています。"
                valid = False

            if valid:
                st.session_state.stage = 'role_setup' # 次のステージへ
                st.session_state.error_message = ""   # エラーメッセージをクリア
                st.rerun() # 次のステージを表示するために再実行
            else:
                 # エラーがあれば再実行してメッセージを表示
                 st.rerun()

    # エラーメッセージ表示
    if st.session_state.error_message:
        st.error(st.session_state.error_message)


# --- ゲーム設定 (役職) ---
elif st.session_state.stage == 'role_setup':
    st.header("役職設定")
    st.write(f"プレイヤー数: {st.session_state.player_count} 人")
    st.write(f"プレイヤー名: {', '.join(st.session_state.player_names)}")
    st.session_state.error_message = "" # ステージ開始時にエラーをクリア

    # --- デフォルト役職構成の使用 ---
    use_default_roles = False
    default_roles_valid = False
    default_role_counts = getattr(settings, "DEFAULT_ROLE_COUNTS", {})
    if default_role_counts and sum(default_role_counts.values()) == st.session_state.player_count:
        default_roles_valid = True
        if st.button("デフォルトの役職構成を使用"):
            st.session_state.role_counts = default_role_counts.copy()
            use_default_roles = True
            st.rerun() # 役職数を反映

    # --- 役職人数入力 ---
    st.subheader("各役職の人数")

    # session_state に role_counts がなければ初期化
    if 'role_counts' not in st.session_state or not st.session_state.role_counts:
         # 利用可能な全役職キーで0を初期値とする
         st.session_state.role_counts = {role: 0 for role in AVAILABLE_ROLES}
         # デフォルトが有効ならそれを初期値にする（ボタン押下前でも）
         if default_roles_valid and not use_default_roles:
              st.session_state.role_counts = default_role_counts.copy()


    input_role_counts = {}
    current_total = 0
    cols = st.columns(3) # 3列で表示
    for i, role in enumerate(AVAILABLE_ROLES):
        container = cols[i % 3]
        # 現在の session_state の値を取得、なければ0
        current_value = st.session_state.role_counts.get(role, 0)
        
        # プレイヤー残り人数計算 (この役職を除く)
        temp_total = sum(st.session_state.role_counts.get(r, 0) for r in AVAILABLE_ROLES if r != role)
        max_value_for_role = st.session_state.player_count - temp_total

        count = container.number_input(
            role,
            min_value=0,
            # max_value を設定すると他の入力と連動して挙動が複雑になるため、一旦外すか、注意深く設定する
            # max_value=max_value_for_role,
            value=current_value,
            step=1,
            key=f"role_count_{role}",
            disabled=use_default_roles
        )
        input_role_counts[role] = count
        current_total += count

    # 入力値が変更されたら session_state に反映
    if not use_default_roles and input_role_counts != st.session_state.role_counts:
        st.session_state.role_counts = input_role_counts
        # 値変更の都度 rerun すると入力がしづらい場合があるので、一旦コメントアウト
        # st.rerun()

    # --- 残り人数表示 ---
    remaining_players = st.session_state.player_count - current_total
    st.info(f"割り当て済み: {current_total} 人 / 残り: {remaining_players} 人")
    if remaining_players < 0:
        st.warning("人数がプレイヤー数を超えています！")
    elif remaining_players > 0:
        st.warning("まだ割り当てられていないプレイヤーがいます。")
    else:
         st.success("すべてのプレイヤーに役職が割り当てられました。")


    # --- 設定確定ボタン ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("設定を確認する", disabled=(remaining_players != 0)): # 合計が一致しないと押せない
            # バリデーション (ボタン無効化で代替しているが念のため)
            if sum(st.session_state.role_counts.values()) == st.session_state.player_count:
                st.session_state.stage = 'confirm_setup'
                st.session_state.error_message = ""
                st.rerun()
            else:
                # このメッセージは通常表示されないはず
                st.session_state.error_message = "役職の合計人数がプレイヤー数と一致しません。"
                st.rerun()
    with col2:
        if st.button("プレイヤー設定に戻る"):
            st.session_state.stage = 'initial_setup'
            st.rerun()

    # エラーメッセージ表示
    if st.session_state.error_message:
        st.error(st.session_state.error_message)


# --- 設定確認 ---
elif st.session_state.stage == 'confirm_setup':
    st.header("設定確認")
    st.subheader("プレイヤー")
    st.write(f"{st.session_state.player_count} 人: {', '.join(st.session_state.player_names)}")
    st.subheader("役職")
    roles_summary = []
    for role, count in st.session_state.role_counts.items():
        if count > 0:
            roles_summary.append(f"{role}: {count}人")
    st.write(" - " + "\n - ".join(roles_summary))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("ゲーム開始！"):
            # GameManager インスタンスを作成してセッション状態に保存
            player_names = st.session_state.player_names
            role_counts = st.session_state.role_counts
            # 役職リストを作成 (GameManager の __init__ に渡すため)
            roles = []
            for role_name, count in role_counts.items():
                roles.extend([role_name] * count)
            
            # GameManager インスタンス化
            # TODO: デバッグモードの設定方法を追加する (例: st.checkbox)
            game_manager = GameManager(player_names, debug_mode=False)
            game_manager.assign_roles(roles)
            
            st.session_state.game_manager = game_manager
            st.session_state.stage = 'night_phase' # 最初のフェーズへ
            st.session_state.current_player_index = 0 # 夜アクションを行うプレイヤーのインデックス
            st.session_state.night_actions = {} # 夜のアクション結果を保存
            st.rerun()
    with col2:
        if st.button("役職設定に戻る"):
            st.session_state.stage = 'role_setup'
            # game_manager が存在すれば削除 (設定変更のため)
            if 'game_manager' in st.session_state:
                 del st.session_state.game_manager
            st.rerun()

# --- 夜フェーズ ---
elif st.session_state.stage == 'night_phase':
    gm = st.session_state.game_manager
    st.header(f"ターン {gm.turn}: 夜🔮")

    alive_players = gm.get_alive_players()
    current_player_index = st.session_state.get('current_player_index', 0) # 初期値設定
    action_confirmed_for_current_player = st.session_state.get(f'action_confirmed_{current_player_index}', False)

    # 全員の夜アクションが完了したかチェック
    if current_player_index >= len(alive_players):
        # 夜のアクション解決処理を実行
        victim_names = gm.resolve_night_actions(st.session_state.night_actions)
        st.session_state.last_night_victims = victim_names # 結果を保存

        st.session_state.stage = 'day_phase'
        st.success("全員の夜のアクションが完了しました。昼フェーズへ移行します。")
        # Reset confirmation flags for next night
        for i in range(len(alive_players)):
            if f'action_confirmed_{i}' in st.session_state:
                del st.session_state[f'action_confirmed_{i}']
        # rerun する前にボタンを表示して、ユーザーが結果を確認する時間を設ける
        if st.button("昼へ進む"):
            st.rerun()
        st.stop() # ボタンが表示されるまで待機

    # 現在アクションするプレイヤーを取得
    # インデックスが範囲外になる場合があるためチェックを追加
    if current_player_index < len(alive_players):
        current_player = alive_players[current_player_index]
    else:
        # 通常ここには到達しないはずだが、安全のためリセットして再実行
        st.warning("プレイヤーインデックスエラー。リセットします。")
        st.session_state.stage = 'initial_setup'
        # Clean up session state before rerun might be needed here
        st.rerun()
        st.stop()

    st.subheader(f"{current_player.name} さんの番です")
    st.warning("⚠️ **他の人は見ないでください！** スマホをこの人に渡してください。")

    # 役職確認エリア
    role_revealed = st.toggle(f"役職を確認する ( {current_player.name} さんのみ)", key=f"role_toggle_{current_player.name}")
    if role_revealed:
        display_role = "占い師" if current_player.role.name == "偽占い師" else current_player.role.name
        st.info(f"あなたの役職は **{display_role}** です。")

        # アクションが必要か判定
        action_required = current_player.role.has_night_action(gm.turn)

        if action_required:
            st.markdown("--- ")
            st.subheader("アクション")

            # アクションが既に確定されている場合 (占い結果表示など)
            if action_confirmed_for_current_player:
                action_data = st.session_state.night_actions.get(current_player.name, {})
                action_type = action_data.get("type")
                selected_target = action_data.get("target")

                if action_type in ["seer", "attack", "guard"] and selected_target:
                    st.write(f"あなたは **{selected_target}** さんを選択しました。")
                    # 占い師・偽占い師の場合、結果を表示
                    if action_type == "seer" or action_type == "fake_seer":
                        target_player = next((p for p in gm.players if p.name == selected_target), None)
                        if target_player:
                            # TODO: 偽占い師の結果生成ロジックを Game Manager 側か Role 側に追加する
                            if current_player.role.name == "偽占い師":
                                # 仮の偽占い結果 (本来は GameManager か Role で実装すべき)
                                seer_result = random.choice(["人狼", "人狼ではない"]) # 例: ランダム
                                st.info(f"占い結果（偽）: **{selected_target}** さんは **{seer_result}** です。")
                            else:
                                seer_result = target_player.role.seer_result()
                                st.info(f"占い結果: **{selected_target}** さんは **{seer_result}** です。")
                        else:
                            st.error("対象プレイヤーが見つかりませんでした。")
                    # 騎士、人狼は結果表示なし (結果は朝にわかる)

                elif action_type == "medium":
                    if gm.last_executed_name:
                        executed_player = next((p for p in gm.players if p.name == gm.last_executed_name), None)
                        if executed_player:
                            medium_result = executed_player.role.medium_result()
                            st.info(f"昨晩処刑された {gm.last_executed_name} は **{medium_result}** でした。")
                        else:
                            st.warning(f"{gm.last_executed_name} の情報が見つかりませんでした。")
                    else:
                        st.info("昨晩は処刑がありませんでした。")
                elif action_type == "none":
                     st.info("このターンでは、特に必要なアクションはありませんでした。")

                # 次へ進むボタン
                if st.button("次のプレイヤーへ", key=f"next_player_{current_player.name}"):
                    st.session_state[f'action_confirmed_{current_player_index}'] = False # Reset flag for the current player index logic
                    st.session_state.current_player_index = current_player_index + 1
                    st.rerun()

            # アクションがまだ確定されていない場合 (選択UI表示)
            else:
                action_type = "none" # デフォルト
                selected_target = None
                can_confirm = False

                # 役職に応じたアクションUIを表示
                if current_player.role.name in ["人狼", "占い師", "偽占い師", "騎士"]:
                    target_options = []
                    action_label = current_player.role.action_description() + "を選んでください:"

                    if current_player.role.name == "人狼":
                        target_options = [p.name for p in alive_players if p.role.species() != "人狼"]
                        action_type = "attack"
                    elif current_player.role.name == "占い師" or current_player.role.name == "偽占い師":
                        target_options = [p.name for p in alive_players if p.name != current_player.name]
                        action_type = "seer" # 偽占い師もタイプは seer で統一？要検討
                    elif current_player.role.name == "騎士":
                        target_options = [p.name for p in alive_players if p.name != current_player.name]
                        action_type = "guard"

                    if not target_options:
                        st.info("選択できる対象がいません。")
                        can_confirm = True # 対象がいなくても確定はできる
                    else:
                        selected_target = st.selectbox(
                            action_label,
                            options=["選択してください"] + target_options,
                            index=0,
                            key=f"action_target_{current_player.name}"
                        )
                        can_confirm = selected_target != "選択してください"

                elif current_player.role.name == "霊媒師":
                    action_type = "medium"
                    can_confirm = True # 表示を確認したら進める
                    # 霊媒結果は確定後に表示するため、ここでは表示しない

                else: # 村人などアクションUI不要な役職
                    action_type = "none"
                    can_confirm = True
                    st.write("あなたのアクションは自動的に処理されるか、現在はありません。")

                # アクション完了ボタン
                button_label = "アクションを確定する" if current_player.role.name not in ["霊媒師"] else "結果を確認する"
                if st.button(button_label, key=f"confirm_action_{current_player.name}", disabled=not can_confirm):
                    action_data = {"type": action_type}
                    valid_action = True

                    if action_type in ["attack", "seer", "guard"]:
                        if selected_target and selected_target != "選択してください":
                            action_data["target"] = selected_target
                        elif not target_options: # 選択肢がなかった場合は target なしで OK
                            pass
                        else:
                            st.error("対象を選択してください。")
                            valid_action = False

                    if valid_action:
                        # アクションデータを保存
                        st.session_state.night_actions[current_player.name] = action_data
                        # 確定フラグを立てる
                        st.session_state[f'action_confirmed_{current_player_index}'] = True
                        # 再実行して結果表示/次のプレイヤーへボタンを表示
                        st.rerun()

        else: # action_required が False の場合 (騎士の初日など)
            st.info("このターンでは、特に必要なアクションはありません。")
            if st.button("確認しました", key=f"no_action_confirm_{current_player.name}"):
                st.session_state.night_actions[current_player.name] = {"type": "none"}
                st.session_state[f'action_confirmed_{current_player_index}'] = False # Reset flag
                st.session_state.current_player_index = current_player_index + 1
                st.rerun()
    else:
        st.write("役職を確認してから、アクションを行ってください。")

# --- 昼フェーズ ---
elif st.session_state.stage == 'day_phase':
    gm = st.session_state.game_manager
    st.header(f"ターン {gm.turn}: 昼☀️")

    # --- 夜の結果発表 ---
    st.subheader("夜の結果")
    last_victims = st.session_state.get('last_night_victims', [])
    if not last_victims:
        st.info("昨晩の犠牲者はいませんでした。")
    else:
        st.error(f"昨晩の犠牲者は **{', '.join(last_victims)}** でした。")
        # 犠牲者情報をクリア（表示が重複しないように）
        # st.session_state.last_night_victims = [] # クリアするかどうかは設計次第

    # --- 勝利判定 ---
    victory_info = gm.check_victory()
    if victory_info:
        st.session_state.stage = 'game_over'
        st.success(victory_info["message"]) # 勝利メッセージを表示
        if st.button("結果を見る"):
             st.rerun()
        # rerun しないで待機
        st.stop() # ゲーム終了なので以降の処理は不要

    # --- 生存者表示 ---
    st.subheader("生存者")
    alive_players = gm.get_alive_players()
    alive_player_names = [p.name for p in alive_players]
    st.write(f"{len(alive_player_names)} 人: {', '.join(alive_player_names)}")

    st.markdown("--- ")

    # TODO: 議論時間表示
    st.subheader("議論タイム")
    st.write("（議論タイム表示は開発中です）")

    st.markdown("--- ")

    # --- 投票 --- # TODO を修正
    st.subheader("投票")

    # 投票データを初期化 (または既存のものを利用)
    if 'day_votes' not in st.session_state:
        st.session_state.day_votes = {}

    # 各生存プレイヤーの投票UIを作成
    for player in alive_players:
        voter_name = player.name
        # 投票済みの場合は投票先を表示、未投票の場合は投票を促す
        current_vote = st.session_state.day_votes.get(voter_name)

        with st.expander(f"🗳️ {voter_name} さんの投票" + (f"済み: {current_vote}" if current_vote else " （クリックして投票）"), expanded=(not current_vote)):
            st.write(f"**{voter_name} さん、処刑したい人に投票してください。**")
            vote_options = alive_player_names # 自分を含む生存者全員が選択肢
            
            # ラジオボタンで投票
            voted_name = st.radio(
                 "投票先:",
                 options=vote_options,
                 key=f"vote_radio_{voter_name}",
                 index=None, # デフォルト未選択
                 # horizontal=True, # 横並びにする場合
                 label_visibility="collapsed" # ラベル「投票先:」を非表示にする場合
            )
            
            # 投票ボタン（選択したら押せるように）
            if st.button(f"{voter_name} として投票を確定する", key=f"vote_confirm_{voter_name}", disabled=(not voted_name)):
                st.session_state.day_votes[voter_name] = voted_name
                st.success(f"{voter_name} さんは {voted_name} さんに投票しました。Expander を閉じてください。")
                st.rerun() # 投票状態を expander ラベルに反映させる

    st.markdown("--- ")

    # --- 投票締め切りと処刑実行 ---
    # 全員の投票が完了したかチェック
    all_voted = len(st.session_state.day_votes) == len(alive_players)
    if all_voted:
        st.subheader("投票結果")
        # 投票結果を集計して表示 (Counter を使うと便利)
        from collections import Counter
        vote_counts = Counter(st.session_state.day_votes.values())
        st.write("各プレイヤーへの得票数:")
        for name, count in vote_counts.most_common():
            st.write(f"- {name}: {count} 票")

        if st.button("投票を締め切り、処刑を実行する"):
            # 処刑実行
            executed_name = gm.execute_day_vote(vote_counts)
            st.session_state.last_executed_name = executed_name

            if executed_name:
                 st.error(f"**{executed_name}** さんが処刑されました。")
            else:
                 st.info("本日は処刑はありませんでした。")

            # 勝利判定 (処刑後)
            victory_info_after_vote = gm.check_victory()
            if victory_info_after_vote:
                 st.session_state.stage = 'game_over'
                 st.success(victory_info_after_vote["message"]) # 勝利メッセージを表示
                 if st.button("最終結果へ"):
                     st.rerun()
                 st.stop() # ゲーム終了
            else:
                 # ゲーム続行 -> 夜フェーズへ自動遷移
                 st.info("投票結果に基づき、夜フェーズへ移行します。")
                 st.session_state.stage = 'night_phase'
                 st.session_state.game_manager.turn += 1
                 st.session_state.current_player_index = 0
                 st.session_state.night_actions = {}
                 st.session_state.day_votes = {}
                 # 少し待ってから再実行 (メッセージ確認用)
                 time.sleep(1.5) # 1.5秒待つ
                 st.rerun()
                 # rerun しない (st.stop()かst.rerun()が呼ばれるため)

    else:
        st.info(f"投票状況: {len(st.session_state.day_votes)} / {len(alive_players)} 人")

    # 仮の遷移ボタンは削除 (投票完了後に自動遷移するため)
    # if st.button("夜へ進む（仮）"):
    #     st.session_state.stage = 'night_phase'
    # ... (略)


# --- ゲーム終了 ---
elif st.session_state.stage == 'game_over':
    st.header("ゲーム終了🏁")
    
    # 勝利メッセージの再表示 (必要なら)
    if 'game_manager' in st.session_state and st.session_state.game_manager.victory_team:
         st.balloons()
         # check_victory で表示済みだが、念のためここでも表示しても良い
         # victory_info = st.session_state.game_manager.check_victory() # 再度呼び出すか、保存しておいたメッセージを使う
         # if victory_info:
         #    st.subheader(victory_info["message"])
         st.subheader(f"🎉 {st.session_state.game_manager.victory_team} 陣営の勝利！ 🎉")
    else:
         # check_victory が None を返した場合など (通常は起こらないはず)
         st.warning("勝敗が正常に判定できませんでした。")

    # --- 結果表示 ---
    if 'game_manager' in st.session_state:
        st.subheader("最終結果")
        game_results = st.session_state.game_manager.get_game_results()
        # pandas DataFrame に変換して表示すると見やすい
        try:
            import pandas as pd
            df_results = pd.DataFrame(game_results)
            # 列の順番を指定
            df_results = df_results[["名前", "役職", "陣営", "生死", "勝利"]]
            st.dataframe(df_results, hide_index=True)
        except ImportError:
            # pandas がない場合は st.table で表示 (少し簡素になる)
            st.table(game_results)
    
    st.markdown("--- ")
    # --- 新しいゲームボタン ---
    if st.button("新しいゲームを始める"):
         # 状態を完全にリセットして初期設定へ
         keys_to_delete = list(st.session_state.keys())
         for key in keys_to_delete:
             del st.session_state[key]
         # stage も削除したので、次の rerun で初期化ブロックが実行される
         st.rerun()

# --- どのステージにも当てはまらない場合 (念のため) ---
else:
    st.error("不明なアプリケーションステージです。リセットします。")
    # 状態をリセットして再実行
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun() 