from flask import Flask, request, jsonify, render_template
from models import GameState
from engine import RuleEngine
from utils import id_to_str
from match_engine import MatchManager
from typing import Optional
import traceback
import random  # 用于模拟 AI 的随机鸣牌决策

app = Flask(__name__)
engine = RuleEngine()

# 全局变量存储当前对局
active_match: Optional[MatchManager] = None

# 强制使用文本变体 \uFE0E 防止浏览器将“中”等字符渲染成立体 Emoji
UNICODE_TILES = [
    "🀇\uFE0E", "🀈\uFE0E", "🀉\uFE0E", "🀊\uFE0E", "🀋\uFE0E", "🀌\uFE0E", "🀍\uFE0E", "🀎\uFE0E", "🀏\uFE0E",
    "🀙\uFE0E", "🀚\uFE0E", "🀛\uFE0E", "🀜\uFE0E", "🀝\uFE0E", "🀞\uFE0E", "🀟\uFE0E", "🀠\uFE0E", "🀡\uFE0E",
    "🀐\uFE0E", "🀑\uFE0E", "🀒\uFE0E", "🀓\uFE0E", "🀔\uFE0E", "🀕\uFE0E", "🀖\uFE0E", "🀗\uFE0E", "🀘\uFE0E",
    "🀀\uFE0E", "🀁\uFE0E", "🀂\uFE0E", "🀃\uFE0E", "🀆\uFE0E", "🀅\uFE0E", "🀄\uFE0E"
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/match')
def match_page():
    return render_template('match.html')


@app.route('/api/evaluate_state', methods=['POST'])
def evaluate_state():
    try:
        data = request.json
        hand_ids = data.get('hand', [])
        dead_ids = data.get('dead', [])
        melds_data = data.get('melds', [])
        dora_indicators = data.get('dora', [])
        require_yaku = data.get('require_yaku', True)
        round_wind = data.get('round_wind', 27)
        player_wind = data.get('player_wind', 28)

        game = GameState()
        my_player = game.players[0]

        for t_id in hand_ids:
            my_player.add_tile_to_hand(t_id)
            game.record_visible_tile(t_id, count=1)
        for t_id in dead_ids:
            game.record_visible_tile(t_id, count=1)
        for m in melds_data:
            game.record_visible_tile(m['tile'], count=4 if m['type'] == 'kan' else 3)
        for t_id in dora_indicators:
            game.record_visible_tile(t_id, count=1)

        current_shanten = engine.get_shanten(my_player.hand)
        recommendations = []

        if current_shanten == -1:
            pass
        elif current_shanten == 0:
            recommendations = engine.evaluate_ev_efficiency(
                hand=my_player.hand, visible_tiles=game.visible_tiles, current_shanten=current_shanten,
                melds_data=melds_data, dora_indicators=dora_indicators, require_yaku=require_yaku,
                round_wind=round_wind, player_wind=player_wind
            )
        else:
            _, recommendations = engine.evaluate_pure_efficiency(
                hand=my_player.hand, visible_tiles=game.visible_tiles, dora_indicators=dora_indicators
            )

        response_data = {"shanten": current_shanten, "recommendations": []}

        for rec in recommendations[:5]:
            details = [{"name": id_to_str(d['tile']), "char": UNICODE_TILES[d['tile']], "left": d['left_count']} for d
                       in rec['details']]
            response_data["recommendations"].append({
                "discard_id": rec['discard_tile'], "discard_name": id_to_str(rec['discard_tile']),
                "discard_char": UNICODE_TILES[rec['discard_tile']], "total_ukeire": rec['total_ukeire'],
                "ev": rec.get('ev', None), "err": rec.get('err', None),
                "is_retreat": rec.get('shanten_after_discard', 0) > current_shanten, "details": details
            })
        return jsonify(response_data)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# =====================================================================
# 沙盒模拟对战核心逻辑 (Match Logic)
# =====================================================================

def check_ron(discarder_index, discard_tile_34):
    """全场截胡检查 (优先级 1)"""
    if not active_match: return False
    for offset in range(1, 4):
        p_idx = (discarder_index + offset) % 4
        hand_34 = active_match.get_hand_34(p_idx)
        hand_34[discard_tile_34] += 1
        if engine.get_shanten(hand_34) == -1:
            active_match.is_game_over = True
            active_match.winner = p_idx
            discarded_136 = active_match.players[discarder_index]["discards_136"].pop()
            active_match.players[p_idx]["hand_136"].append(discarded_136)
            return True
        hand_34[discard_tile_34] -= 1
    return False


def handle_ai_melds(discarder_index, tile_34):
    """【核心修复】AI 拦截鸣牌检查 (优先级 2)，防止战局卡死"""
    if not active_match: return False
    for i in range(1, 4):
        if i == discarder_index: continue
        can_kan = active_match.can_call_kan(i, tile_34)
        can_pon = active_match.can_call_pon(i, tile_34)
        # 简单概率模型：AI 有 30% 概率鸣牌以推进战局
        if (can_kan or can_pon) and random.random() < 0.3:
            meld_type = 'kan' if can_kan else 'pon'
            active_match.perform_meld(i, tile_34, meld_type, discarder_index)
            return True
    return False


def get_human_actions(discarder_index, tile_34):
    """检查人类玩家 (P0) 的拦截动作"""
    if not active_match or discarder_index == 0: return []
    actions = []
    if active_match.can_call_kan(0, tile_34): actions.append({"type": "kan", "tile": tile_34})
    if active_match.can_call_pon(0, tile_34): actions.append({"type": "pon", "tile": tile_34})
    return actions


@app.route('/api/match/start', methods=['POST'])
def start_match():
    global active_match
    active_match = MatchManager()
    return jsonify(get_match_state())


@app.route('/api/match/state', methods=['GET'])
def match_state():
    if not active_match: return jsonify({"error": "No match"}), 400
    return jsonify(get_match_state())


@app.route('/api/match/player_discard', methods=['POST'])
def match_player_discard():
    global active_match
    data = request.json
    discard_tile_34 = data.get('discard_tile')
    active_match.player_discard(0, discard_tile_34)

    if check_ron(0, discard_tile_34): return jsonify(get_match_state())
    if handle_ai_melds(0, discard_tile_34): return jsonify(get_match_state())
    return jsonify(get_match_state())


@app.route('/api/match/ai_turn', methods=['POST'])
def match_ai_turn():
    global active_match
    if not active_match or active_match.current_turn == 0:
        return jsonify({"error": "Human turn"}), 400

    ai_idx = active_match.current_turn
    if active_match.is_game_over: return jsonify(get_match_state())

    # 【修复点】判定是否需要摸牌：鸣牌后手牌为 14 张，不摸牌直接出牌
    hand_count = sum(active_match.get_hand_34(ai_idx))
    if hand_count == 13:
        if not active_match.player_draw(ai_idx): return jsonify(get_match_state())

    hand_34 = active_match.get_hand_34(ai_idx)
    shanten = engine.get_shanten(hand_34)

    if shanten == -1:
        active_match.is_game_over, active_match.winner = True, ai_idx
        return jsonify(get_match_state())

    dora_34 = [t // 4 for t in active_match.dora_indicators]

    # AI 决策
    visible = active_match.dead_tiles_34
    if shanten == 0:
        # 传入格式化后的 dora_34
        recs = engine.evaluate_ev_efficiency(hand_34, visible, shanten, active_match.players[ai_idx]["melds"], dora_34)
    else:
        # 传入格式化后的 dora_34
        _, recs = engine.evaluate_pure_efficiency(hand_34, visible, dora_34)

    best_tile = recs[0]['discard_tile'] if recs else active_match.players[ai_idx]["hand_136"][-1] // 4
    active_match.player_discard(ai_idx, best_tile)

    # 拦截扫描流程
    if check_ron(ai_idx, best_tile): return jsonify(get_match_state())

    actions = get_human_actions(ai_idx, best_tile)
    if actions:
        state = get_match_state()
        state.update({"available_actions": actions, "last_discarder": ai_idx, "last_tile": best_tile})
        return jsonify(state)

    if handle_ai_melds(ai_idx, best_tile): return jsonify(get_match_state())

    if active_match.current_turn == 0 and not active_match.is_game_over:
        active_match.player_draw(0)
    return jsonify(get_match_state())


@app.route('/api/match/call_meld', methods=['POST'])
def match_call_meld():
    data = request.json
    active_match.perform_meld(0, data['tile'], data['type'], data['discarder'])
    return jsonify(get_match_state())


def get_match_state():
    if not active_match: return {}
    state = {
        "current_turn": active_match.current_turn,
        "wall_remaining": len(active_match.wall),
        "dora_indicators": [t // 4 for t in active_match.dora_indicators],
        "is_game_over": active_match.is_game_over,
        "winner": active_match.winner,
        "players": []
    }
    for i in range(4):
        h34 = active_match.get_hand_34(i)
        p_data = {
            "index": i, "discards": active_match.get_discards_34(i),
            "melds": active_match.players[i]["melds"], "hand_count": sum(h34)
        }
        if i == 0 or active_match.is_game_over:
            p_data["hand"] = [t for t in range(34) for _ in range(h34[t])]
        state["players"].append(p_data)
    return state


if __name__ == '__main__':
    # 生产环境通常由 gunicorn 启动，但保留此逻辑方便本地调试
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)