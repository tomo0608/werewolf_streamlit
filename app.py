# Streamlit 人狼ゲーム アプリ
import streamlit as st
import sys
import os # os モジュールを追加
import random
import time
import pandas as pd

# プロジェクトルートを Python パスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# game, config モジュールをインポート
try:
    from game.game_manager import GameManager
    from game.player import Player
    from game.role import role_dict
    import config.settings as settings
except ImportError as e:
    st.error(f"モジュールのインポートに失敗しました: {e}")
    st.error("プロジェクト構造を確認し、必要なファイルが存在するか確認してください。")
    st.stop()

# --- 定数 ---
AVAILABLE_ROLES = list(role_dict.keys())
MIN_PLAYERS = 3

# --- セッション状態の初期化 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'initial_setup'
    st.session_state.player_count = 0
    st.session_state.player_names = []
    st.session_state.role_counts = {}
    st.session_state.error_message = ""

# --- アプリケーションのタイトル ---
st.title("人狼ゲーム🐺")

# --- ゲーム設定 (プレイヤー数・名前) ---
if st.session_state.stage == 'initial_setup':
    st.header("ゲーム設定")
    st.session_state.error_message = ""

    # --- プレイヤー数設定 ---
    st.subheader("プレイヤー人数")

    # デフォルト設定の使用
    use_default_count = False
    default_count = getattr(settings, "DEFAULT_PLAYER_COUNT", 0)
    if default_count >= MIN_PLAYERS:
        if st.button(f"デフォルトの {default_count} 人で設定"):
            st.session_state.player_count = default_count
            use_default_count = True
            st.rerun()

    # 数値入力
    current_player_count = st.session_state.player_count if st.session_state.player_count >= MIN_PLAYERS else MIN_PLAYERS
    num_input = st.number_input(
        f"人数を入力してください（{MIN_PLAYERS}人以上）",
        min_value=MIN_PLAYERS,
        value=current_player_count,
        step=1,
        key="player_count_input",
        disabled=use_default_count
    )
    # number_input の値が変更されたら session_state に反映
    if not use_default_count and num_input != st.session_state.player_count:
         st.session_state.player_count = num_input
         st.session_state.player_names = [""] * num_input # 名前入力欄をリセット
         st.rerun()

    # --- プレイヤー名設定 ---
    if st.session_state.player_count >= MIN_PLAYERS:
        st.subheader("プレイヤー名")

        # 名前入力欄を動的に生成
        if len(st.session_state.player_names) != st.session_state.player_count:
             st.session_state.player_names = [""] * st.session_state.player_count

        input_names = []
        cols = st.columns(3)
        for i in range(st.session_state.player_count):
            container = cols[i % 3]
            default_value = st.session_state.player_names[i] or f"プレイヤー{i + 1}"
            name = container.text_input(
                f"プレイヤー{i + 1}",
                value=default_value,
                key=f"player_name_{i}"
            )
            input_names.append(name)

        # 名前が変更されたら session_state に反映
        if input_names != st.session_state.player_names:
             st.session_state.player_names = input_names

        # --- 設定確定ボタン ---
        if st.button("役職設定へ進む"):
            # 入力チェック
            valid = True
            if not st.session_state.player_names:
                st.session_state.error_message = "プレイヤー名が設定されていません。"
                valid = False
            elif "" in st.session_state.player_names:
                st.session_state.error_message = "すべてのプレイヤー名を入力してください。"
                valid = False
            elif len(set(st.session_state.player_names)) != st.session_state.player_count:
                st.session_state.error_message = "プレイヤー名が重複しています。"
                valid = False

            if valid:
                st.session_state.stage = 'role_setup'
                st.session_state.error_message = ""
                st.rerun()
            else:
                 st.rerun()

    # エラーメッセージ表示
    if st.session_state.error_message:
        st.error(st.session_state.error_message)


# --- ゲーム設定 (役職) ---
elif st.session_state.stage == 'role_setup':
    st.header("役職設定")
    st.write(f"プレイヤー数: {st.session_state.player_count} 人")
    st.write(f"プレイヤー名: {', '.join(st.session_state.player_names)}")
    st.session_state.error_message = ""

    # --- デフォルト役職構成の使用 ---
    use_default_roles = False
    default_roles_valid = False
    default_role_counts = getattr(settings, "DEFAULT_ROLE_COUNTS", {})
    if default_role_counts and sum(default_role_counts.values()) == st.session_state.player_count:
        default_roles_valid = True
        if st.button("デフォルトの役職構成を使用"):
            st.session_state.role_counts = default_role_counts.copy()
            use_default_roles = True
            st.rerun()

    # --- 役職人数入力 ---
    st.subheader("各役職の人数")

    # session_state に role_counts がなければ初期化
    if 'role_counts' not in st.session_state or not st.session_state.role_counts:
         st.session_state.role_counts = {role: 0 for role in AVAILABLE_ROLES}
         if default_roles_valid and not use_default_roles:
              st.session_state.role_counts = default_role_counts.copy()

    input_role_counts = {}
    current_total = 0
    cols = st.columns(3)
    for i, role in enumerate(AVAILABLE_ROLES):
        container = cols[i % 3]
        current_value = st.session_state.role_counts.get(role, 0)
        temp_total = sum(st.session_state.role_counts.get(r, 0) for r in AVAILABLE_ROLES if r != role)
        max_value_for_role = st.session_state.player_count - temp_total

        count = container.number_input(
            role,
            min_value=0,
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
        if st.button("設定を確認する", disabled=(remaining_players != 0)):
            if sum(st.session_state.role_counts.values()) == st.session_state.player_count:
                st.session_state.stage = 'confirm_setup'
                st.session_state.error_message = ""
                st.rerun()
            else:
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
    
    # デバッグモードのチェックボックスをボタンの前に配置
    debug_mode = st.checkbox("デバッグモード (ログ詳細表示)", value=st.session_state.get("debug_mode_enabled", False), 
                             key="debug_mode_checkbox", 
                             help="有効にすると、ゲーム進行のデバッグ情報が表示されます")
    # チェックボックスの状態をセッションに保存
    st.session_state.debug_mode_enabled = debug_mode

    col1, col2 = st.columns(2)
    with col1:
        if st.button("ゲーム開始！"):
            player_names = st.session_state.player_names
            role_counts = st.session_state.role_counts
            roles = []
            for role_name, count in role_counts.items():
                roles.extend([role_name] * count)

            # セッション状態からデバッグモード設定を読み込む
            current_debug_mode = st.session_state.get("debug_mode_enabled", False)
            game_manager = GameManager(player_names, debug_mode=current_debug_mode)
            game_manager.assign_roles(roles)

            st.session_state.game_manager = game_manager
            st.session_state.stage = 'night_phase'
            st.session_state.current_player_index = 0
            st.session_state.night_actions = {}
            st.rerun()
    with col2:
        if st.button("役職設定に戻る"):
            st.session_state.stage = 'role_setup'
            # 戻る際にデバッグモード設定もリセット（任意）
            if 'debug_mode_enabled' in st.session_state:
                del st.session_state.debug_mode_enabled
            if 'game_manager' in st.session_state:
                 del st.session_state.game_manager
            st.rerun()

# --- 夜フェーズ ---
elif st.session_state.stage == 'night_phase':
    gm = st.session_state.game_manager
    st.header(f"ターン {gm.turn}: 夜🔮")

    alive_players = gm.get_alive_players()
    current_player_index = st.session_state.get('current_player_index', 0)
    action_confirmed_for_current_player = st.session_state.get(f'action_confirmed_{current_player_index}', False)

    # 全員の夜アクションが完了したかチェック
    if current_player_index >= len(alive_players):
        # 夜のアクション結果を解決
        night_results = gm.resolve_night_actions(st.session_state.night_actions)
        victim_names = night_results.get("victims", [])
        immoral_suicides = night_results.get("immoral_suicides", [])
        # debug_log = night_results.get("debug") # 必要ならデバッグログも表示
        
        st.session_state.last_night_victims = victim_names
        st.session_state.last_night_immoral_suicides = immoral_suicides # 後追い自殺者も保存

        st.session_state.stage = 'day_phase'
        st.success("全員の夜のアクションが完了しました。昼フェーズへ移行します。")
        for i in range(len(alive_players)):
            if f'action_confirmed_{i}' in st.session_state:
                del st.session_state[f'action_confirmed_{i}']
        if st.button("昼へ進む"):
            st.rerun()
        st.stop()

    # 現在アクションするプレイヤーを取得
    if current_player_index < len(alive_players):
        current_player = alive_players[current_player_index]
    else:
        st.warning("プレイヤーインデックスエラー。リセットします。")
        st.session_state.stage = 'initial_setup'
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
                            # 偽占い師の結果生成ロジックは Role 側に実装済み
                            if current_player.role.name == "偽占い師":
                                seer_result = current_player.role.fake_seer_result()
                                st.info(f"占い結果（偽）: **{selected_target}** さんは **{seer_result}** です。")
                            else:
                                seer_result = target_player.role.seer_result()
                                st.info(f"占い結果: **{selected_target}** さんは **{seer_result}** です。")
                        else:
                            st.error("対象プレイヤーが見つかりませんでした。")

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
                    st.session_state[f'action_confirmed_{current_player_index}'] = False
                    st.session_state.current_player_index = current_player_index + 1
                    st.rerun()

            # アクションがまだ確定されていない場合 (選択UI表示)
            else:
                action_type = "none"
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
                        action_type = "seer"
                    elif current_player.role.name == "騎士":
                        target_options = [p.name for p in alive_players if p.name != current_player.name]
                        action_type = "guard"

                    if not target_options:
                        st.info("選択できる対象がいません。")
                        can_confirm = True
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
                    can_confirm = True

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
                        elif not target_options:
                            pass
                        else:
                            st.error("対象を選択してください。")
                            valid_action = False

                    if valid_action:
                        st.session_state.night_actions[current_player.name] = action_data
                        st.session_state[f'action_confirmed_{current_player_index}'] = True
                        st.rerun()

        else: # action_required が False の場合 (騎士の初日など)
            st.info("このターンでは、特に必要なアクションはありません。")
            if st.button("確認しました", key=f"no_action_confirm_{current_player.name}"):
                st.session_state.night_actions[current_player.name] = {"type": "none"}
                st.session_state[f'action_confirmed_{current_player_index}'] = False
                st.session_state.current_player_index = current_player_index + 1
                st.rerun()
    else:
        st.write("役職を確認してから、アクションを行ってください。")

# --- 昼フェーズ ---
elif st.session_state.stage == 'day_phase':
    gm = st.session_state.game_manager # gm を最初に取得
    # デバッグ: day_phase ステージ開始時のフラグ状態確認
    if gm.debug_mode:
        st.write(f"DEBUG: Entering day_phase. execution_processed = {st.session_state.get('execution_processed')}") 
    st.header(f"ターン {gm.turn}: 昼☀️")

    # --- 夜の結果発表 ---
    st.subheader("夜の結果")
    last_victims = st.session_state.get('last_night_victims', [])
    last_immoral_suicides = st.session_state.get('last_night_immoral_suicides', [])
    
    victim_message_parts = []
    if last_victims:
        victim_message_parts.append(f"昨晩の犠牲者は **{', '.join(last_victims)}** でした。")
    if last_immoral_suicides:
        victim_message_parts.append(f"妖狐が死亡したため、**{', '.join(last_immoral_suicides)}** が後を追いました。")
    
    if victim_message_parts:
        st.error("\n".join(victim_message_parts))
    else:
        st.info("昨晩は誰も死亡しませんでした。")

    # --- 最初の勝利判定 (夜の結果を受けて) ---
    victory_info = gm.check_victory()
    if victory_info:
        st.session_state.stage = 'game_over'
        st.success(victory_info["message"])
        if st.button("結果を見る"):
             st.rerun()
        st.stop()

    # --- 生存者表示 ---
    st.subheader("生存者")
    alive_players = gm.get_alive_players()
    alive_player_names = [p.name for p in alive_players]
    st.write(f"{len(alive_player_names)} 人: {', '.join(alive_player_names)}")

    st.markdown("--- ")

    # 議論時間表示
    st.subheader("議論タイム")
    discussion_time = st.slider("議論時間 (分)", min_value=1, max_value=10, value=3, step=1)
    discussion_seconds = discussion_time * 60
    timer_container = st.empty()
    timer_html = f"""
    <div style="background-color:#f0f0f0; padding:10px; border-radius:5px; text-align:center; margin-bottom:10px;">
      <h3 id="timer">{discussion_time}:00</h3>
    </div>
    <button id="start-timer" style="background-color:#4CAF50; color:white; border:none; padding:10px 20px; 
     border-radius:5px; cursor:pointer; margin-right:10px;">開始</button>
    <button id="reset-timer" style="background-color:#f44336; color:white; border:none; padding:10px 20px; 
     border-radius:5px; cursor:pointer;">リセット</button>
    
    <script>
    let timerInterval;
    let seconds = {discussion_seconds};
    let isRunning = false;
    
    function updateTimerDisplay() {{
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      document.getElementById('timer').textContent = 
        `${{minutes}}:${{remainingSeconds < 10 ? '0' : ''}}${{remainingSeconds}}`;
    }}
    
    document.getElementById('start-timer').addEventListener('click', function() {{
      if (!isRunning) {{
        isRunning = true;
        this.textContent = '一時停止';
        this.style.backgroundColor = '#2196F3';
        
        timerInterval = setInterval(function() {{
          if (seconds > 0) {{
            seconds--;
            updateTimerDisplay();
          }} else {{
            clearInterval(timerInterval);
            document.getElementById('timer').textContent = '時間切れ！';
            document.getElementById('timer').style.color = 'red';
            document.getElementById('start-timer').disabled = true;
            document.getElementById('start-timer').style.backgroundColor = '#cccccc';
          }}
        }}, 1000);
      }} else {{
        isRunning = false;
        this.textContent = '再開';
        this.style.backgroundColor = '#4CAF50';
        clearInterval(timerInterval);
      }}
    }});
    
    document.getElementById('reset-timer').addEventListener('click', function() {{
      clearInterval(timerInterval);
      seconds = {discussion_seconds};
      updateTimerDisplay();
      isRunning = false;
      document.getElementById('start-timer').textContent = '開始';
      document.getElementById('start-timer').style.backgroundColor = '#4CAF50';
      document.getElementById('start-timer').disabled = false;
      document.getElementById('timer').style.color = 'black';
    }});
    </script>
    """
    with timer_container:
        st.components.v1.html(timer_html, height=150)

    st.markdown("--- ")

    # --- 投票 ---
    st.subheader("投票")
    if 'day_votes' not in st.session_state:
        st.session_state.day_votes = {}
    for player in alive_players:
        voter_name = player.name
        current_vote = st.session_state.day_votes.get(voter_name)
        with st.expander(f"🗳️ {voter_name} さんの投票" + (f"済み: {current_vote}" if current_vote else " （クリックして投票）"), expanded=(not current_vote)):
            st.write(f"**{voter_name} さん、処刑したい人に投票してください。**")
            vote_options = alive_player_names

            voted_name = st.radio(
                 "投票先:",
                 options=vote_options,
                 key=f"vote_radio_{voter_name}",
                 index=None,
                 label_visibility="collapsed"
            )

            if st.button(f"{voter_name} として投票を確定する", key=f"vote_confirm_{voter_name}", disabled=(not voted_name)):
                st.session_state.day_votes[voter_name] = voted_name
                st.success(f"{voter_name} さんは {voted_name} さんに投票しました。Expander を閉じてください。")
                st.rerun()

    st.markdown("--- ")

    # --- 投票締め切りと処刑実行ロジック ---
    all_voted = len(st.session_state.day_votes) == len(alive_players)
    execution_result_to_display = None # 表示用結果を初期化
    
    if 'execution_processed' not in st.session_state:
        st.session_state.execution_processed = False

    if all_voted:
        st.subheader("投票結果")
        from collections import Counter
        vote_counts = Counter(st.session_state.day_votes.values())
        st.write("各プレイヤーへの得票数:")
        for name, count in vote_counts.most_common():
            st.write(f"- {name}: {count} 票")
        st.markdown("--- ")

        # まだ処刑処理が行われていない場合のみ、処刑ボタンを表示・処理
        if not st.session_state.execution_processed:
            if st.button("投票を締め切り、処刑を実行する"):
                execution_result = gm.execute_day_vote(vote_counts)
                st.session_state.last_execution_result = execution_result 
                st.session_state.last_executed_name = execution_result.get("executed")
                st.session_state.execution_processed = True
                if gm.debug_mode:
                    st.write("DEBUG: Setting execution_processed to True. No rerun here.") 
                # ここではリランしない
        
        # 処刑処理済みの場合、表示用の結果を取得
        if st.session_state.execution_processed:
             execution_result_to_display = st.session_state.get('last_execution_result')
             if gm.debug_mode:
                 st.write(f"DEBUG: Fetched last_execution_result: {execution_result_to_display}") # DEBUG

    # --- 処刑結果の表示エリア --- 
    if execution_result_to_display:
        if gm.debug_mode:
            st.write("DEBUG: Displaying execution results area.") # DEBUG
        executed_name = execution_result_to_display.get("executed")
        immoral_suicides = execution_result_to_display.get("immoral_suicides", [])
        error_message = execution_result_to_display.get("error")

        if error_message:
            st.error(f"処刑処理エラー: {error_message}")
        else:
            if executed_name:
                 st.error(f"**{executed_name}** さんが処刑されました。")
            else:
                 st.info("本日は処刑はありませんでした。")
            if immoral_suicides:
                st.warning(f"妖狐が処刑されたため、**{', '.join(immoral_suicides)}** が後を追いました。")
    
    # --- 次のステップへのボタン表示エリア --- 
    # (処刑処理済み かつ ゲームオーバーでない かつ エラーがない場合)
    if st.session_state.execution_processed: 
        victory_info_after_vote = gm.check_victory() # 処刑後の勝利判定
        if gm.debug_mode:
            st.write(f"DEBUG: Victory Check Result after vote: {victory_info_after_vote}") # DEBUG
        error_occurred = execution_result_to_display and execution_result_to_display.get("error")

        if victory_info_after_vote:
             st.session_state.stage = 'game_over'
             st.success(victory_info_after_vote["message"])
             if st.button("最終結果へ", key="go_to_results_button"):
                 st.rerun()
             st.stop()
        elif not error_occurred:
            if gm.debug_mode:
                st.write("DEBUG: Trying to show 'Proceed to Night' button.") # DEBUG
            if st.button("夜へ進む", key="proceed_to_night_button"):
                if gm.debug_mode:
                    st.warning("DEBUG: 'Proceed to Night' button clicked!") 
                st.info("夜フェーズへ移行します。") 
                st.session_state.stage = 'night_phase'
                if gm.debug_mode:
                    st.write(f"DEBUG: Set stage to {st.session_state.stage}") 
                st.session_state.game_manager.turn += 1
                st.session_state.current_player_index = 0
                st.session_state.night_actions = {}
                st.session_state.day_votes = {}
                st.session_state.execution_processed = False # フラグをリセット
                if 'last_execution_result' in st.session_state:
                    del st.session_state.last_execution_result # 不要になった結果を削除
                if gm.debug_mode:
                    st.write("DEBUG: About to rerun for night phase.") # DEBUG
                st.rerun()

    # --- 投票状況の表示エリア (全員投票前) ---
    elif not all_voted: 
        st.info(f"投票状況: {len(st.session_state.day_votes)} / {len(alive_players)} 人")


# --- ゲーム終了 ---
elif st.session_state.stage == 'game_over':
    st.header("ゲーム終了🏁")

    if 'game_manager' in st.session_state and st.session_state.game_manager.victory_team:
         st.balloons()
         st.subheader(f"🎉 {st.session_state.game_manager.victory_team} 陣営の勝利！ 🎉")
    else:
         st.warning("勝敗が正常に判定できませんでした。")

    # --- 結果表示 ---
    if 'game_manager' in st.session_state:
        st.subheader("最終結果")
        game_results = st.session_state.game_manager.get_game_results()
        try:
            df_results = pd.DataFrame(game_results)
            df_results = df_results[["名前", "役職", "陣営", "生死", "勝利"]]
            st.dataframe(df_results, hide_index=True)
        except ImportError:
            st.table(game_results)

    st.markdown("--- ")
    # --- 新しいゲームボタン ---
    if st.button("新しいゲームを始める"):
         keys_to_delete = list(st.session_state.keys())
         for key in keys_to_delete:
             del st.session_state[key]
         st.rerun()

# --- どのステージにも当てはまらない場合 (念のため) ---
else:
    st.error("不明なアプリケーションステージです。リセットします。")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun() 