# Streamlit 人狼ゲーム アプリ
import streamlit as st
import sys
import os
# pandas は game_over_ui でのみ使用
# from collections import Counter # day_ui でのみ使用

# プロジェクトルートを Python パスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

# game, config モジュールをインポート
try:
    # GameManager は confirm_setup でのみ使用
    from game.game_manager import GameManager
    from game.player import Player
    from game.role import role_dict # setup_ui で使用
    import config.settings as settings
except ImportError as e:
    st.error(f"モジュールのインポートに失敗しました: {e}")
    st.error("プロジェクト構造を確認し、必要なファイルが存在するか確認してください。")
    st.stop()

# UI モジュールをインポート
try:
    from ui.setup_ui import render_initial_setup, render_role_setup, render_confirm_setup
    from ui.night_ui import render_night_phase
    from ui.day_ui import render_day_phase
    from ui.game_over_ui import render_game_over
except ImportError as e:
    st.error(f"UIモジュールのインポートに失敗しました: {e}")
    st.error("プロジェクト構造を確認し、ui ディレクトリとファイルが存在するか確認してください。")
    st.stop()

# --- 定数 ---
# AVAILABLE_ROLES は setup_ui へ移動
# MIN_PLAYERS は setup_ui へ移動

# --- セッション状態の初期化 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'initial_setup'
    # player_count, player_names, role_counts は setup UI 内で初期化/管理
    st.session_state.player_count = 0 # 初期化を元に戻す
    st.session_state.player_names = [] # 初期化を元に戻す
    # st.session_state.role_counts = {} # これは role_setup で初期化
    st.session_state.error_message = "" # これは setup UI でも使う可能性あり

# --- アプリケーションのタイトル ---
st.title("人狼ゲーム🐺")

# --- ステージに応じたUIの描画 ---
if st.session_state.stage == 'initial_setup':
    render_initial_setup()

elif st.session_state.stage == 'role_setup':
    render_role_setup()

elif st.session_state.stage == 'confirm_setup':
    render_confirm_setup()

elif st.session_state.stage == 'night_phase':
    # GameManager の存在チェック
    if 'game_manager' not in st.session_state:
        st.error("ゲーム状態が不正です。設定画面に戻ります。")
        st.session_state.stage = 'initial_setup'
        st.rerun()
    else:
        render_night_phase()

elif st.session_state.stage == 'day_phase':
    # GameManager の存在チェック
    if 'game_manager' not in st.session_state:
        st.error("ゲーム状態が不正です。設定画面に戻ります。")
        st.session_state.stage = 'initial_setup'
        st.rerun()
    else:
        render_day_phase()

elif st.session_state.stage == 'game_over':
    # GameManager の存在チェックは render_game_over 内で行われる
    render_game_over()

# --- どのステージにも当てはまらない場合 (念のため) ---
else:
    st.error("不明なアプリケーションステージです。リセットします。")
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
