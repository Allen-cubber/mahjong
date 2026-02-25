from typing import List, Dict, Optional


class TileConst:
    """
    常量类：为了代码可读性，定义字牌的索引
    0-8: 万 (1m-9m)
    9-17: 筒 (1p-9p)
    18-26: 索 (1s-9s)
    27-33: 字牌 (东 南 西 北 白 发 中)
    """
    EAST, SOUTH, WEST, NORTH = 27, 28, 29, 30
    HAKU, HATSU, CHUN = 31, 32, 33


class Meld:
    """
    副露类：记录吃、碰、杠的信息
    """

    def __init__(self, meld_type: str, tiles: List[int]):
        # type 包含: 'chi' (吃), 'pon' (碰), 'kan' (大明杠/加杠), 'ankan' (暗杠)
        self.type = meld_type
        self.tiles = tiles  # 组成该副露的牌 ID 列表


class PlayerState:
    """
    玩家状态类：记录单个玩家在局中的所有信息
    """

    def __init__(self, seat_wind: int):
        self.seat_wind: int = seat_wind  # 自风 (27-30)
        self.score: int = 25000  # 当前点数

        # 核心手牌结构：长度为 34 的数组，索引为牌ID，值为该牌在手里的数量
        self.hand: List[int] = [0] * 34

        self.discards: List[int] = []  # 牌河：按打出顺序记录牌 ID
        self.melds: List[Meld] = []  # 副露列表

        self.is_riichi: bool = False  # 是否已立直
        self.is_furiten: bool = False  # 是否处于振听状态（通常由引擎动态计算后更新到这里）

    def add_tile_to_hand(self, tile_id: int):
        """摸牌入局"""
        self.hand[tile_id] += 1

    def discard_tile(self, tile_id: int):
        """打出牌"""
        if self.hand[tile_id] > 0:
            self.hand[tile_id] -= 1
            self.discards.append(tile_id)
        else:
            raise ValueError(f"手里没有这张牌(ID:{tile_id})，无法打出！")


class GameState:
    """
    全局状态类：维护整个牌局的公共上下文
    """

    def __init__(self):
        # 初始化 4 个玩家，假设索引 0 是当前视角（你），1下家，2对家，3上家
        # 默认开局座风分配为 东南西北
        self.players: List[PlayerState] = [PlayerState(w) for w in range(27, 31)]

        self.round_wind: int = TileConst.EAST  # 场风（东风局、南风局）
        self.kyoku: int = 1  # 局数（如：东1局）
        self.honba: int = 0  # 本场数（连庄棒）
        self.riichi_sticks: int = 0  # 场上的立直棒数量

        self.tiles_left: int = 70  # 牌山剩余有效牌数 (开局配牌后一般是70)
        self.dora_indicators: List[int] = []  # 宝牌指示牌列表

        # 【核心字段】：全局可见牌计数器。长度34的数组。
        # 包含：所有人打出的牌 + 所有副露 + 宝牌指示牌 + 你自己的手牌
        # 作用：用于计算“真实的剩余进张数量”
        self.visible_tiles: List[int] = [0] * 34

    def record_visible_tile(self, tile_id: int, count: int = 1):
        """
        记录场上变为可见的牌
        """
        self.visible_tiles[tile_id] += count
        # 容错：现实中同一种牌最多只有4张
        if self.visible_tiles[tile_id] > 4:
            self.visible_tiles[tile_id] = 4


