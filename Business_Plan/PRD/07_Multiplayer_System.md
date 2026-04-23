# MindPal PRD - 07 多人系统设计

> 本文档详细定义多人在线、社交功能、组队系统、聊天系统

---

## 1. 多人架构概述

### 1.1 网络架构

```
┌─────────────────────────────────────────────────────────────┐
│                     多人网络架构                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     ┌─────────┐   ┌─────────┐   ┌─────────┐               │
│     │ 客户端1  │   │ 客户端2  │   │ 客户端N  │               │
│     └────┬────┘   └────┬────┘   └────┬────┘               │
│          │             │             │                      │
│          └─────────────┼─────────────┘                      │
│                        │                                    │
│                        ▼                                    │
│                 ┌─────────────┐                            │
│                 │  负载均衡器  │                            │
│                 └──────┬──────┘                            │
│                        │                                    │
│          ┌─────────────┼─────────────┐                     │
│          │             │             │                      │
│          ▼             ▼             ▼                      │
│    ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│    │ 游戏服务器│  │ 游戏服务器│  │ 游戏服务器│               │
│    │  (区域1)  │  │  (区域2)  │  │  (区域3)  │               │
│    └──────────┘  └──────────┘  └──────────┘               │
│                        │                                    │
│                        ▼                                    │
│               ┌───────────────┐                            │
│               │   共享数据库   │                            │
│               │ (用户/社交/AI) │                            │
│               └───────────────┘                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 房间系统

```yaml
room_system:
  room_types:
    central_plaza:
      name: "中央广场"
      max_players: 100
      instances: "动态创建（满100人开新房间）"
      sync_rate: "20Hz"

    mirror_city:
      name: "镜像之城"
      max_players: 50
      instances: "动态创建"
      sync_rate: "20Hz"

    memory_forest:
      name: "记忆森林"
      max_players: 50
      instances: "动态创建"
      sync_rate: "20Hz"

    future_station:
      name: "未来空间站"
      max_players: 50
      instances: "动态创建"
      sync_rate: "20Hz"

    private_instance:
      name: "私人房间（队伍）"
      max_players: 5
      instances: "按队伍创建"
      sync_rate: "30Hz"

  room_selection:
    strategy: "自动分配到人数适中的房间"
    friend_priority: "优先与好友同房间"
    party_together: "队伍成员必须同房间"
```

### 1.3 玩家同步协议

```python
# 玩家状态同步数据包
PLAYER_SYNC_PACKET = {
    "type": "player_sync",
    "timestamp": "服务器时间戳",
    "player_id": "玩家ID",
    "position": {
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    },
    "rotation": {
        "y": 0.0,  # 只同步Y轴旋转
    },
    "state": {
        "animation": "idle/walk/run/jump/sit/talk",
        "is_talking": False,
        "emote": None,  # 当前表情动作
    },
    "appearance_hash": "外观哈希（用于检测是否需要更新外观）",
}

# 同步频率配置
SYNC_CONFIG = {
    "send_rate_hz": 20,  # 客户端发送频率
    "receive_rate_hz": 20,  # 服务端广播频率
    "interpolation_delay_ms": 100,  # 插值延迟
    "position_threshold": 0.01,  # 位置变化阈值（小于此值不发送）
    "rotation_threshold": 1.0,  # 旋转变化阈值（度）
}
```

---

## 2. 社交系统

### 2.1 好友系统

```yaml
friend_system:
  features:
    - "添加好友"
    - "删除好友"
    - "屏蔽玩家"
    - "查看好友在线状态"
    - "查看好友所在位置"
    - "传送到好友身边"
    - "邀请好友组队"

  friend_request:
    methods:
      - "通过昵称搜索"
      - "点击附近玩家头像"
      - "通过聊天中@的玩家"
    flow:
      1: "发送好友请求"
      2: "对方收到通知"
      3: "对方选择接受/拒绝"
      4: "接受后双方互为好友"

  friend_list:
    display:
      online_first: true
      sort_options: ["在线优先", "亲密度", "添加时间", "昵称"]
    info_per_friend:
      - "昵称"
      - "在线状态"
      - "当前位置"
      - "亲密度等级"
      - "最后在线时间"

  friend_limit:
    free_user: 50
    vip_user: 200

  intimacy:
    name: "亲密度"
    increase_by:
      - "一起在线：1点/10分钟"
      - "一起组队：2点/10分钟"
      - "完成任务：10点/任务"
      - "赠送礼物：根据礼物价值"
    levels:
      - "普通好友：0-99"
      - "好朋友：100-499"
      - "挚友：500-999"
      - "灵魂伴侣：1000+"
    benefits:
      - "亲密度等级显示在名字旁"
      - "高亲密度解锁特殊互动动作"
```

### 2.2 好友UI设计

```yaml
friend_ui:
  access: "主菜单 > 好友（或快捷键O）"

  layout:
    left_panel:
      width: "30%"
      content:
        - "好友列表标签"
        - "好友请求标签"
        - "屏蔽列表标签"
        - "搜索框"

    right_panel:
      width: "70%"
      content:
        - "选中好友详情"
        - "操作按钮"

  friend_card:
    elements:
      - "头像"
      - "昵称"
      - "在线状态指示灯"
      - "亲密度图标"
      - "当前位置（在线时）"

    actions:
      - "私聊"
      - "查看资料"
      - "邀请组队"
      - "传送到ta身边"
      - "删除好友"
      - "屏蔽"

  notifications:
    friend_request:
      display: "屏幕右下角弹出"
      sound: "叮~"
      content: "[昵称]想添加你为好友"
      buttons: ["接受", "拒绝", "稍后处理"]

    friend_online:
      display: "屏幕右下角弹出"
      content: "[好友昵称]上线了"
      duration: "3秒"
```

### 2.3 屏蔽系统

```yaml
block_system:
  effects:
    - "看不到被屏蔽玩家的消息"
    - "被屏蔽玩家无法给你发私聊"
    - "不会被分配到同一房间（尽量）"
    - "看不到对方的表情动作"

  unblock:
    method: "在屏蔽列表中点击解除"
    cooldown: "解除后24小时内无法再次屏蔽同一人"

  report:
    integrated: true
    reasons:
      - "骚扰"
      - "不当言论"
      - "作弊"
      - "冒充他人"
      - "其他"
    evidence: "自动附带最近聊天记录"
```

---

## 3. 组队系统

### 3.1 队伍基础

```yaml
party_system:
  max_size: 5
  leader_permissions:
    - "邀请成员"
    - "踢出成员"
    - "转让队长"
    - "解散队伍"
    - "设置队伍目标"

  member_permissions:
    - "离开队伍"
    - "查看队伍信息"
    - "队伍聊天"
    - "查看队友位置"

  party_creation:
    methods:
      - "在好友列表邀请"
      - "点击附近玩家邀请"
      - "使用组队匹配"
    auto_party: "接受邀请自动创建队伍"
```

### 3.2 组队功能

```yaml
party_features:
  shared_location:
    description: "队友位置在小地图显示"
    icon: "队友专属图标"

  party_teleport:
    description: "传送到队长/队友身边"
    cooldown: "30秒"

  shared_quests:
    description: "部分任务可以组队完成"
    progress_share: "探索任务进度共享"
    completion_share: "完成奖励每人独立"

  party_chat:
    description: "队伍专属聊天频道"
    color: "绿色"

  party_voice:
    description: "语音聊天（未来功能）"
    status: "v1.0暂不实现"
```

### 3.3 组队匹配

```yaml
party_matching:
  description: "自动匹配想要组队的玩家"

  match_criteria:
    - "区域相同"
    - "任务目标相似"
    - "等级差距不超过10级"

  flow:
    1: "玩家点击'寻找队伍'"
    2: "选择目标（探索/任务/闲逛）"
    3: "进入匹配队列"
    4: "系统找到合适队伍后通知"
    5: "确认加入"

  queue_time:
    average: "30秒-2分钟"
    timeout: "5分钟未匹配自动取消"
```

### 3.4 组队UI设计

```yaml
party_ui:
  party_frame:
    position: "屏幕左侧"
    display: "队伍成员列表（仅组队时显示）"
    per_member:
      - "头像"
      - "昵称"
      - "在线状态"
      - "队长标记"
    actions:
      - "右键菜单：传送/踢出/私聊"

  party_invite:
    popup: "收到邀请时弹出"
    content: "[邀请者]邀请你加入队伍"
    buttons: ["接受", "拒绝"]
    timeout: "60秒"

  party_menu:
    access: "点击队伍面板或快捷键P"
    options:
      - "邀请成员"
      - "离开队伍"
      - "队伍设置"
      - "传送到队友"
```

---

## 4. 聊天系统

### 4.1 聊天频道

```yaml
chat_channels:
  world:
    name: "世界"
    color: "#FFFFFF"
    scope: "当前服务器所有玩家"
    rate_limit: "5条/分钟"

  local:
    name: "附近"
    color: "#FFFF00"
    scope: "附近50米内玩家"
    rate_limit: "无限制"

  party:
    name: "队伍"
    color: "#00FF00"
    scope: "队伍成员"
    rate_limit: "无限制"

  whisper:
    name: "私聊"
    color: "#FF69B4"
    scope: "一对一"
    rate_limit: "20条/分钟"

  system:
    name: "系统"
    color: "#FF0000"
    scope: "系统公告"
    user_sendable: false
```

### 4.2 聊天功能

```yaml
chat_features:
  basic:
    - "发送文字消息"
    - "表情符号（emoji）"
    - "快捷表情包"
    - "@提及玩家"
    - "历史记录（最近100条）"

  advanced:
    - "消息撤回（2分钟内）"
    - "复制消息"
    - "举报消息"
    - "屏蔽发送者"

  commands:
    - "/w [玩家名] [消息] - 私聊"
    - "/p [消息] - 队伍聊天"
    - "/l [消息] - 附近聊天"
    - "/join [频道] - 加入频道"
```

### 4.3 聊天UI设计

```yaml
chat_ui:
  chat_box:
    position: "屏幕左下角"
    default_state: "最小化（显示最近3条）"
    expanded_state: "展开显示20条"

    elements:
      - "频道标签切换"
      - "消息列表"
      - "输入框"
      - "表情按钮"
      - "发送按钮"

  message_display:
    format: "[频道][时间] 昵称: 消息内容"
    player_name:
      - "可点击查看资料"
      - "颜色根据身份变化"

  input_box:
    placeholder: "按Enter发送消息..."
    max_length: 200
    auto_complete: "输入@时显示附近玩家"

  chat_bubble:
    description: "玩家头顶显示最新消息"
    duration: "5秒"
    max_length: "50字符（超出截断）"
    channels: ["local", "party"]  # 只显示附近和队伍
```

### 4.4 内容过滤

```yaml
content_filter:
  profanity_filter:
    enabled: true
    action: "替换为*"
    custom_words: true  # 允许服务端添加

  spam_detection:
    enabled: true
    rules:
      - "重复消息检测"
      - "频率限制"
      - "全大写检测"
    action: "警告 → 禁言"

  sensitive_content:
    keywords: ["危机关键词列表"]
    action: "标记并通知管理员"

  mute_system:
    auto_mute:
      trigger: "3次警告"
      duration: "10分钟 → 1小时 → 24小时"
    manual_mute:
      by: "管理员"
      duration: "自定义"
```

---

## 5. 玩家交互

### 5.1 附近玩家显示

```yaml
nearby_players:
  display:
    range: "50米"
    nameplates:
      show: true
      content: "昵称 + 等级"
      friend_indicator: "好友显示特殊颜色"
      party_indicator: "队友显示队伍图标"

  interaction:
    method: "点击玩家或接近后按E"
    menu_options:
      - "查看资料"
      - "添加好友"
      - "邀请组队"
      - "私聊"
      - "举报"
      - "屏蔽"
```

### 5.2 表情动作系统

```yaml
emote_system:
  access:
    - "快捷键F1-F4"
    - "表情菜单（按B）"
    - "聊天命令 /emote [名称]"

  emote_list:
    free_emotes:
      - "wave: 挥手"
      - "bow: 鞠躬"
      - "clap: 鼓掌"
      - "thumbs_up: 点赞"
      - "sit: 坐下"
      - "dance_basic: 基础舞蹈"

    unlockable_emotes:
      - "dance_cool: 酷舞（10级解锁）"
      - "backflip: 后空翻（20级解锁）"
      - "heart: 比心（商店购买）"
      - "sleep: 睡觉（成就解锁）"

  emote_interaction:
    description: "部分表情可以与其他玩家互动"
    examples:
      - "high_five: 双人击掌"
      - "hug: 拥抱"
      - "dance_together: 双人舞"
    trigger: "发起者对目标使用，目标确认后触发"
```

### 5.3 交易系统（未来功能）

```yaml
trade_system:
  status: "v1.0暂不实现"
  planned_features:
    - "玩家间物品交换"
    - "摆摊系统"
    - "拍卖行"
```

---

## 6. 多人同步技术细节

### 6.1 状态同步代码示例（GDScript）

```gdscript
# MultiplayerManager.gd
extends Node

var socket: WebSocketClient
var player_id: String
var other_players: Dictionary = {}  # player_id -> RemotePlayer

# 连接服务器
func connect_to_server(server_url: String, token: String) -> void:
    socket = WebSocketClient.new()
    socket.connect("connection_established", self, "_on_connected")
    socket.connect("data_received", self, "_on_data_received")
    socket.connect("connection_closed", self, "_on_disconnected")

    var headers = ["Authorization: Bearer " + token]
    socket.connect_to_url(server_url, [], false, headers)

# 发送位置更新
func send_position_update(position: Vector3, rotation: float, animation: String) -> void:
    var packet = {
        "type": "player_move",
        "data": {
            "position": {"x": position.x, "y": position.y, "z": position.z},
            "rotation": {"y": rotation},
            "animation": animation
        }
    }
    socket.get_peer(1).put_packet(JSON.stringify(packet).to_utf8())

# 接收数据处理
func _on_data_received() -> void:
    var packet = socket.get_peer(1).get_packet()
    var data = JSON.parse(packet.get_string_from_utf8()).result

    match data.type:
        "player_sync":
            _handle_player_sync(data)
        "player_join":
            _handle_player_join(data)
        "player_leave":
            _handle_player_leave(data)
        "chat_message":
            _handle_chat_message(data)

# 处理玩家同步
func _handle_player_sync(data: Dictionary) -> void:
    var pid = data.player_id
    if pid == player_id:
        return  # 忽略自己

    if not other_players.has(pid):
        _spawn_remote_player(pid, data)
    else:
        other_players[pid].update_state(data)

# 生成远程玩家
func _spawn_remote_player(pid: String, data: Dictionary) -> void:
    var remote_player = preload("res://scenes/characters/RemotePlayer.tscn").instantiate()
    remote_player.initialize(pid, data)
    get_tree().current_scene.add_child(remote_player)
    other_players[pid] = remote_player
```

### 6.2 位置插值（GDScript）

```gdscript
# RemotePlayer.gd
extends CharacterBody3D

var target_position: Vector3
var target_rotation: float
var interpolation_speed: float = 10.0

func update_state(data: Dictionary) -> void:
    target_position = Vector3(
        data.position.x,
        data.position.y,
        data.position.z
    )
    target_rotation = data.rotation.y
    _update_animation(data.animation)

func _physics_process(delta: float) -> void:
    # 位置插值
    global_position = global_position.lerp(target_position, interpolation_speed * delta)

    # 旋转插值
    rotation.y = lerp_angle(rotation.y, target_rotation, interpolation_speed * delta)
```

### 6.3 服务端同步逻辑（Python）

```python
# game_sync.py
import asyncio
from typing import Dict, Set
import json

class GameRoom:
    def __init__(self, room_id: str, max_players: int = 50):
        self.room_id = room_id
        self.max_players = max_players
        self.players: Dict[str, dict] = {}  # player_id -> player_state
        self.connections: Dict[str, WebSocket] = {}

    async def add_player(self, player_id: str, websocket: WebSocket, initial_state: dict):
        """添加玩家到房间"""
        self.players[player_id] = initial_state
        self.connections[player_id] = websocket

        # 通知其他玩家有新玩家加入
        await self.broadcast({
            "type": "player_join",
            "player_id": player_id,
            "data": initial_state
        }, exclude={player_id})

        # 发送当前所有玩家给新玩家
        for pid, state in self.players.items():
            if pid != player_id:
                await websocket.send_json({
                    "type": "player_sync",
                    "player_id": pid,
                    **state
                })

    async def remove_player(self, player_id: str):
        """移除玩家"""
        if player_id in self.players:
            del self.players[player_id]
            del self.connections[player_id]

            await self.broadcast({
                "type": "player_leave",
                "player_id": player_id
            })

    async def update_player_state(self, player_id: str, state: dict):
        """更新玩家状态"""
        if player_id in self.players:
            self.players[player_id].update(state)

    async def broadcast(self, message: dict, exclude: Set[str] = None):
        """广播消息给所有玩家"""
        exclude = exclude or set()
        for pid, ws in self.connections.items():
            if pid not in exclude:
                try:
                    await ws.send_json(message)
                except:
                    pass  # 处理断开的连接

    async def sync_loop(self):
        """定期同步所有玩家状态"""
        while True:
            await asyncio.sleep(0.05)  # 20Hz

            # 批量发送所有玩家状态
            for pid, ws in list(self.connections.items()):
                try:
                    batch = []
                    for other_pid, state in self.players.items():
                        if other_pid != pid:
                            batch.append({
                                "type": "player_sync",
                                "player_id": other_pid,
                                **state
                            })
                    if batch:
                        await ws.send_json({"type": "batch", "messages": batch})
                except:
                    pass
```

---

**下一篇 → `08_Economy_System.md`（经济系统设计）**
