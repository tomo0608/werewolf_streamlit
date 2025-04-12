import os

def clear_screen():
    """画面をクリアする関数"""
    os.system('cls' if os.name == 'nt' else 'clear')
    # pass # 今回は画面クリアを行わない