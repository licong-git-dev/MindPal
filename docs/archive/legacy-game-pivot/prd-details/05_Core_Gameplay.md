# MindPal PRD - 05 核心玩法设计

> 本文档详细定义游戏核心循环、三把钥匙挑战、任务系统

---

## 1. 核心游戏循环

### 1.1 主循环设计

```
┌─────────────────────────────────────────────────────────────┐
│                     MindPal 核心循环                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│    ┌─────────┐                                              │
│    │  登录   │                                              │
│    └────┬────┘                                              │
│         │                                                   │
│         ▼                                                   │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐            │
│    │  探索   │────▶│  对话   │────▶│  反思   │            │
│    │  世界   │     │  互动   │     │  成长   │            │
│    └────┬────┘     └────┬────┘     └────┬────┘            │
│         │              │              │                    │
│         └──────────────┴──────────────┘                    │
│                        │                                    │
│                        ▼                                    │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐            │
│    │  完成   │────▶│  获得   │────▶│  解锁   │            │
│    │  任务   │     │  奖励   │     │  新内容 │            │
│    └─────────┘     └─────────┘     └─────────┘            │
│                                                             │
│                   ┌─────────────┐                          │
│                   │  集齐钥匙   │                          │
│                   │  进入圣殿   │                          │
│                   └─────────────┘                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 游戏节奏设计

| 阶段 | 时间 | 主要内容 | 情绪曲线 |
|------|------|---------|---------|
| **新手期** | 0-1小时 | 教程、认识NPC、熟悉操作 | 好奇 → 熟悉 |
| **探索期** | 1-5小时 | 探索三区域、支线任务、与小北深度对话 | 探索 → 沉浸 |
| **挑战期** | 5-15小时 | 三把钥匙挑战、主线推进 | 期待 → 感动 |
| **高潮期** | 15-20小时 | 心灵圣殿、最终对话 | 紧张 → 释然 |
| **延续期** | 20小时+ | 多人社交、收集、日常陪伴 | 平静 → 归属 |

### 1.3 日常循环（每日游玩）

```yaml
daily_loop:
  login:
    - 显示每日签到奖励
    - 小北打招呼，询问今天状态
    - 芝麻撒娇

  daily_activities:
    - 每日任务（3个简单任务）
    - 与小北对话（无限制）
    - 探索/社交

  rewards:
    - 每日签到：50金币
    - 完成每日任务：100金币
    - 与小北对话超过10分钟：20金币
    - 帮助其他玩家：30金币

  logout:
    - 小北告别语
    - 显示今日游玩摘要
    - 预告明日内容
```

---

## 2. 主线任务：三把钥匙

### 2.1 主线概述

```yaml
main_quest:
  name: "心灵之路"
  description: "集齐三把钥匙，打开心灵圣殿的大门"

  structure:
    prologue: "觉醒"
    chapter_1: "勇气之路"（现代区）
    chapter_2: "释然之路"（奇幻区）
    chapter_3: "希望之路"（科幻区）
    epilogue: "回归"（心灵圣殿）

  unlock_condition:
    chapter_1: "完成新手教程"
    chapter_2: "完成Chapter 1 或 游玩2小时"
    chapter_3: "完成Chapter 2 或 游玩4小时"
    epilogue: "集齐三把钥匙"

  order: "非线性，玩家可以选择顺序"
```

### 2.2 第一把钥匙：勇气之钥

#### 2.2.1 任务线

```yaml
chapter_1_quest_line:
  name: "勇气之路"
  location: "现代区 - 镜像之城"
  theme: "面对现实，直面恐惧"
  key: "勇气之钥"

  quests:
    - quest_1_1:
        name: "踏入镜城"
        type: "探索"
        description: "前往镜像之城，感受都市的霓虹与喧嚣"
        objectives:
          - "通过传送门进入现代区"
          - "探索主街道"
          - "找到疗愈酒吧"
        reward: "50金币"

    - quest_1_2:
        name: "酒吧的对话"
        type: "对话"
        description: "在疗愈酒吧与小北聊聊现实中的困扰"
        objectives:
          - "进入疗愈酒吧"
          - "与小北对话"
          - "分享一个你在现实中回避的事情"
        reward: "100金币 + 道具：勇气徽章"
        note: "这里的对话是自由的，AI会引导但不强迫"

    - quest_1_3:
        name: "镜像大厅"
        type: "挑战"
        description: "进入镜像大厅，面对'镜中的自己'"
        objectives:
          - "进入镜像大厅"
          - "完成'镜像对话'挑战"
          - "获得勇气之钥"
        reward: "200金币 + 勇气之钥 + 成就：直面镜中人"
```

#### 2.2.2 镜像对话挑战（详细设计）

```yaml
mirror_dialogue_challenge:
  name: "镜像对话"
  location: "镜像大厅"
  duration: "15-30分钟"
  difficulty: "情感难度：中等"

  setup:
    scene: "玩家进入一个被镜子环绕的圆形大厅"
    visual: "镜中的倒影会'独立行动'"
    narrative: |
      时守的声音在大厅中回响：
      "勇气，不是没有恐惧...而是尽管恐惧，依然前行。
      现在，直视镜中的自己。
      告诉它，你一直不敢说的话。"

  gameplay_flow:
    phase_1_preparation:
      name: "准备阶段"
      description: "AI询问玩家想练习的场景"
      ai_prompt: |
        你是引导玩家进行'镜像对话'挑战的AI。
        首先，温和地询问玩家：
        "在现实生活中，有没有一个人，或者一种情况，是你一直想说些什么，却没有勇气说的？"
        根据玩家的回答，准备模拟场景。
      examples:
        - "想对老板说'我不同意'"
        - "想对父母说'请尊重我的选择'"
        - "想对朋友说'你伤害了我'"
        - "想对自己说'我值得被爱'"

    phase_2_simulation:
      name: "模拟阶段"
      description: "AI扮演玩家描述的'对方'"
      ai_prompt: |
        现在，你要扮演玩家描述的那个"对方"（可能是老板、父母、朋友等）。
        根据玩家的描述，合理地扮演这个角色。

        重要原则：
        1. 开始时可以有些"难搞"，模拟真实情况
        2. 但要随着对话进展，逐渐展现理解
        3. 最终目标是让玩家体验到"被倾听"的感觉
        4. 不要太快妥协，但也不要一直对抗
        5. 这是一个治愈性的体验，不是真实冲突

    phase_3_breakthrough:
      name: "突破阶段"
      description: "玩家成功表达自己，'对方'展现理解"
      completion_conditions:
        - "玩家表达了自己真实的感受"
        - "玩家说出了想说但没说的话"
        - "对话进行了至少5轮"
      ai_response: |
        当检测到玩家成功表达后，'对方'应该展现理解：
        "...我从来不知道你是这么想的。谢谢你告诉我。"
        然后镜像碎裂，露出勇气之钥。

    phase_4_reflection:
      name: "反思阶段"
      description: "小北出现，帮助玩家整理感受"
      bei_dialogue: |
        "你刚才很勇敢。（微笑）
        不管在现实中会怎样，至少在这里，你已经迈出了第一步。
        这把钥匙，属于你。"

  rewards:
    - key: "勇气之钥"
    - achievement: "直面镜中人"
    - gold: 200
    - exp: 500
    - item: "破碎的镜片（纪念品）"

  fail_safe:
    - "如果玩家中途想退出，允许退出但不给钥匙"
    - "如果玩家长时间沉默，小北会介入询问是否需要帮助"
    - "如果检测到极端情绪，触发危机干预"
```

### 2.3 第二把钥匙：释然之钥

#### 2.3.1 任务线

```yaml
chapter_2_quest_line:
  name: "释然之路"
  location: "奇幻区 - 记忆森林"
  theme: "放下过去，接纳自己"
  key: "释然之钥"

  quests:
    - quest_2_1:
        name: "森林入口"
        type: "探索"
        description: "进入记忆森林，感受月光与萤火"
        objectives:
          - "通过传送门进入奇幻区"
          - "探索林间小径"
          - "找到世界树"
        reward: "50金币"

    - quest_2_2:
        name: "世界树下"
        type: "对话"
        description: "在世界树下与小北聊聊过去"
        objectives:
          - "爬上世界树休息室"
          - "与小北对话"
          - "分享一个你放不下的遗憾"
        reward: "100金币 + 道具：萤火瓶"

    - quest_2_3:
        name: "记忆迷宫"
        type: "挑战"
        description: "进入由你的记忆构成的迷宫"
        objectives:
          - "进入记忆迷宫"
          - "完成'记忆迷宫'挑战"
          - "获得释然之钥"
        reward: "200金币 + 释然之钥 + 成就：与过去和解"
```

#### 2.3.2 记忆迷宫挑战（详细设计）

```yaml
memory_maze_challenge:
  name: "记忆迷宫"
  location: "记忆迷宫"
  duration: "20-40分钟"
  difficulty: "情感难度：较高"

  setup:
    scene: "玩家进入一个迷宫，墙壁是半透明的'记忆片段'"
    visual: "走廊中漂浮着发光的记忆碎片"
    narrative: |
      时守的声音在迷宫入口响起：
      "这座迷宫，由你的记忆构成。
      每一条死路，都是一个你放不下的遗憾。
      想要走出去，你必须...学会放下。"

  gameplay_flow:
    phase_1_enter:
      name: "进入迷宫"
      description: "玩家进入迷宫，小北作为向导陪伴"
      bei_dialogue: "我会陪着你。不管看到什么，记住，那只是记忆。"

    phase_2_memory_stations:
      name: "记忆站点"
      description: "迷宫中有3个'记忆站点'，每个代表一种遗憾"
      count: 3
      types:
        - station_regret:
            name: "遗憾之门"
            theme: "我本可以..."
            visual: "一扇锁着的门"
            ai_prompt: |
              引导玩家讨论一个"如果当时...就好了"的遗憾。
              帮助玩家认识到：
              1. 当时的选择，在当时的条件下是合理的
              2. 无法改变过去，但可以改变对过去的看法
              3. 遗憾本身不是问题，被遗憾困住才是

        - station_guilt:
            name: "愧疚之镜"
            theme: "对不起..."
            visual: "一面裂开的镜子"
            ai_prompt: |
              引导玩家讨论一个让自己感到愧疚的事情。
              帮助玩家认识到：
              1. 意识到错误本身就是成长
              2. 可以原谅自己，同时记住教训
              3. 如果可能，可以用行动弥补，但不必永远背负

        - station_loss:
            name: "失去之河"
            theme: "再也没有..."
            visual: "一条流淌的光之河"
            ai_prompt: |
              引导玩家讨论一个失去的人/事/物。
              帮助玩家认识到：
              1. 悲伤是爱的另一种形式
              2. 失去不意味着结束，记忆和影响还在
              3. 允许自己悲伤，也允许自己继续前行

    phase_3_release:
      name: "释放仪式"
      description: "在迷宫中心的遗忘湖边，进行象征性的'放下'"
      ritual:
        - "玩家选择一个'记忆碎片'投入湖中"
        - "碎片溶解，变成光点升上天空"
        - "小北陪伴并给予肯定"
      bei_dialogue: |
        "放下，不是忘记。
        是让过去成为过去，而不是让它决定现在。
        你做到了。（微笑）"

    phase_4_exit:
      name: "走出迷宫"
      description: "迷宫的出口出现，释然之钥就在那里"
      visual: "迷宫墙壁变透明，露出出口和发光的钥匙"

  rewards:
    - key: "释然之钥"
    - achievement: "与过去和解"
    - gold: 200
    - exp: 500
    - item: "记忆水晶（可存储一段对话）"

  emotional_safety:
    - "每个站点都可以跳过"
    - "小北全程陪伴"
    - "如果玩家情绪过于激动，提供休息选项"
    - "危机词检测持续运行"
```

### 2.4 第三把钥匙：希望之钥

#### 2.4.1 任务线

```yaml
chapter_3_quest_line:
  name: "希望之路"
  location: "科幻区 - 未来空间站"
  theme: "拥抱未来，相信可能"
  key: "希望之钥"

  quests:
    - quest_3_1:
        name: "星际穿越"
        type: "探索"
        description: "进入未来空间站，俯瞰星海"
        objectives:
          - "通过传送门进入科幻区"
          - "探索观景长廊"
          - "找到指挥中心"
        reward: "50金币"

    - quest_3_2:
        name: "指挥中心"
        type: "对话"
        description: "在指挥中心与小北聊聊对未来的期待和恐惧"
        objectives:
          - "进入指挥中心"
          - "与小北对话"
          - "分享一个关于未来的担忧"
        reward: "100金币 + 道具：星图碎片"

    - quest_3_3:
        name: "未来建筑师"
        type: "挑战"
        description: "在时间模拟器中，构建你的理想未来"
        objectives:
          - "进入时间模拟器"
          - "完成'未来建筑师'挑战"
          - "获得希望之钥"
        reward: "200金币 + 希望之钥 + 成就：未来建筑师"
```

#### 2.4.2 未来建筑师挑战（详细设计）

```yaml
future_architect_challenge:
  name: "未来建筑师"
  location: "时间模拟器"
  duration: "20-35分钟"
  difficulty: "情感难度：中等"

  setup:
    scene: "玩家站在一个圆形平台上，周围是无尽的星空"
    visual: "全息投影会根据对话内容动态变化"
    narrative: |
      时守的声音从星空中传来：
      "未来，不是等来的，是你一步步走出来的。
      但在走之前，你需要知道...你想走向哪里。
      今天，你是自己未来的建筑师。"

  gameplay_flow:
    phase_1_explore:
      name: "探索可能"
      description: "AI帮助玩家探索对未来的各种设想"
      ai_prompt: |
        你是一个帮助玩家探索未来可能性的AI。
        通过问答，帮助玩家思考：
        1. 如果不考虑任何限制，你最想做什么？
        2. 五年后，你希望自己是什么样子？
        3. 什么会让你觉得生活有意义？

        每个回答，都会在全息投影中生成相应的画面。
      hologram_generation:
        - "如果玩家说想旅行 → 显示世界各地的风景"
        - "如果玩家说想创业 → 显示一个办公室/工作室"
        - "如果玩家说想有家庭 → 显示温馨的家庭场景"

    phase_2_obstacles:
      name: "直面障碍"
      description: "AI帮助玩家识别内心的障碍"
      ai_prompt: |
        现在，温和地询问：
        "是什么让你觉得这个未来很难实现？"

        帮助玩家认识到：
        1. 有些障碍是真实的限制，需要逐步解决
        2. 有些障碍是内心的恐惧，需要勇气面对
        3. 大部分情况下，障碍没有想象中那么大
      hologram_change:
        - "障碍被说出时，全息画面会蒙上阴影"
        - "当玩家说出解决思路时，阴影逐渐消散"

    phase_3_build:
      name: "构建蓝图"
      description: "玩家亲手'构建'自己的未来蓝图"
      interaction:
        - "玩家选择3个关键词代表自己的未来愿景"
        - "系统基于关键词生成一个'未来城市'的全息模型"
        - "城市的样子代表玩家心中的理想生活"
      ai_summary: |
        基于玩家的选择，生成一段描述：
        "在你的未来蓝图中，[关键词1]是基石，[关键词2]是方向，[关键词3]是意义。
        这不是终点，是起点。从今天开始，每一步都在接近它。"

    phase_4_commit:
      name: "许下承诺"
      description: "玩家对自己的未来做出一个小承诺"
      ai_prompt: |
        "现在，对自己许一个小小的承诺吧。
        不需要很大，一个你接下来一周可以做到的事情就好。
        这将是你走向这个未来的第一步。"
      examples:
        - "我承诺这周至少运动一次"
        - "我承诺跟一个朋友联系"
        - "我承诺对自己说一句鼓励的话"
      bei_dialogue: |
        "（郑重地点头）我记住了。
        下次见面，我会问你的哦~（微笑）
        希望之钥，属于相信明天的你。"

  rewards:
    - key: "希望之钥"
    - achievement: "未来建筑师"
    - gold: 200
    - exp: 500
    - item: "未来蓝图（可查看自己构建的全息图）"

  follow_up:
    - "小北会在后续对话中询问承诺的进展"
    - "如果玩家完成了承诺，给予额外奖励"
```

---

## 3. 支线任务系统

### 3.1 支线任务类型

```yaml
side_quest_types:
  exploration:
    name: "探索任务"
    description: "发现隐藏区域、收集物品"
    examples:
      - "找到镜像之城的5个隐藏涂鸦"
      - "在记忆森林收集10颗萤火虫"
      - "探索空间站的所有舱室"
    rewards: "金币 + 经验 + 收集品"

  social:
    name: "社交任务"
    description: "与其他玩家互动"
    examples:
      - "与3个不同的玩家打招呼"
      - "帮助一个新玩家完成教程"
      - "在聊天室分享一条建议"
    rewards: "金币 + 社交点数 + 称号"

  npc_story:
    name: "NPC故事线"
    description: "深入了解NPC的背景"
    examples:
      - "听老莫讲述他的旅行故事"
      - "帮艾拉整理信息大厅"
      - "陪芝麻探险发现宝藏"
    rewards: "金币 + NPC好感度 + 特殊道具"

  daily:
    name: "每日任务"
    description: "每日刷新的简单任务"
    count: 3
    examples:
      - "与小北对话5分钟"
      - "探索任意区域"
      - "完成1次小游戏"
    rewards: "金币 + 每日积分"

  weekly:
    name: "每周挑战"
    description: "每周刷新的中等难度任务"
    count: 1
    examples:
      - "完成本周所有每日任务"
      - "帮助10个玩家"
      - "与小北进行一次深度对话（超过15分钟）"
    rewards: "大量金币 + 钻石 + 限定道具"
```

### 3.2 任务系统UI

```yaml
quest_ui:
  quest_log:
    position: "右上角图标，点击展开"
    sections:
      - main_quest: "主线任务"
      - side_quest: "支线任务"
      - daily_quest: "每日任务"
      - weekly_quest: "每周挑战"

    display:
      - quest_name: "任务名称"
      - quest_description: "任务描述"
      - objectives: "目标列表（带勾选）"
      - progress: "进度条"
      - rewards: "奖励预览"

  quest_tracker:
    position: "屏幕右侧"
    description: "显示当前追踪的任务（最多3个）"
    features:
      - "实时更新进度"
      - "点击可导航到目标"

  quest_completion:
    animation: "任务完成时播放庆祝动画"
    sound: "叮~的完成音效"
    popup: "显示获得的奖励"
```

---

## 4. 成就系统

### 4.1 成就分类

```yaml
achievement_categories:
  story:
    name: "故事成就"
    color: "金色"
    achievements:
      - name: "直面镜中人"
        description: "完成镜像对话挑战"
        reward: "200金币 + 称号"

      - name: "与过去和解"
        description: "完成记忆迷宫挑战"
        reward: "200金币 + 称号"

      - name: "未来建筑师"
        description: "完成未来建筑师挑战"
        reward: "200金币 + 称号"

      - name: "心灵觉醒者"
        description: "集齐三把钥匙，进入心灵圣殿"
        reward: "500金币 + 稀有皮肤 + 称号"

  exploration:
    name: "探索成就"
    color: "绿色"
    achievements:
      - name: "旅行者"
        description: "到达所有区域"
        reward: "100金币"

      - name: "探险家"
        description: "发现所有隐藏区域"
        reward: "300金币 + 地图皮肤"

      - name: "收集狂"
        description: "收集100个隐藏物品"
        reward: "200金币"

  social:
    name: "社交成就"
    color: "蓝色"
    achievements:
      - name: "初次见面"
        description: "与第一个玩家互动"
        reward: "50金币"

      - name: "人气王"
        description: "添加50个好友"
        reward: "200金币 + 社交表情包"

      - name: "助人为乐"
        description: "帮助100个玩家"
        reward: "300金币 + 称号"

  emotional:
    name: "情感成就"
    color: "粉色"
    achievements:
      - name: "打开心扉"
        description: "与小北进行第一次深度对话"
        reward: "100金币"

      - name: "老朋友"
        description: "与小北对话累计10小时"
        reward: "300金币 + 小北特殊皮肤"

      - name: "心灵伙伴"
        description: "连续30天与小北对话"
        reward: "500金币 + 永久称号"

  pet:
    name: "宠物成就"
    color: "橙色"
    achievements:
      - name: "芝麻的朋友"
        description: "与芝麻互动100次"
        reward: "100金币"

      - name: "宠物大师"
        description: "解锁所有宠物形态"
        reward: "200金币"

      - name: "寻宝猎人"
        description: "让芝麻发现20个宝藏"
        reward: "150金币"
```

### 4.2 成就展示

```yaml
achievement_display:
  notification:
    trigger: "解锁成就时"
    animation: "从屏幕顶部滑入"
    content: "成就图标 + 名称 + 描述"
    sound: "成就解锁音效"
    duration: "3秒"

  achievement_page:
    access: "主菜单 > 成就"
    layout: "网格展示，按分类分组"
    states:
      - locked: "灰色，显示解锁条件"
      - unlocked: "彩色，显示解锁时间"
      - new: "带'NEW'标记"

  showcase:
    description: "玩家可以选择3个成就展示在名片上"
```

---

## 5. 进度与存档系统

### 5.1 存档数据结构

```python
SAVE_DATA_SCHEMA = {
    "user_id": "用户唯一ID",
    "save_version": "存档版本号",
    "created_at": "创建时间",
    "updated_at": "最后更新时间",

    "player_data": {
        "nickname": "昵称",
        "avatar": {
            "base_model": "基础模型ID",
            "customization": {},  # 自定义数据
            "current_outfit": "当前装扮ID",
        },
        "level": "等级",
        "exp": "经验值",
        "gold": "金币",
        "diamond": "钻石",
        "play_time_minutes": "游戏时间（分钟）",
    },

    "quest_progress": {
        "main_quest": {
            "current_chapter": "当前章节",
            "chapter_1_complete": False,
            "chapter_2_complete": False,
            "chapter_3_complete": False,
            "sanctuary_unlocked": False,
        },
        "side_quests": {
            "completed": [],  # 已完成的支线任务ID
            "in_progress": [],  # 进行中的任务
        },
        "daily_quests": {
            "date": "日期",
            "quests": [],
            "completed": [],
        },
    },

    "keys": {
        "courage_key": False,
        "release_key": False,
        "hope_key": False,
    },

    "inventory": {
        "items": [],  # 物品列表
        "outfits": [],  # 已解锁的服装
        "decorations": [],  # 装饰品
    },

    "achievements": {
        "unlocked": [],  # 已解锁成就ID
        "showcase": [],  # 展示的成就（最多3个）
    },

    "social": {
        "friends": [],  # 好友列表
        "blocked": [],  # 屏蔽列表
    },

    "npc_relationships": {
        "aela": {"affinity": 0, "dialogues_count": 0},
        "momo": {"affinity": 0, "purchases_count": 0},
        "chronos": {"affinity": 0, "quests_completed": 0},
        "bei": {"affinity": 0, "dialogue_minutes": 0},
        "sesame": {"affinity": 0, "interactions_count": 0},
    },

    "exploration": {
        "visited_areas": [],  # 已访问区域
        "discovered_secrets": [],  # 发现的秘密
        "collected_items": [],  # 收集物
    },

    "settings": {
        "volume_music": 0.8,
        "volume_sfx": 0.8,
        "volume_voice": 1.0,
        "text_speed": "normal",
        "camera_sensitivity": 0.5,
    },
}
```

### 5.2 存档触发时机

```yaml
auto_save_triggers:
  - "每5分钟自动保存"
  - "完成任务时"
  - "获得钥匙时"
  - "购买物品后"
  - "退出游戏前"
  - "切换区域时"

manual_save:
  enabled: false  # 不提供手动存档，自动存档足够
```

---

**下一篇 → `06_Player_System.md`（玩家系统设计）**
