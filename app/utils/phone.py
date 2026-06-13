"""
手机号工具类
支持国际手机号格式化和国家代码识别
"""

# 常用国家代码映射 (按长度和前缀排序，便于匹配)
COUNTRY_CODES = {
    # 1位国家代码
    "1": {"name": "美国/加拿大", "length": 10},
    # 2位国家代码
    "20": {"name": "埃及", "length": 10},
    "27": {"name": "南非", "length": 9},
    "30": {"name": "希腊", "length": 10},
    "31": {"name": "荷兰", "length": 9},
    "32": {"name": "比利时", "length": 9},
    "33": {"name": "法国", "length": 9},
    "34": {"name": "西班牙", "length": 9},
    "36": {"name": "匈牙利", "length": 9},
    "39": {"name": "意大利", "length": 10},
    "40": {"name": "罗马尼亚", "length": 10},
    "41": {"name": "瑞士", "length": 9},
    "43": {"name": "奥地利", "length": 10},
    "44": {"name": "英国", "length": 10},
    "45": {"name": "丹麦", "length": 8},
    "46": {"name": "瑞典", "length": 9},
    "47": {"name": "挪威", "length": 8},
    "48": {"name": "波兰", "length": 9},
    "49": {"name": "德国", "length": 10},
    "51": {"name": "秘鲁", "length": 9},
    "52": {"name": "墨西哥", "length": 10},
    "54": {"name": "阿根廷", "length": 10},
    "55": {"name": "巴西", "length": 11},
    "56": {"name": "智利", "length": 9},
    "57": {"name": "哥伦比亚", "length": 10},
    "58": {"name": "委内瑞拉", "length": 10},
    "60": {"name": "马来西亚", "length": 9},
    "61": {"name": "澳大利亚", "length": 9},
    "62": {"name": "印尼", "length": 11},
    "63": {"name": "菲律宾", "length": 10},
    "64": {"name": "新西兰", "length": 9},
    "65": {"name": "新加坡", "length": 8},
    "66": {"name": "泰国", "length": 9},
    "81": {"name": "日本", "length": 10},
    "82": {"name": "韩国", "length": 10},
    "84": {"name": "越南", "length": 10},
    "86": {"name": "中国", "length": 11},
    "90": {"name": "土耳其", "length": 10},
    "91": {"name": "印度", "length": 10},
    "92": {"name": "巴基斯坦", "length": 10},
    "93": {"name": "阿富汗", "length": 9},
    "94": {"name": "斯里兰卡", "length": 9},
    "95": {"name": "缅甸", "length": 9},
    "98": {"name": "伊朗", "length": 10},
    # 3位国家代码
    "120": {"name": "加拿大", "length": 10},
    "124": {"name": "加拿大", "length": 10},
    "125": {"name": "加拿大", "length": 10},
    "126": {"name": "加拿大", "length": 10},
    "127": {"name": "加拿大", "length": 10},
    "128": {"name": "加拿大", "length": 10},
    "134": {"name": "美国", "length": 10},
    "144": {"name": "牙买加", "length": 10},
    "147": {"name": "开曼群岛", "length": 10},
    "156": {"name": "特立尼达和多巴哥", "length": 10},
    "164": {"name": "波多黎各", "length": 10},
    "165": {"name": "波多黎各", "length": 10},
    "166": {"name": "波多黎各", "length": 10},
    "167": {"name": "波多黎各", "length": 10},
    "168": {"name": "波多黎各", "length": 10},
    "175": {"name": "百慕大", "length": 10},
    "176": {"name": "百慕大", "length": 10},
    "178": {"name": "阿根廷", "length": 10},
    "180": {"name": "墨西哥", "length": 10},
    "181": {"name": "墨西哥", "length": 10},
    "182": {"name": "墨西哥", "length": 10},
    "183": {"name": "墨西哥", "length": 10},
    "184": {"name": "墨西哥", "length": 10},
    "186": {"name": "秘鲁", "length": 9},
    "187": {"name": "阿根廷", "length": 10},
    "188": {"name": "哥斯达黎加", "length": 8},
    "190": {"name": "菲律宾", "length": 10},
    "212": {"name": "摩洛哥", "length": 9},
    "213": {"name": "阿尔及利亚", "length": 9},
    "216": {"name": "突尼斯", "length": 8},
    "218": {"name": "利比亚", "length": 9},
    "220": {"name": "冈比亚", "length": 9},
    "221": {"name": "塞内加尔", "length": 9},
    "222": {"name": "毛里塔尼亚", "length": 9},
    "223": {"name": "马里", "length": 8},
    "224": {"name": "几内亚", "length": 9},
    "225": {"name": "科特迪瓦", "length": 10},
    "226": {"name": "布基纳法索", "length": 8},
    "227": {"name": "尼日尔", "length": 8},
    "228": {"name": "多哥", "length": 8},
    "229": {"name": "贝宁", "length": 8},
    "230": {"name": "毛里求斯", "length": 8},
    "231": {"name": "利比里亚", "length": 8},
    "232": {"name": "塞拉利昂", "length": 8},
    "233": {"name": "加纳", "length": 9},
    "234": {"name": "尼日利亚", "length": 10},
    "235": {"name": "乍得", "length": 9},
    "236": {"name": "中非", "length": 8},
    "237": {"name": "喀麦隆", "length": 9},
    "238": {"name": "佛得角", "length": 9},
    "239": {"name": "圣多美和普林西比", "length": 9},
    "240": {"name": "赤道几内亚", "length": 9},
    "241": {"name": "加蓬", "length": 9},
    "242": {"name": "刚果(布)", "length": 9},
    "243": {"name": "刚果(金)", "length": 9},
    "244": {"name": "安哥拉", "length": 9},
    "245": {"name": "几内亚比绍", "length": 9},
    "246": {"name": "英属印度洋领地", "length": 7},
    "247": {"name": "阿森松岛", "length": 7},
    "248": {"name": "塞舌尔", "length": 7},
    "249": {"name": "苏丹", "length": 9},
    "250": {"name": "卢旺达", "length": 9},
    "251": {"name": "埃塞俄比亚", "length": 9},
    "252": {"name": "索马里", "length": 9},
    "253": {"name": "吉布提", "length": 8},
    "254": {"name": "肯尼亚", "length": 9},
    "255": {"name": "坦桑尼亚", "length": 9},
    "256": {"name": "乌干达", "length": 9},
    "257": {"name": "布隆迪", "length": 8},
    "258": {"name": "莫桑比克", "length": 9},
    "260": {"name": "赞比亚", "length": 9},
    "261": {"name": "马达加斯加", "length": 10},
    "262": {"name": "留尼汪/马约特", "length": 9},
    "263": {"name": "津巴布韦", "length": 9},
    "264": {"name": "纳米比亚", "length": 9},
    "265": {"name": "马拉维", "length": 9},
    "266": {"name": "莱索托", "length": 8},
    "267": {"name": "博茨瓦纳", "length": 8},
    "268": {"name": "斯威士兰", "length": 8},
    "269": {"name": "科摩罗", "length": 7},
    "291": {"name": "厄立特里亚", "length": 7},
    "297": {"name": "阿鲁巴", "length": 7},
    "298": {"name": "法罗群岛", "length": 6},
    "299": {"name": "格陵兰", "length": 6},
    "350": {"name": "直布罗陀", "length": 8},
    "351": {"name": "葡萄牙", "length": 9},
    "352": {"name": "卢森堡", "length": 9},
    "353": {"name": "爱尔兰", "length": 9},
    "354": {"name": "冰岛", "length": 9},
    "355": {"name": "阿尔巴尼亚", "length": 9},
    "356": {"name": "马耳他", "length": 8},
    "357": {"name": "塞浦路斯", "length": 8},
    "358": {"name": "芬兰", "length": 10},
    "359": {"name": "保加利亚", "length": 9},
    "370": {"name": "立陶宛", "length": 8},
    "371": {"name": "拉脱维亚", "length": 8},
    "372": {"name": "爱沙尼亚", "length": 9},
    "373": {"name": "摩尔多瓦", "length": 8},
    "374": {"name": "亚美尼亚", "length": 8},
    "375": {"name": "白俄罗斯", "length": 9},
    "376": {"name": "安道尔", "length": 6},
    "377": {"name": "摩纳哥", "length": 8},
    "378": {"name": "圣马力诺", "length": 10},
    "380": {"name": "乌克兰", "length": 9},
    "381": {"name": "塞尔维亚", "length": 9},
    "382": {"name": "黑山", "length": 8},
    "385": {"name": "克罗地亚", "length": 9},
    "386": {"name": "斯洛文尼亚", "length": 9},
    "387": {"name": "波黑", "length": 8},
    "389": {"name": "北马其顿", "length": 8},
    "420": {"name": "捷克", "length": 9},
    "421": {"name": "斯洛伐克", "length": 9},
    "423": {"name": "列支敦士登", "length": 7},
    "501": {"name": "伯利兹", "length": 7},
    "502": {"name": "危地马拉", "length": 8},
    "503": {"name": "萨尔瓦多", "length": 8},
    "504": {"name": "洪都拉斯", "length": 8},
    "505": {"name": "尼加拉瓜", "length": 8},
    "506": {"name": "哥斯达黎加", "length": 8},
    "507": {"name": "巴拿马", "length": 8},
    "508": {"name": "圣皮埃尔和密克隆", "length": 6},
    "509": {"name": "海地", "length": 8},
    "591": {"name": "玻利维亚", "length": 8},
    "592": {"name": "圭亚那", "length": 7},
    "593": {"name": "厄瓜多尔", "length": 9},
    "595": {"name": "巴拉圭", "length": 9},
    "597": {"name": "苏里南", "length": 7},
    "598": {"name": "乌拉圭", "length": 8},
    "599": {"name": "荷属安的列斯", "length": 8},
    "670": {"name": "东帝汶", "length": 7},
    "672": {"name": "南极洲", "length": 7},
    "673": {"name": "文莱", "length": 7},
    "675": {"name": "巴布亚新几内亚", "length": 8},
    "676": {"name": "汤加", "length": 7},
    "677": {"name": "所罗门群岛", "length": 7},
    "678": {"name": "瓦努阿图", "length": 7},
    "679": {"name": "斐济", "length": 7},
    "680": {"name": "帕劳", "length": 7},
    "681": {"name": "瓦利斯和富图纳", "length": 6},
    "682": {"name": "库克群岛", "length": 5},
    "683": {"name": "纽埃", "length": 4},
    "685": {"name": "圣文森特和格林纳丁斯", "length": 7},
    "686": {"name": "基里巴斯", "length": 8},
    "687": {"name": "新喀里多尼亚", "length": 6},
    "688": {"name": "图瓦卢", "length": 6},
    "689": {"name": "法属波利尼西亚", "length": 8},
    "690": {"name": "托克劳", "length": 4},
    "691": {"name": "密克罗尼西亚", "length": 7},
    "692": {"name": "马绍尔群岛", "length": 7},
    "850": {"name": "朝鲜", "length": 10},
    "852": {"name": "香港", "length": 8},
    "853": {"name": "澳门", "length": 8},
    "855": {"name": "柬埔寨", "length": 9},
    "856": {"name": "老挝", "length": 9},
    "880": {"name": "孟加拉国", "length": 10},
    "886": {"name": "台湾", "length": 9},
    "960": {"name": "马尔代夫", "length": 7},
    "961": {"name": "黎巴嫩", "length": 8},
    "962": {"name": "约旦", "length": 9},
    "963": {"name": "叙利亚", "length": 9},
    "964": {"name": "伊拉克", "length": 10},
    "965": {"name": "科威特", "length": 8},
    "966": {"name": "沙特阿拉伯", "length": 9},
    "967": {"name": "也门", "length": 9},
    "968": {"name": "阿曼", "length": 8},
    "970": {"name": "巴勒斯坦", "length": 9},
    "971": {"name": "阿联酋", "length": 9},
    "972": {"name": "以色列", "length": 9},
    "973": {"name": "巴林", "length": 8},
    "974": {"name": "卡塔尔", "length": 8},
    "975": {"name": "不丹", "length": 8},
    "976": {"name": "蒙古", "length": 8},
    "977": {"name": "尼泊尔", "length": 10},
    "992": {"name": "塔吉克斯坦", "length": 9},
    "993": {"name": "土库曼斯坦", "length": 8},
    "994": {"name": "阿塞拜疆", "length": 9},
    "995": {"name": "格鲁吉亚", "length": 9},
    "996": {"name": "吉尔吉斯斯坦", "length": 9},
    "998": {"name": "乌兹别克斯坦", "length": 9},
}


def detect_country_code(phone: str) -> tuple[str | None, str | None, str]:
    """
    检测手机号的国家代码

    Args:
        phone: 手机号，格式如 "+8613800138000" 或 "8613800138000" 或 "13800138000"

    Returns:
        (country_code, country_name, local_phone)
        - country_code: 国家代码，如 "86"
        - country_name: 国家名称，如 "中国"
        - local_phone: 本地手机号（去掉国家代码后的部分）
    """
    # 移除首部的 + 号
    clean_phone = phone.lstrip("+")

    # 尝试匹配不同长度的国家代码（从长到短，避免前缀混淆）
    for length in [4, 3, 2, 1]:
        if len(clean_phone) > length:
            code = clean_phone[:length]
            if code in COUNTRY_CODES:
                country_info = COUNTRY_CODES[code]
                local_phone = clean_phone[length:]

                # 验证本地号码长度是否合理
                expected_len = country_info["length"]
                if len(local_phone) >= expected_len - 2 and len(local_phone) <= expected_len + 2:
                    return code, country_info["name"], local_phone

    # 未匹配到已知国家代码，默认中国
    # 如果号码以1开头且长度为11，假设为中国
    if clean_phone.startswith("1") and len(clean_phone) == 11:
        return "86", "中国", clean_phone

    # 无法识别，返回原始号码
    return None, "未知", clean_phone


def format_phone(phone: str, include_country: bool = True) -> str:
    """
    格式化手机号显示

    Args:
        phone: 原始手机号
        include_country: 是否包含国家名称

    Returns:
        格式化后的手机号，如 "中国 +86 138 0013 8000"
    """
    country_code, country_name, local_phone = detect_country_code(phone)

    if include_country and country_name:
        return f"{country_name} +{country_code} {local_phone}"
    elif country_code:
        return f"+{country_code} {local_phone}"
    else:
        return phone
