import streamlit as st
from collections import Counter

def render_day_phase():
    """昼フェーズのUIを描画する"""
    gm = st.session_state.game_manager # gm を最初に取得
    # デバッグ: day_phase ステージ開始時のフラグ状態確認
    if gm.debug_mode:
        st.write(f"DEBUG: Entering day_phase. execution_processed = {st.session_state.get('execution_processed')}")
    st.header(f"{gm.turn}日目 - 昼☀️")

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
    if 'batch_vote_mode' not in st.session_state:
        st.session_state.batch_vote_mode = False

    # 一括投票モード切り替えチェックボックス
    st.session_state.batch_vote_mode = st.checkbox("一括処刑モード (議論の結果、処刑対象を直接決定)", value=st.session_state.batch_vote_mode)
    st.markdown("--- ") # 区切り線

    # --- 一括処刑モード --- 
    if st.session_state.batch_vote_mode:
        st.info("議論の結果、処刑する対象者を一人選択してください。")
        vote_options = alive_player_names
        selected_target = st.selectbox(
            "処刑対象者:",
            options=[""] + vote_options, # 未選択を許容
            key="batch_execute_target"
        )

        # 処刑実行ボタン (まだ処刑処理が行われていない場合のみ表示)
        if not st.session_state.get("execution_processed", False):
            if st.button("処刑を確定する", disabled=(not selected_target)):
                if selected_target:
                    # 選択された対象者に1票だけ入ったCounterを作成
                    vote_counts = Counter({selected_target: 1})
                    execution_result = gm.execute_day_vote(vote_counts)
                    st.session_state.last_execution_result = execution_result
                    st.session_state.last_executed_name = execution_result.get("executed")
                    st.session_state.execution_processed = True
                    st.success(f"{selected_target} の処刑を決定しました。")
                else:
                    st.warning("処刑対象者を選択してください。")

    # --- 個別投票モード --- 
    else:
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
                    index=vote_options.index(current_vote) if current_vote in vote_options else None,
                    label_visibility="collapsed"
                )

                if voted_name and voted_name != current_vote:
                    st.session_state.day_votes[voter_name] = voted_name
                    st.info(f"{voter_name} さんは {voted_name} さんに投票しました。")
                    st.rerun()

    st.markdown("--- ")

    # --- 投票締め切りと処刑実行ロジック・投票状況表示 (個別投票モード時のみ) ---
    if not st.session_state.batch_vote_mode:
        all_voted = len(st.session_state.day_votes) == len(alive_players)

        if 'execution_processed' not in st.session_state:
            st.session_state.execution_processed = False

        if all_voted:
            st.subheader("投票結果")
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
                    # リラン不要、下の処理で結果が表示される
        else: # まだ全員投票していない場合
            # --- 投票状況の表示エリア (個別投票モード時のみ) --- 
            st.info(f"投票状況: {len(st.session_state.day_votes)} / {len(alive_players)} 人")

    # --- 処刑結果の取得 (共通処理) ---
    execution_result_to_display = None
    if st.session_state.get("execution_processed", False):
        execution_result_to_display = st.session_state.get('last_execution_result')
        if gm.debug_mode:
            st.write(f"DEBUG: Fetched last_execution_result: {execution_result_to_display}")

    # --- 処刑結果の表示エリア (共通処理) --- 
    if execution_result_to_display:
        executed_name = execution_result_to_display.get("executed")
        immoral_suicides = execution_result_to_display.get("immoral_suicides", [])
        retaliation_victim = execution_result_to_display.get("retaliation_victim")
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
            if retaliation_victim:
                st.error(f"**{executed_name}**(猫又) が処刑されたため、**{retaliation_victim}** を道連れにしました。")

    # --- 次のステップへのボタン表示エリア (共通処理) --- 
    if st.session_state.get("execution_processed", False):
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
                st.session_state.current_player_index = 0
                st.session_state.night_actions = {}
                st.session_state.day_votes = {}
                st.session_state.execution_processed = False # フラグをリセット
                if 'last_execution_result' in st.session_state:
                    del st.session_state.last_execution_result # 不要になった結果を削除
                if gm.debug_mode:
                    st.write("DEBUG: About to rerun for night phase.") # DEBUG
                st.rerun() 