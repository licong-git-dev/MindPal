# MindPal PRD - 06 玩家系统设计

> 本文档详细定义玩家Avatar、控制系统、背包、等级系统

---

## 1. Avatar系统

### 1.1 Avatar创建流程

```yaml
avatar_creation_flow:
  step_1_base:
    name: "选择基础形象"
    options:
      gender:
        - "男性"
        - "女性"
        - "中性"
      body_type:
        - "标准"
        - "高挑"
        - "娇小"
      skin_tone:
        - "肤色1（浅）"
        - "肤色2"
        - "肤色3"
        - "肤色4"
        - "肤色5（深）"

  step_2_face:
    name: "面部定制"
    options:
      face_shape: ["圆形", "方形", "椭圆", "心形"]
      eyes: ["大眼", "细眼", "标准", "下垂眼"]
      eyebrows: ["自然", "粗眉", "细眉", "一字眉"]
      nose: ["标准", "高挺", "小巧"]
      mouth: ["微笑", "标准", "厚唇"]

  step_3_hair:
    name: "发型定制"
    options:
      style: ["短发", "中发", "长发", "扎发", "光头"]
      color: ["黑色", "棕色", "金色", "红色", "蓝色", "粉色", "渐变"]

  step_4_outfit:
    name: "初始服装"
    free_options:
      - "休闲套装（白T+牛仔裤）"
      - "运动套装"
      - "简约裙装"
    note: "更多服装需要在商店购买"

  step_5_name:
    name: "设置昵称"
    rules:
      - "2-12个字符"
      - "不能包含敏感词"
      - "不能与已有玩家重复"
```

### 1.2 Avatar数据结构

```python
AVATAR_SCHEMA = {
    "avatar_id": "唯一ID",
    "base": {
        "gender": "male/female/neutral",
        "body_type": "standard/tall/petite",
        "skin_tone": 1-5,
    },
    "face": {
        "shape": "round/square/oval/heart",
        "eyes": "big/narrow/standard/droopy",
        "eyebrows": "natural/thick/thin/straight",
        "nose": "standard/high/small",
        "mouth": "smile/standard/full",
    },
    "hair": {
        "style_id": "发型ID",
        "color": "#RRGGBB",
        "gradient": None or "#RRGGBB",
    },
    "outfit": {
        "top": "上衣ID",
        "bottom": "下装ID",
        "shoes": "鞋子ID",
        "accessory_1": "配饰1",
        "accessory_2": "配饰2",
    },
    "special_effects": {
        "aura": None,  # 光环效果
        "trail": None,  # 拖尾效果
        "pet_follow": "sesame",  # 跟随宠物
    },
}
```

### 1.3 Avatar动画列表

```yaml
avatar_animations:
  locomotion:
    - idle: "站立待机"
    - walk: "行走"
    - run: "跑步"
    - jump: "跳跃"
    - fall: "下落"
    - land: "着陆"

  social:
    - wave: "挥手"
    - bow: "鞠躬"
    - clap: "鼓掌"
    - thumbs_up: "点赞"
    - dance_1: "舞蹈1"
    - dance_2: "舞蹈2"

  emotional:
    - happy: "开心"
    - sad: "难过"
    - think: "思考"
    - nod: "点头"
    - shake_head: "摇头"

  interaction:
    - sit: "坐下"
    - stand_up: "起立"
    - talk: "说话（嘴部动画）"
    - pick_up: "捡起物品"

  special:
    - teleport_in: "传送进入"
    - teleport_out: "传送离开"
    - level_up: "升级特效"
```

---

## 2. 控制系统

### 2.1 键盘控制方案

```yaml
keyboard_controls:
  movement:
    W: "前进"
    S: "后退"
    A: "左移"
    D: "右移"
    Space: "跳跃"
    Shift: "切换跑步/行走"

  camera:
    mouse_move: "视角旋转（按住右键）"
    scroll_wheel: "缩放"
    middle_mouse: "重置视角"

  interaction:
    E: "交互（与NPC对话/拾取物品）"
    F: "快速操作"
    Tab: "切换目标"

  ui:
    Escape: "打开菜单/关闭当前UI"
    I: "打开背包"
    M: "打开地图"
    J: "打开任务日志"
    T: "打开聊天"
    Enter: "发送聊天/确认"

  quick_access:
    1-5: "快捷栏道具"
    B: "召唤小北"
    P: "与芝麻互动"

  emotes:
    F1-F4: "快捷表情"
```

### 2.2 手柄控制方案（可选支持）

```yaml
gamepad_controls:
  left_stick: "移动"
  right_stick: "视角"
  A: "跳跃"
  B: "取消/返回"
  X: "交互"
  Y: "打开菜单"
  LB: "召唤小北"
  RB: "切换跑步"
  LT: "缩小视角"
  RT: "放大视角"
  D-pad: "快捷栏"
  Start: "暂停菜单"
  Select: "地图"
```

### 2.3 玩家控制器实现（GDScript伪代码）

```gdscript
# PlayerController.gd
extends CharacterBody3D

# 移动参数
const WALK_SPEED = 4.0
const RUN_SPEED = 8.0
const JUMP_VELOCITY = 6.0
const GRAVITY = 20.0

# 状态
var is_running := false
var is_grounded := true
var current_speed := WALK_SPEED

# 输入处理
func _physics_process(delta: float) -> void:
    # 获取输入方向
    var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_backward")
    var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()

    # 切换跑步
    if Input.is_action_just_pressed("toggle_run"):
        is_running = !is_running
    current_speed = RUN_SPEED if is_running else WALK_SPEED

    # 应用移动
    if direction:
        velocity.x = direction.x * current_speed
        velocity.z = direction.z * current_speed
        # 播放移动动画
        _play_movement_animation()
    else:
        velocity.x = move_toward(velocity.x, 0, current_speed)
        velocity.z = move_toward(velocity.z, 0, current_speed)
        # 播放待机动画
        _play_idle_animation()

    # 重力和跳跃
    if not is_on_floor():
        velocity.y -= GRAVITY * delta
    elif Input.is_action_just_pressed("jump"):
        velocity.y = JUMP_VELOCITY

    move_and_slide()

# 交互处理
func _input(event: InputEvent) -> void:
    if event.is_action_pressed("interact"):
        _try_interact()

func _try_interact() -> void:
    # 检测前方可交互对象
    var interactable = _get_nearest_interactable()
    if interactable:
        interactable.interact(self)
```

---

## 3. 背包系统

### 3.1 物品分类

```yaml
item_categories:
  consumables:
    name: "消耗品"
    icon: "药水图标"
    examples:
      - "治愈药水（恢复NPC好感度）"
      - "传送卷轴（快速传送）"
      - "经验书（获得经验）"
      - "宠物零食（喂芝麻）"

  equipment:
    name: "装备"
    icon: "衣服图标"
    subcategories:
      - "上衣"
      - "下装"
      - "鞋子"
      - "配饰"
      - "特效"

  collectibles:
    name: "收集品"
    icon: "星星图标"
    examples:
      - "勇气之钥"
      - "释然之钥"
      - "希望之钥"
      - "记忆碎片"
      - "隐藏物品"

  materials:
    name: "材料"
    icon: "宝石图标"
    examples:
      - "星光碎片"
      - "萤火精华"
      - "时间之沙"

  special:
    name: "特殊物品"
    icon: "礼盒图标"
    examples:
      - "任务物品"
      - "活动道具"
```

### 3.2 背包数据结构

```python
INVENTORY_SCHEMA = {
    "capacity": 100,  # 背包容量
    "items": [
        {
            "item_id": "物品唯一ID",
            "item_type": "物品类型",
            "quantity": "数量（可堆叠物品）",
            "acquired_at": "获得时间",
            "metadata": {}  # 额外数据
        }
    ],
    "equipped": {
        "top": "已装备上衣ID",
        "bottom": "已装备下装ID",
        "shoes": "已装备鞋子ID",
        "accessory_1": "已装备配饰1",
        "accessory_2": "已装备配饰2",
        "aura": "已装备光环",
        "trail": "已装备拖尾",
    },
    "quick_bar": ["快捷栏物品ID", None, None, None, None]  # 5格快捷栏
}
```

### 3.3 背包UI设计

```yaml
inventory_ui:
  layout:
    left_panel:
      width: "30%"
      content: "角色预览（3D模型）"

    right_panel:
      width: "70%"
      content:
        - tabs: ["全部", "消耗品", "装备", "收集品", "材料", "特殊"]
        - grid: "5x8格子"
        - item_info: "选中物品详情"

  item_slot:
    size: "64x64px"
    states:
      - empty: "空格子"
      - filled: "物品图标 + 数量"
      - selected: "高亮边框"
      - equipped: "装备标记"

  item_actions:
    left_click: "选中/使用"
    right_click: "打开菜单（使用/装备/丢弃/详情）"
    double_click: "快速使用/装备"
    drag: "移动到其他格子/快捷栏"

  search_sort:
    search: "按名称搜索"
    sort_options: ["默认", "名称", "类型", "获得时间", "稀有度"]
```

---

## 4. 等级与经验系统

### 4.1 等级设计

```yaml
level_system:
  max_level: 50
  exp_curve: "二次函数增长"

  level_exp_table:
    level_1: 0
    level_2: 100
    level_3: 250
    level_4: 450
    level_5: 700
    # ... 以此类推
    level_50: 50000

  level_up_rewards:
    every_level:
      - "100金币"
      - "解锁成就进度"

    milestone_levels:
      level_5: "解锁社交功能"
      level_10: "解锁每日任务"
      level_15: "解锁每周挑战"
      level_20: "解锁高级表情包"
      level_30: "解锁特殊区域"
      level_40: "解锁大师称号"
      level_50: "解锁传说皮肤"
```

### 4.2 经验获取方式

```yaml
exp_sources:
  quests:
    main_quest: "100-500经验/任务"
    side_quest: "50-200经验/任务"
    daily_quest: "30经验/任务"
    weekly_quest: "200经验/任务"

  exploration:
    discover_area: "50经验/新区域"
    find_secret: "30经验/秘密"
    collect_item: "10经验/收集品"

  social:
    add_friend: "20经验（每日上限5次）"
    help_player: "30经验"
    chat_participation: "5经验/10条消息"

  npc_interaction:
    dialogue_with_bei: "10经验/5分钟（每日上限100经验）"
    complete_npc_story: "100经验"

  achievements:
    unlock_achievement: "经验根据成就等级"
```

### 4.3 等级UI显示

```yaml
level_display:
  hud:
    position: "左上角，头像下方"
    elements:
      - "等级数字"
      - "经验条（当前/所需）"
      - "升级时闪光效果"

  profile:
    position: "个人资料页"
    elements:
      - "等级徽章"
      - "总经验"
      - "下一等级所需"
      - "等级奖励预览"

  level_up_popup:
    trigger: "升级时"
    animation: "华丽的升级特效"
    content:
      - "恭喜升级！"
      - "新等级"
      - "解锁内容"
      - "获得奖励"
    duration: "3秒（可点击跳过）"
```

---

## 5. 设置系统

### 5.1 设置选项

```yaml
settings_menu:
  graphics:
    name: "画面设置"
    options:
      quality:
        type: "select"
        options: ["低", "中", "高", "超高"]
        default: "高"

      resolution:
        type: "select"
        options: ["1280x720", "1920x1080", "2560x1440", "3840x2160"]
        default: "系统检测"

      fullscreen:
        type: "toggle"
        default: true

      vsync:
        type: "toggle"
        default: true

      fps_limit:
        type: "select"
        options: ["30", "60", "120", "不限制"]
        default: "60"

      shadow_quality:
        type: "select"
        options: ["关闭", "低", "中", "高"]
        default: "中"

      anti_aliasing:
        type: "select"
        options: ["关闭", "FXAA", "MSAA 2x", "MSAA 4x"]
        default: "FXAA"

  audio:
    name: "音频设置"
    options:
      master_volume:
        type: "slider"
        range: [0, 100]
        default: 80

      music_volume:
        type: "slider"
        range: [0, 100]
        default: 70

      sfx_volume:
        type: "slider"
        range: [0, 100]
        default: 80

      voice_volume:
        type: "slider"
        range: [0, 100]
        default: 100

      mute_when_unfocused:
        type: "toggle"
        default: true

  controls:
    name: "控制设置"
    options:
      mouse_sensitivity:
        type: "slider"
        range: [0.1, 2.0]
        default: 1.0

      invert_y:
        type: "toggle"
        default: false

      key_bindings:
        type: "rebind"
        description: "自定义按键绑定"

  gameplay:
    name: "游戏设置"
    options:
      language:
        type: "select"
        options: ["简体中文", "English"]
        default: "简体中文"

      text_speed:
        type: "select"
        options: ["慢", "正常", "快", "即时"]
        default: "正常"

      auto_save_interval:
        type: "select"
        options: ["1分钟", "5分钟", "10分钟"]
        default: "5分钟"

      show_hints:
        type: "toggle"
        default: true

      show_tutorials:
        type: "toggle"
        default: true

  privacy:
    name: "隐私设置"
    options:
      allow_friend_requests:
        type: "toggle"
        default: true

      show_online_status:
        type: "toggle"
        default: true

      allow_party_invites:
        type: "toggle"
        default: true

      chat_filter:
        type: "toggle"
        default: true
```

---

**下一篇 → `07_Multiplayer_System.md`（多人系统设计）**
