import streamlit as st
from game.role import role_dict
import config.settings as settings

# role_dict から AVAILABLE_ROLES を定義
AVAILABLE_ROLES = list(role_dict.keys())

MIN_PLAYERS = 3

def render_initial_setup():
    """プレイヤー数と名前の設定UIを描画する"""
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


def render_role_setup():
    """役職設定のUIを描画する"""
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


def render_confirm_setup():
    """設定確認画面のUIを描画する"""
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
            from game.game_manager import GameManager # GameManagerをここでインポート
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