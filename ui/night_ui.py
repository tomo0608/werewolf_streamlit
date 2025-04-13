import streamlit as st

def render_night_phase():
    """夜フェーズのUIを描画する"""
    gm = st.session_state.game_manager
    st.header(f"ターン {gm.turn}: 夜🔮")

    alive_players = gm.get_alive_players()
    current_player_index = st.session_state.get('current_player_index', 0)
    action_confirmed_for_current_player = st.session_state.get(f'action_confirmed_{current_player_index}', False)

    # 全員の夜アクションが完了したかチェック
    if current_player_index >= len(alive_players):
        # 夜のアクション結果を解決
        night_results = gm.resolve_night_actions(st.session_state.night_actions)
        # 結果をセッション状態に保存 (昼フェーズで表示するため)
        st.session_state.last_night_victims = night_results.get("victims", [])
        st.session_state.last_night_immoral_suicides = night_results.get("immoral_suicides", [])
        # 必要ならデバッグログも保存
        # st.session_state.last_night_debug_log = night_results.get("debug")

        # 勝利判定
        victory_info = gm.check_victory()
        # ★★★ ターンを進め、状態を昼に移行 ★★★
        gm.turn += 1
        st.session_state.stage = 'day_phase'
        # 昼フェーズ用の状態をリセット
        st.session_state.day_votes = {} # 投票情報をリセット
        st.session_state.execution_processed = False # 処刑済みフラグをリセット
        if 'last_execution_result' in st.session_state:
            del st.session_state.last_execution_result # 前の昼の結果をクリア
        # 夜アクション確認用フラグをクリア
        for i in range(len(alive_players)):
            if f'action_confirmed_{i}' in st.session_state:
                del st.session_state[f'action_confirmed_{i}']

        st.success("全員の夜のアクションが完了しました。")
            # 「昼へ進む」ボタンでリランし、昼画面を表示
        if st.button("昼へ進む"):
            if gm.debug_mode:
                st.write(f"DEBUG: Proceeding to Day {gm.turn}")
            st.rerun()
        st.stop() # ボタン押下待ち

    # --- (現在アクションするプレイヤーの処理 - 変更なし) --- 
    else:
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