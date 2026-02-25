from mahjong.shanten import Shanten
from mahjong.hand_calculating.hand import HandCalculator
from mahjong.hand_calculating.hand_config import HandConfig, OptionalRules
from mahjong.meld import Meld
from typing import List, Dict, Tuple, Optional


class RuleEngine:
    def __init__(self):
        self.shanten_calculator = Shanten()
        self.hand_calculator = HandCalculator()

    # --- 基础工具方法 ---
    def get_shanten(self, hand: List[int]) -> int:
        """计算向听数 (核心方法)"""
        return self.shanten_calculator.calculate_shanten(hand)

    def _calculate_hand_utility(self, hand: List[int], dora_indicators: List[int] = None) -> float:
        """
        计算手牌的战略价值评分 (用于在进张数相等时打破平局)
        权重逻辑：Dora > 中张(2-8) > 幺九/字牌
        """
        score = 0.0

        # 1. 确定当前所有的宝牌 ID (0-33)
        dora_ids = []
        if dora_indicators:
            for raw_id in dora_indicators:
                # 兼容性处理：如果是物理 ID 则转换为种类 ID
                ind = raw_id // 4 if raw_id > 33 else raw_id
                if ind < 27:  # 数牌 (万筒索)
                    dora_ids.append((ind // 9) * 9 + (ind % 9 + 1) % 9)
                elif ind < 31:  # 风牌 (东南西北)
                    dora_ids.append(27 + (ind - 27 + 1) % 4)
                else:  # 三元牌 (白发中)
                    dora_ids.append(31 + (ind - 31 + 1) % 3)

        for t_id in range(34):
            count = hand[t_id]
            if count == 0: continue

            # 权重 A：宝牌持有量 (每张宝牌 +50分)
            if t_id in dora_ids:
                score += count * 50.0

            # 权重 B：中张灵活性 (2-8)
            t_val = t_id % 9
            if t_id < 27 and 1 <= t_val <= 7:
                score += count * 2.0

            # 权重 C：幺九/字牌扣分
            if t_id >= 27 or t_val == 0 or t_val == 8:
                score -= count * 1.0

        return score

    # --- 核心引擎方法 ---

    def evaluate_pure_efficiency(self, hand: List[int], visible_tiles: List[int], dora_indicators: List[int] = None) -> \
            Tuple[int, List[Dict]]:
        """基础纯牌效引擎 (包含二阶评分逻辑)"""
        current_shanten = self.get_shanten(hand)
        best_discards = []

        for discard_tile in range(34):
            if hand[discard_tile] == 0: continue
            hand[discard_tile] -= 1

            shanten_after_discard = self.get_shanten(hand)
            ukeire_details = []
            total_ukeire_count = 0

            for draw_tile in range(34):
                if visible_tiles[draw_tile] >= 4: continue
                hand[draw_tile] += 1
                if self.get_shanten(hand) < shanten_after_discard:
                    real_left = 4 - visible_tiles[draw_tile]
                    if real_left > 0:
                        ukeire_details.append({'tile': draw_tile, 'left_count': real_left})
                        total_ukeire_count += real_left
                hand[draw_tile] -= 1

            # 计算战略价值
            utility = self._calculate_hand_utility(hand, dora_indicators)

            best_discards.append({
                'discard_tile': discard_tile,
                'shanten_after_discard': shanten_after_discard,
                'total_ukeire': total_ukeire_count,
                'quality_score': utility,
                'details': ukeire_details
            })
            hand[discard_tile] += 1

        # 排序：进张有效性 > 向听推进 > 进张数量 > 战略价值
        best_discards.sort(key=lambda x: (
            x['total_ukeire'] > 0,
            -x['shanten_after_discard'],
            x['total_ukeire'],
            x['quality_score']
        ), reverse=True)

        return current_shanten, best_discards

    def calculate_exact_score(self, hand: List[int], win_tile: int, is_riichi: bool = False,
                              melds_data: List[Dict] = None, dora_indicators: List[int] = None,
                              require_yaku: bool = True, round_wind: int = 27, player_wind: int = 28) -> Tuple[
        int, str]:
        """高精度算分引擎"""
        hand_136 = []
        used_counts = [0] * 34

        for t_id in range(34):
            count = hand[t_id]
            for i in range(count): hand_136.append(t_id * 4 + i)
            used_counts[t_id] = count

        win_tile_136 = win_tile * 4 + (used_counts[win_tile] - 1)

        melds_136 = []
        if melds_data:
            for m in melds_data:
                m_type, t_id = m['type'], m['tile']
                start_idx = used_counts[t_id]
                if m_type == 'kan':
                    tiles = [t_id * 4 + i for i in range(4)]
                    melds_136.append(Meld('kan', tiles, False))
                    hand_136.extend(tiles)
                    used_counts[t_id] = 4
                elif m_type == 'pon':
                    tiles = [t_id * 4 + start_idx + i for i in range(3)]
                    melds_136.append(Meld('pon', tiles, True))
                    hand_136.extend(tiles)
                    used_counts[t_id] += 3

        dora_indicators_136 = []
        if dora_indicators:
            for raw_id in dora_indicators:
                # 【核心修复】：物理 ID (0-135) -> 种类 ID (0-33) 的安全转换
                t_id = raw_id // 4 if raw_id > 33 else raw_id

                # 边界防御检查
                if t_id < 0 or t_id >= 34: continue

                start_idx = used_counts[t_id]
                if start_idx < 4:
                    dora_indicators_136.append(t_id * 4 + start_idx)
                    used_counts[t_id] += 1

        config = HandConfig(
            is_tsumo=True, is_riichi=is_riichi, round_wind=round_wind, player_wind=player_wind,
            options=OptionalRules(has_open_tanyao=True)
        )

        result = self.hand_calculator.estimate_hand_value(
            tiles=hand_136, win_tile=win_tile_136, melds=melds_136 if melds_136 else None,
            dora_indicators=dora_indicators_136 if dora_indicators_136 else None, config=config
        )

        if result.error:
            return (0, result.error) if require_yaku else (1000, None)
        return result.cost['main'], None

    def evaluate_ev_efficiency(self, hand: List[int], visible_tiles: List[int], current_shanten: int,
                               melds_data: List[Dict] = None, dora_indicators: List[int] = None,
                               require_yaku: bool = True, round_wind: int = 27, player_wind: int = 28) -> List[Dict]:
        """打点期望引擎 (包含二阶评分逻辑)"""
        best_discards = []
        can_riichi = not melds_data or all(m['type'] == 'kan' for m in melds_data)

        for discard_tile in range(34):
            if hand[discard_tile] == 0: continue
            hand[discard_tile] -= 1

            shanten_after_discard = self.get_shanten(hand)
            ukeire_details, total_ukeire_count, expected_value = [], 0, 0.0
            last_error = None

            for draw_tile in range(34):
                if visible_tiles[draw_tile] >= 4: continue
                hand[draw_tile] += 1
                new_shanten = self.get_shanten(hand)

                if new_shanten < shanten_after_discard:
                    real_left = 4 - visible_tiles[draw_tile]
                    if real_left > 0:
                        if new_shanten == -1:
                            score, err = self.calculate_exact_score(
                                hand, draw_tile, is_riichi=can_riichi, melds_data=melds_data,
                                dora_indicators=dora_indicators, require_yaku=require_yaku,
                                round_wind=round_wind, player_wind=player_wind
                            )
                            score_estimate = score
                            if err: last_error = err
                        else:
                            score_estimate = 1000

                        expected_value += real_left * score_estimate
                        ukeire_details.append(
                            {'tile': draw_tile, 'left_count': real_left, 'estimated_score': score_estimate})
                        total_ukeire_count += real_left
                hand[draw_tile] -= 1

            utility = self._calculate_hand_utility(hand, dora_indicators)

            best_discards.append({
                'discard_tile': discard_tile, 'shanten_after_discard': shanten_after_discard,
                'total_ukeire': total_ukeire_count, 'ev': expected_value, 'quality_score': utility,
                'err': last_error if expected_value == 0 and last_error else None,
                'details': ukeire_details
            })
            hand[discard_tile] += 1

        # 排序：进张有效性 > 向听推进 > 期望分(EV) > 进张数量 > 战略价值
        best_discards.sort(
            key=lambda x: (x['total_ukeire'] > 0, -x['shanten_after_discard'], x['ev'], x['total_ukeire'],
                           x['quality_score']),
            reverse=True)
        return best_discards