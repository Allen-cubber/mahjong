import os
import traceback
from models import GameState
from engine import RuleEngine
from utils import parse_tiles, id_to_str


def clear_screen():
    """清空控制台屏幕，保持界面整洁"""
    os.system('cls' if os.name == 'nt' else 'clear')


def interactive_loop():
    engine = RuleEngine()

    clear_screen()
    print("=" * 50)
    print("麻将决策辅助终端 v1.0")
    print("=" * 50)
    print("输入格式说明：")
    print(" - 万子: 1-9m  (如: 123m)")
    print(" - 筒子: 1-9p  (如: 456p)")
    print(" - 索子: 1-9s  (如: 789s)")
    print(" - 字牌: 1-7z  (1-4对应东南西北，5-7对应白发中)")
    print(" - 退出程序请输入: q")
    print("-" * 50)

    while True:
        try:
            # 1. 接收手牌输入
            hand_input = input("\n👉 请输入你的手牌 (例如 123m456p789s1122z): ").strip().lower()
            if hand_input == 'q':
                print("感谢使用，祝你把把役满！")
                break
            if not hand_input:
                continue

            # 2. 接收死牌输入 (可选)
            dead_input = input("👀 请输入场上可见的死牌 (包含别人打的、副露的、宝牌指示牌，无则回车): ").strip().lower()
            if dead_input == 'q':
                break

            # 3. 初始化状态 (每次查询都重置状态，避免输入错误导致历史污染)
            game = GameState()
            my_player = game.players[0]

            # 解析手牌
            hand_ids = parse_tiles(hand_input)
            if len(hand_ids) not in [2, 5, 8, 11, 14]:
                print(f"⚠️ 警告: 你输入了 {len(hand_ids)} 张牌。通常决策时手牌应为 14, 11, 8, 5, 2 张。")

            for t_id in hand_ids:
                my_player.add_tile_to_hand(t_id)
                game.record_visible_tile(t_id, count=1)  # 手牌计入全局可见牌

            # 解析死牌
            if dead_input:
                dead_ids = parse_tiles(dead_input)
                for t_id in dead_ids:
                    game.record_visible_tile(t_id, count=1)

            # 4. 调用引擎计算
            print("\n" + "-" * 20 + " 思考中... " + "-" * 20)
            current_shanten, recommendations = engine.evaluate_pure_efficiency(
                hand=my_player.hand,
                visible_tiles=game.visible_tiles
            )

            # 5. 格式化输出结果
            print(f"\n✅ 当前向听数: 【 {current_shanten} 向听 】 (0代表已听牌)")
            if current_shanten == -1:
                print("🎉 恭喜！你已经和牌了！")
                continue

            if not recommendations:
                print("⚠️ 没有找到可以改善向听数的打法，可能是死听或输入有误。")
                continue

            print("💡 推荐打法排行榜:")
            # 只展示前 5 个最优选择
            for idx, rec in enumerate(recommendations[:5]):
                discard_name = id_to_str(rec['discard_tile'])
                total_ukeire = rec['total_ukeire']

                # 格式化进张详情
                detail_strs = []
                for d in rec['details']:
                    t_name = id_to_str(d['tile'])
                    detail_strs.append(f"{t_name}(剩{d['left_count']}张)")

                # 美化输出排版
                rank_icon = "🥇" if idx == 0 else "🥈" if idx == 1 else "🥉" if idx == 2 else "🔹"
                print(f"{rank_icon} 选项 {idx + 1}: 打出 【 {discard_name} 】")
                print(f"    进张面: 共 {total_ukeire} 张")
                print(f"    有效牌: {', '.join(detail_strs)}\n")

        except Exception as e:
            print(f"\n❌ 解析出错，请检查输入格式是否正确！")
            print(f"错误信息: {e}")
            # traceback.print_exc() # 如果需要详细报错信息可以取消注释这行


if __name__ == "__main__":
    interactive_loop()