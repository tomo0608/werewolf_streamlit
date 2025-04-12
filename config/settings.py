DEFAULT_ROLE_COUNTS = {
    "人狼": 2,
    "村人": 3,
    "占い師": 1,
    "霊媒師": 1,
    "騎士": 1,
    "狂人": 1,
    "狂信者": 0,
    "妖狐": 2,
    "背徳者": 0,
    "偽占い師": 1,
}

DEFAULT_PLAYER_COUNT = sum(DEFAULT_ROLE_COUNTS.values())

DEFAULT_PLAYER_NAMES = [str(i+1) for i in range(DEFAULT_PLAYER_COUNT)]
