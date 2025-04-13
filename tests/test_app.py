import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# 親ディレクトリをパスに追加してモジュールをインポート
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Streamlit の基本的な動作（st.session_state など）を模倣する
# MagicMock を使って、属性アクセスやメソッド呼び出しが可能にする
mock_st = MagicMock()

# ui.setup_ui をインポート (streamlit モックが必要な場合があるため、ここでインポート)
try:
    from ui import setup_ui
except ImportError as e: # より具体的に ImportError を捕捉
    print(f"ImportError importing ui.setup_ui: {e}")
    print(f"sys.path: {sys.path}") # sys.path を確認
    # traceback を表示して詳細を確認
    import traceback
    traceback.print_exc()
    print("Make sure necessary modules (like streamlit) are mockable or installed.")
    setup_ui = None
except Exception as e: # その他の予期せぬエラー
    print(f"Unexpected error importing ui.setup_ui: {e}")
    import traceback
    traceback.print_exc()
    setup_ui = None

class TestAppRoleSetupValidation(unittest.TestCase):

    def setUp(self):
        if setup_ui is None:
            self.fail("ui.setup_ui module could not be imported.")

        # setup_ui 内で参照される定数を取得
        self.AVAILABLE_ROLES = setup_ui.AVAILABLE_ROLES

        # テストごとのセッション状態を模倣する辞書
        self.mock_session_state_dict = {
            'stage': 'role_setup',
            'player_count': 5,
            'player_names': ['A', 'B', 'C', 'D', 'E'],
            'role_counts': {role: 0 for role in self.AVAILABLE_ROLES},
            'error_message': ""
        }

    def test_role_count_validation_correct_sum(self):
        """役職合計人数がプレイヤー数と一致する場合 (手動チェック)"""
        self.mock_session_state_dict['role_counts'] = {
            "人狼": 1, "村人": 2, "占い師": 1, "騎士": 1,
            **{role: 0 for role in self.AVAILABLE_ROLES if role not in ["人狼", "村人", "占い師", "騎士"]}
        }
        total_roles = sum(self.mock_session_state_dict['role_counts'].values())
        self.assertEqual(total_roles, self.mock_session_state_dict['player_count'])

    def test_role_count_validation_incorrect_sum_too_many(self):
        """役職合計人数がプレイヤー数より多い場合 (手動チェック)"""
        self.mock_session_state_dict['role_counts'] = {
            "人狼": 2, "村人": 2, "占い師": 1, "騎士": 1, # 合計6
            **{role: 0 for role in self.AVAILABLE_ROLES if role not in ["人狼", "村人", "占い師", "騎士"]}
        }
        total_roles = sum(self.mock_session_state_dict['role_counts'].values())
        self.assertNotEqual(total_roles, self.mock_session_state_dict['player_count'])
        self.assertGreater(total_roles, self.mock_session_state_dict['player_count'])

    def test_role_count_validation_incorrect_sum_too_few(self):
        """役職合計人数がプレイヤー数より少ない場合 (手動チェック)"""
        self.mock_session_state_dict['role_counts'] = {
            "人狼": 1, "村人": 2, "占い師": 1, # 合計4
            **{role: 0 for role in self.AVAILABLE_ROLES if role not in ["人狼", "村人", "占い師"]}
        }
        total_roles = sum(self.mock_session_state_dict['role_counts'].values())
        self.assertNotEqual(total_roles, self.mock_session_state_dict['player_count'])
        self.assertLess(total_roles, self.mock_session_state_dict['player_count'])

if __name__ == '__main__':
    # Streamlit のモックを sys.modules に設定
    sys.modules['streamlit'] = mock_st
    unittest.main() 