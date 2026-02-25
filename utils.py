from typing import List


def parse_tiles(hand_str: str) -> List[int]:
    """
    将天凤格式的字符串解析为牌的 ID 列表。
    支持的格式例如: '123m456p789s1122z'
    m: 万(0-8), p: 筒(9-17), s: 索(18-26), z: 字牌(27-33, 1-7分别对应东南西北白发中)

    返回:
        List[int]: 包含牌 ID 的列表，例如 [0, 1, 2, ...]
    """
    result = []
    current_numbers = []
    offsets = {'m': 0, 'p': 9, 's': 18, 'z': 27}

    for char in hand_str:
        if char.isdigit():
            current_numbers.append(int(char))
        elif char in offsets:
            offset = offsets[char]
            for num in current_numbers:
                # 牌面数字 1-9，对应的内部索引是 0-8，所以要减 1
                result.append(num - 1 + offset)
            current_numbers = []

    return result


def id_to_str(tile_id: int) -> str:
    """
    将单个内部牌 ID (0-33) 转换为人类可读的中文全称。
    例如: 0 -> '1万', 27 -> '东'
    """
    if tile_id < 0 or tile_id > 33:
        return "未知牌"

    if tile_id < 9:
        return f"{tile_id + 1}万"
    if tile_id < 18:
        return f"{tile_id - 9 + 1}筒"
    if tile_id < 27:
        return f"{tile_id - 18 + 1}索"

    zi_names = ["东", "南", "西", "北", "白", "发", "中"]
    return zi_names[tile_id - 27]


def print_hand(hand_array: List[int]) -> None:
    """
    在控制台打印当前手牌。
    输入为长度 34 的数组 (索引为牌 ID，值为该牌数量)。
    """
    tiles = []
    for tile_id, count in enumerate(hand_array):
        for _ in range(count):
            tiles.append(id_to_str(tile_id))
    print(f"[{', '.join(tiles)}]")


def hand_array_to_tenhou_str(hand_array: List[int]) -> str:
    """
    (进阶工具) 将长度为 34 的手牌数组转换回天凤格式的字符串。
    在记录牌谱日志，或者将手牌状态发送给其他 API (如算点数) 时非常有用。
    例如: 将数组转换为 '123m456p789s1122z'
    """
    res = ""

    # 提取万子 (0-8)
    m_str = "".join([str(i + 1) * hand_array[i] for i in range(0, 9)])
    if m_str: res += m_str + "m"

    # 提取筒子 (9-17)
    p_str = "".join([str(i - 9 + 1) * hand_array[i] for i in range(9, 18)])
    if p_str: res += p_str + "p"

    # 提取索子 (18-26)
    s_str = "".join([str(i - 18 + 1) * hand_array[i] for i in range(18, 27)])
    if s_str: res += s_str + "s"

    # 提取字牌 (27-33)
    z_str = "".join([str(i - 27 + 1) * hand_array[i] for i in range(27, 34)])
    if z_str: res += z_str + "z"

    return res


# --- 简单的单元测试 ---
if __name__ == "__main__":
    # 1. 测试字符串转 ID
    test_str = "19m19p19s1234567z"  # 国士无双起手
    ids = parse_tiles(test_str)
    print(f"天凤字符串 '{test_str}' 解析出的 ID 列表:")
    print(ids)

    # 2. 测试 ID 转可读字符串
    print("\nID 对应的中文牌名:")
    readable_tiles = [id_to_str(tid) for tid in ids]
    print(readable_tiles)

    # 3. 构造一个 34 长度的数组并测试反向转换
    test_array = [0] * 34
    for tid in ids:
        test_array[tid] += 1

    print("\n从数组反向生成的字符串:")
    print(hand_array_to_tenhou_str(test_array))