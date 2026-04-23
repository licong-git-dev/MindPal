# MindPal PRD - 08 经济系统设计

> 本文档详细定义游戏货币、商店系统、道具设计、付费策略

---

## 1. 货币体系

### 1.1 双货币系统

```yaml
currency_system:
  primary_currency:
    name: "金币"
    icon: "🪙"
    color: "#FFD700"
    obtain_methods:
      - "每日签到"
      - "完成任务"
      - "成就奖励"
      - "帮助他人"
    usage:
      - "基础商品"
      - "普通装饰"
      - "消耗品"

  premium_currency:
    name: "钻石"
    icon: "💎"
    color: "#00BFFF"
    obtain_methods:
      - "充值购买（主要）"
      - "特殊成就"
      - "活动奖励"
    usage:
      - "高级商品"
      - "稀有装饰"
      - "加速道具"
      - "金币兑换"
```

### 1.2 金币获取详情

```yaml
gold_income:
  daily:
    login_reward:
      day_1: 50
      day_2: 60
      day_3: 70
      day_4: 80
      day_5: 90
      day_6: 100
      day_7: 200  # 第7天翻倍
      note: "连续签到，断签重置"

  quests:
    daily_quest:
      count: 3
      gold_per_quest: 30-50
      daily_total_max: 150

    weekly_quest:
      count: 1
      gold_per_quest: 200

    main_quest:
      range: "100-500/任务"

    side_quest:
      range: "50-200/任务"

  social:
    help_player: 30  # 每日上限3次
    add_friend: 20  # 每日上限5次

  npc_interaction:
    dialogue_with_bei:
      gold_per_5min: 10
      daily_max: 100

  estimated_daily_income:
    casual_player: "150-300金币"
    active_player: "400-600金币"
```

### 1.3 钻石获取详情

```yaml
diamond_income:
  purchase:
    packages:
      - name: "小额充值"
        price_rmb: 6
        diamonds: 60
        bonus: 0

      - name: "中额充值"
        price_rmb: 30
        diamonds: 330
        bonus: 30

      - name: "大额充值"
        price_rmb: 98
        diamonds: 1180
        bonus: 180

      - name: "豪华充值"
        price_rmb: 198
        diamonds: 2580
        bonus: 580

      - name: "至尊充值"
        price_rmb: 648
        diamonds: 8880
        bonus: 2280

  free_sources:
    achievements:
      note: "特定成就奖励少量钻石"
      example: "完成主线：50钻石"

    events:
      note: "节日活动可能赠送钻石"

    first_clear:
      note: "首次通关某些挑战"

  diamond_to_gold:
    rate: "1钻石 = 10金币"
    note: "单向兑换，不可逆"
```

---

## 2. 商店系统

### 2.1 商店分类

```yaml
shop_categories:
  outfits:
    name: "服装"
    subcategories:
      - tops: "上衣"
      - bottoms: "下装"
      - shoes: "鞋子"
      - sets: "套装"

  accessories:
    name: "配饰"
    subcategories:
      - hats: "帽子"
      - glasses: "眼镜"
      - jewelry: "饰品"
      - bags: "背包"

  effects:
    name: "特效"
    subcategories:
      - auras: "光环"
      - trails: "拖尾"
      - footprints: "脚印"

  consumables:
    name: "消耗品"
    items:
      - "传送卷轴"
      - "经验加成"
      - "宠物零食"

  pet_items:
    name: "宠物"
    subcategories:
      - skins: "宠物皮肤"
      - accessories: "宠物配饰"

  limited:
    name: "限定"
    note: "节日/活动限定商品"
    rotation: "每周更新"
```

### 2.2 商品定价策略

```yaml
pricing_strategy:
  rarity_tiers:
    common:
      name: "普通"
      color: "#FFFFFF"
      gold_range: "50-200"
      diamond_range: "N/A"

    uncommon:
      name: "精良"
      color: "#00FF00"
      gold_range: "200-500"
      diamond_range: "20-50"

    rare:
      name: "稀有"
      color: "#0080FF"
      gold_range: "500-1000"
      diamond_range: "50-100"

    epic:
      name: "史诗"
      color: "#9932CC"
      gold_range: "N/A（仅钻石）"
      diamond_range: "100-300"

    legendary:
      name: "传说"
      color: "#FF8C00"
      gold_range: "N/A"
      diamond_range: "300-500"

  example_items:
    - name: "基础T恤"
      rarity: "common"
      price_gold: 100
      price_diamond: null

    - name: "星空连衣裙"
      rarity: "rare"
      price_gold: 800
      price_diamond: 80

    - name: "凤凰之翼"
      rarity: "legendary"
      price_gold: null
      price_diamond: 500
```

### 2.3 商店UI设计

```yaml
shop_ui:
  access:
    - "主菜单 > 商店"
    - "与老莫对话"
    - "快捷键Y"

  layout:
    left_sidebar:
      width: "20%"
      content: "商品分类导航"

    main_area:
      width: "60%"
      content: "商品网格（4列）"

    right_panel:
      width: "20%"
      content:
        - "选中商品预览"
        - "商品详情"
        - "购买按钮"
        - "玩家货币显示"

  item_card:
    elements:
      - "商品图标"
      - "名称"
      - "稀有度边框颜色"
      - "价格（金币/钻石）"
      - "已拥有标记"
      - "限定标记"

  purchase_flow:
    1: "点击商品"
    2: "显示预览（可试穿）"
    3: "确认购买"
    4: "扣除货币"
    5: "获得物品"
    6: "播放获得动画"

  filters:
    - "按类型"
    - "按稀有度"
    - "按价格"
    - "仅显示金币可购"
    - "仅显示未拥有"

  sort:
    - "默认"
    - "价格升序"
    - "价格降序"
    - "最新上架"
    - "人气"
```

---

## 3. 道具系统

### 3.1 消耗品详情

```yaml
consumable_items:
  teleport_scroll:
    name: "传送卷轴"
    description: "立即传送到指定传送点"
    rarity: "uncommon"
    price_gold: 100
    price_diamond: 10
    stackable: true
    max_stack: 99
    usage: "打开地图选择目的地"

  exp_boost:
    name: "经验药水"
    description: "30分钟内经验获取+50%"
    rarity: "rare"
    price_gold: 300
    price_diamond: 30
    stackable: true
    max_stack: 10
    duration: "30分钟"
    cooldown: "使用后2小时冷却"

  pet_snack_basic:
    name: "宠物零食（普通）"
    description: "喂给芝麻，增加10点好感度"
    rarity: "common"
    price_gold: 50
    stackable: true
    max_stack: 99

  pet_snack_premium:
    name: "宠物零食（高级）"
    description: "喂给芝麻，增加50点好感度"
    rarity: "uncommon"
    price_gold: 200
    price_diamond: 20
    stackable: true
    max_stack: 20

  memory_crystal:
    name: "记忆水晶"
    description: "保存一段与小北的对话，可随时回顾"
    rarity: "rare"
    price_gold: 500
    price_diamond: 50
    stackable: true
    max_stack: 10
    usage: "在对话中使用，保存最近10轮对话"

  revival_feather:
    name: "复苏羽毛"
    description: "在小游戏中失败时可使用，从当前进度继续"
    rarity: "epic"
    price_diamond: 100
    stackable: true
    max_stack: 5
```

### 3.2 装饰品详情

```yaml
decoration_items:
  outfits:
    example_items:
      - id: "outfit_casual_001"
        name: "休闲套装-白"
        set: ["top_tshirt_white", "bottom_jeans_blue", "shoes_sneakers_white"]
        rarity: "common"
        price_gold: 200

      - id: "outfit_fantasy_001"
        name: "精灵套装"
        set: ["top_elf_tunic", "bottom_elf_pants", "shoes_elf_boots"]
        rarity: "rare"
        price_gold: 800
        price_diamond: 80

      - id: "outfit_scifi_001"
        name: "宇航服"
        set: ["top_spacesuit", "bottom_spacesuit", "shoes_space_boots"]
        rarity: "epic"
        price_diamond: 200

  effects:
    example_items:
      - id: "aura_sparkle"
        name: "星光环绕"
        description: "身体周围漂浮发光星星"
        rarity: "rare"
        price_gold: 600
        price_diamond: 60

      - id: "trail_rainbow"
        name: "彩虹拖尾"
        description: "移动时留下彩虹轨迹"
        rarity: "epic"
        price_diamond: 150

      - id: "footprint_flowers"
        name: "花朵脚印"
        description: "走过的地方长出小花"
        rarity: "uncommon"
        price_gold: 300

  pet_cosmetics:
    example_items:
      - id: "pet_skin_golden"
        name: "金色皮肤"
        description: "让芝麻变成金色"
        rarity: "rare"
        price_diamond: 100

      - id: "pet_hat_wizard"
        name: "魔法师帽"
        description: "芝麻戴上小巫师帽"
        rarity: "uncommon"
        price_gold: 200
```

### 3.3 功能性道具

```yaml
functional_items:
  inventory_expansion:
    name: "背包扩展"
    description: "永久增加10格背包空间"
    rarity: "epic"
    price_diamond: 300
    max_purchase: 5
    effect: "背包容量+10"

  friend_list_expansion:
    name: "好友位扩展"
    description: "永久增加50个好友位"
    rarity: "rare"
    price_diamond: 200
    max_purchase: 3
    effect: "好友上限+50"

  name_change_card:
    name: "改名卡"
    description: "修改你的游戏昵称"
    rarity: "rare"
    price_diamond: 150
    usage: "使用后可输入新昵称"
    cooldown: "30天一次"
```

---

## 4. 会员订阅系统

### 4.1 会员等级

```yaml
membership_tiers:
  free:
    name: "普通玩家"
    price: 0
    benefits:
      - "基础游戏体验"
      - "每日任务"
      - "50好友位"
      - "100背包格"

  vip_monthly:
    name: "心灵会员"
    price_rmb: 25
    duration: "月卡"
    benefits:
      - "所有普通玩家权益"
      - "每日登录金币翻倍"
      - "每月赠送300钻石"
      - "专属会员皮肤（每月更新）"
      - "好友位+50"
      - "优先匹配"
      - "会员专属表情"
      - "会员标识"

  vip_yearly:
    name: "年度心灵会员"
    price_rmb: 228  # 相当于月卡76折
    duration: "年卡"
    benefits:
      - "所有月卡权益"
      - "每月赠送500钻石"
      - "年度专属传说皮肤"
      - "专属称号"
```

### 4.2 会员UI

```yaml
membership_ui:
  access: "主菜单 > 会员中心"

  display:
    current_status:
      - "当前会员等级"
      - "到期时间"
      - "累计会员天数"

    benefits_comparison:
      - "普通vs会员对比表"

    purchase_options:
      - "月卡"
      - "年卡"
      - "支付方式选择"

  member_badge:
    position: "昵称旁"
    design: "小皇冠图标"
    color: "#FFD700"
```

---

## 5. 经济平衡

### 5.1 经济模型

```yaml
economy_balance:
  gold_sink:
    description: "金币消耗渠道，防止通货膨胀"
    channels:
      - "商店购买"
      - "传送卷轴消耗"
      - "道具使用"
      - "后期：交易手续费"

  gold_faucet:
    description: "金币产出渠道"
    daily_average:
      casual: 300
      active: 500
      hardcore: 800

  pricing_philosophy:
    basic_items: "1-3天可获得"
    rare_items: "1-2周可获得"
    epic_items: "1个月或付费"
    legendary_items: "付费为主"

  free_to_play_friendly:
    core_experience: "完全免费"
    paid_content: "仅装饰，不影响游戏"
    progression: "付费只加速，不跳过"
```

### 5.2 防止滥用

```yaml
anti_abuse:
  gold_cap:
    daily_earn_cap: 1000  # 每日金币获取上限
    total_cap: 99999  # 金币持有上限

  gift_restriction:
    note: "v1.0不支持玩家间赠送"
    reason: "防止RMT和洗钱"

  refund_policy:
    consumables: "不可退款"
    decorations: "购买后7天内可退（未使用）"
    membership: "按剩余时间比例退款"

  fraud_detection:
    - "异常大额交易监控"
    - "快速获取监控"
    - "重复购买监控"
```

---

## 6. 促销与活动

### 6.1 常规促销

```yaml
regular_promotions:
  first_purchase_bonus:
    description: "首次充值双倍钻石"
    condition: "第一次充值任意金额"
    bonus: "获得双倍钻石"

  weekly_deals:
    description: "每周特惠商品"
    rotation: "每周一更新"
    discount: "限定商品7折"

  monthly_login_reward:
    description: "月度登录奖励"
    day_15: "稀有道具"
    day_28: "史诗道具/皮肤"
```

### 6.2 节日活动

```yaml
holiday_events:
  spring_festival:
    name: "春节活动"
    duration: "2周"
    content:
      - "限定春节皮肤"
      - "红包金币雨"
      - "拜年任务"
      - "组队奖励翻倍"

  halloween:
    name: "万圣节活动"
    duration: "1周"
    content:
      - "南瓜装扮"
      - "幽灵宠物皮肤"
      - "捣蛋任务"

  anniversary:
    name: "周年庆"
    duration: "2周"
    content:
      - "周年限定皮肤"
      - "全场折扣"
      - "回馈老玩家"
      - "特殊成就"
```

---

**下一篇 → `09_AI_Integration.md`（AI集成详细设计）**
