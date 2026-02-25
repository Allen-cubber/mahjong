import random
from typing import List, Dict


class MatchManager:
    def __init__(self):
        # 136张物理牌 (0-135，每4个ID代表同一种牌，例如 0,1,2,3 都是一万)
        self.wall = list(range(136))
        random.shuffle(self.wall)

        # 4名玩家 (0 是人类，1, 2, 3 是 AI)
        self.players = {
            i: {
                "hand_136": [],  # 玩家手里的物理牌
                "discards_136": [],  # 玩家的牌河
                "melds": []  # 副露暂留
            } for i in range(4)
        }

        self.current_turn = 0
        self.dora_indicators = []
        self.dead_tiles_34 = [0] * 34  # 全局计数器，供 AI 算进张用
        self.is_game_over = False
        self.winner = -1

        # 开局发牌
        self._deal_initial_hands()

    def _deal_initial_hands(self):
        """洗牌并给四家发牌"""
        for _ in range(13):
            for i in range(4):
                self.players[i]["hand_136"].append(self.wall.pop())

        # 给庄家 (玩家0) 多发一张，开始回合
        self.players[0]["hand_136"].append(self.wall.pop())

        # 翻开第一张宝牌指示牌
        dora_tile = self.wall.pop()
        self.dora_indicators.append(dora_tile)
        self.dead_tiles_34[dora_tile // 4] += 1

    def get_hand_34(self, player_index: int) -> List[int]:
        """将玩家的 136 格式手牌转换为 AI 引擎需要的 34 计数格式"""
        hand_34 = [0] * 34
        for t in self.players[player_index]["hand_136"]:
            hand_34[t // 4] += 1
        return hand_34

    def get_discards_34(self, player_index: int) -> List[int]:
        """获取玩家打出的牌 (转换为 34 格式方便前端渲染)"""
        return [t // 4 for t in self.players[player_index]["discards_136"]]

    def player_draw(self, player_index: int) -> bool:
        """玩家摸牌，如果牌山空了返回 False (流局)"""
        if not self.wall:
            self.is_game_over = True
            return False
        self.players[player_index]["hand_136"].append(self.wall.pop())
        return True

    def player_discard(self, player_index: int, tile_34: int):
        """玩家打出一张牌 (传入 34 格式 ID，系统自动在手里找对应的物理牌扔掉)"""
        for t in self.players[player_index]["hand_136"]:
            if t // 4 == tile_34:
                self.players[player_index]["hand_136"].remove(t)
                self.players[player_index]["discards_136"].append(t)
                self.dead_tiles_34[tile_34] += 1
                break
        # 轮转回合
        self.current_turn = (self.current_turn + 1) % 4

    def can_call_pon(self, player_index: int, tile_34: int) -> bool:
        """判定某玩家是否可以碰"""
        if player_index == self.current_turn: return False  # 不能碰自己打的
        hand_34 = self.get_hand_34(player_index)
        return hand_34[tile_34] >= 2

    def can_call_kan(self, player_index: int, tile_34: int) -> bool:
        """判定某玩家是否可以明杠"""
        if player_index == self.current_turn: return False
        hand_34 = self.get_hand_34(player_index)
        return hand_34[tile_34] == 3

    def perform_meld(self, player_index: int, tile_34: int, meld_type: str, discarder_index: int):
        """执行副露动作"""
        # 1. 从手中移除相应数量的牌
        num_to_remove = 2 if meld_type == 'pon' else 3
        removed = 0
        for t in list(self.players[player_index]["hand_136"]):
            if t // 4 == tile_34 and removed < num_to_remove:
                self.players[player_index]["hand_136"].remove(t)
                removed += 1

        # 2. 将打出的牌从牌河中捞回，并加入副露区
        if self.players[discarder_index]["discards_136"]:
            self.players[discarder_index]["discards_136"].pop()
            self.dead_tiles_34[tile_34] -= 1  # 牌河计数减1

        self.players[player_index]["melds"].append({"type": meld_type, "tile": tile_34})

        # 3. 记录副露用掉的牌到全局可见池
        # 实际上副露的牌已经全部公开，在计算 AI 进张时应视为死牌
        self.dead_tiles_34[tile_34] += num_to_remove + 1  # (手中2/3张 + 捞回的1张)

        # 4. 鸣牌后，回合直接跳到该玩家，进入其出牌阶段（不摸牌）
        self.current_turn = player_index