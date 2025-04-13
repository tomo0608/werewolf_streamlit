import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

def render_game_over():
    """ゲーム終了画面のUIを描画する"""
    st.header("ゲーム終了🏁")

    if 'game_manager' in st.session_state and st.session_state.game_manager.victory_team:
         st.balloons()
         st.subheader(f"🎉 {st.session_state.game_manager.victory_team} 陣営の勝利！ 🎉")
    else:
         st.warning("勝敗が正常に判定できませんでした。")

    # --- 結果表示 & 保存 ---
    if 'game_manager' in st.session_state:
        st.subheader("最終結果")
        game_results = st.session_state.game_manager.get_game_results()

        # --- 結果の表示 ---
        try:
            df_results = pd.DataFrame(game_results)
            df_results = df_results[["名前", "役職", "陣営", "生死", "勝利"]]
            st.dataframe(df_results, hide_index=True)
        except ImportError:
            # pandas がない場合のフォールバック
            st.table(game_results)
        except Exception as e:
            st.error(f"結果の表示中にエラーが発生しました: {e}")
            st.write("ゲーム結果データ:", game_results) # デバッグ用に元データを表示

        # --- 結果のファイル保存 ---
        try:
            results_dir = "result"
            os.makedirs(results_dir, exist_ok=True) # result ディレクトリがなければ作成
            now = datetime.now()
            filename = now.strftime("%Y%m%d_%H%M%S") + ".json"
            filepath = os.path.join(results_dir, filename)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(game_results, f, ensure_ascii=False, indent=4)
            st.success(f"結果を {filepath} に保存しました。")
        except Exception as e:
            st.error(f"結果の保存中にエラーが発生しました: {e}")

    st.markdown("--- ")
    # --- 新しいゲームボタン ---
    if st.button("新しいゲームを始める"):
         keys_to_delete = list(st.session_state.keys())
         for key in keys_to_delete:
             del st.session_state[key]
         st.rerun() 