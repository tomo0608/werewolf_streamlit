import streamlit as st
import pandas as pd

def render_game_over():
    """ゲーム終了画面のUIを描画する"""
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
            # pandas がない場合のフォールバック
            st.table(game_results)
        except Exception as e:
            st.error(f"結果の表示中にエラーが発生しました: {e}")
            st.write("ゲーム結果データ:", game_results) # デバッグ用に元データを表示


    st.markdown("--- ")
    # --- 新しいゲームボタン ---
    if st.button("新しいゲームを始める"):
         keys_to_delete = list(st.session_state.keys())
         for key in keys_to_delete:
             del st.session_state[key]
         st.rerun() 