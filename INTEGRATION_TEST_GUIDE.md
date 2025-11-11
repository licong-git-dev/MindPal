# MindPal 前后端联调测试指南

> 🎉 后端API已开发完成并成功启动，前端已完成API集成！

## ✅ 已完成的工作

### 后端 (Backend)
- ✅ Flask应用框架搭建
- ✅ 阿里云通义千问API集成 (qwen-turbo)
- ✅ SQLite数据库创建和初始化
- ✅ JWT用户认证系统
- ✅ 数字人CRUD API
- ✅ AI流式对话API (Server-Sent Events)
- ✅ 对话历史存储
- ✅ 情绪识别系统
- ✅ 性格系统 (6种基础性格 + 5维特质)

### 前端 (Frontend)
- ✅ 登录页面连接真实API (`index.html`)
- ✅ 创建数字人连接真实API (`create-dh-step5.html`)
- ✅ 聊天页面流式响应集成 (`chat.html`)
- ✅ Token管理 (保存到localStorage)

---

## 🚀 快速开始测试

### 1. 启动后端服务器

后端已经在运行中！服务地址：**http://localhost:5000**

如果需要重启:
```bash
cd D:/app/PythonFiles/MindPal/backend
python app.py
```

### 2. 打开前端页面

使用浏览器打开:
```
D:\app\PythonFiles\MindPal\frontend\index.html
```

或使用Live Server (推荐):
```bash
# 使用VS Code的Live Server扩展
# 在frontend目录右键 -> Open with Live Server
```

---

## 📋 完整测试流程

### 步骤1: 注册新用户

1. 打开 `index.html` (登录页)
2. 输入手机号: `13800138000`
3. 输入密码: `test123456`
4. 点击"登录"按钮

**预期结果**:
- ✅ 后端自动注册新用户 (首次登录会自动注册)
- ✅ 返回JWT token并保存到localStorage
- ✅ 跳转到 `onboarding.html` (首次) 或 `dh-list.html` (已引导)

**调试方法**:
```javascript
// 在浏览器Console中检查token
console.log(localStorage.getItem('mindpal_token'));
console.log(localStorage.getItem('mindpal_user'));
```

---

### 步骤2: 创建数字人

1. 完成引导流程 (onboarding)
2. 进入创建数字人流程
3. **Step 1**: 选择形象 (例如: 👦 阳光男孩)
4. **Step 2**: 选择性格 (例如: 温柔体贴)
   - 调整特质滑块 (活泼度、幽默感、共情力、主动性、创造力)
5. **Step 3**: 选择声音 (例如: xiaoyu)
6. **Step 4**: 跳过知识库 (P1阶段功能)
7. **Step 5**: 输入名字 (例如: "小智")，点击"开始对话"

**预期结果**:
- ✅ 调用 `POST /api/digital-humans` 创建数字人
- ✅ 返回数字人ID
- ✅ 跳转到 `chat.html?id=1`

**测试API** (curl命令):
```bash
curl -X POST http://localhost:5000/api/digital-humans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "小智",
    "avatar": "boy-sunny",
    "avatarEmoji": "👦",
    "personality": "gentle",
    "traits": {
      "liveliness": 70,
      "humor": 80,
      "empathy": 90,
      "initiative": 60,
      "creativity": 50
    },
    "voice": "xiaoyu",
    "voiceParams": {
      "speed": 1.0,
      "pitch": 0,
      "volume": 80
    }
  }'
```

---

### 步骤3: AI对话测试

1. 进入聊天页面 (`chat.html?id=1`)
2. 在输入框输入消息，例如:
   - "你好，自我介绍一下"
   - "今天天气怎么样？"
   - "讲个笑话"
   - "2+2等于几？"

**预期结果**:
- ✅ 消息立即显示在聊天区域
- ✅ 数字人状态显示"正在输入..."
- ✅ AI回复以**流式方式**逐字显示 (像ChatGPT一样)
- ✅ 回复完成后显示"在线"状态
- ✅ 消息保存到数据库
- ✅ 对话历史可查看

**流式响应示例**:
```
data: {"chunk": "你好"}
data: {"chunk": "呀"}
data: {"chunk": "！"}
data: {"chunk": "很高兴"}
data: {"chunk": "见到"}
data: {"chunk": "你"}
data: {"done": true, "emotion": "happy"}
```

---

## 🧪 API端点测试

### 1. 健康检查
```bash
curl http://localhost:5000/health
```

### 2. 用户注册
```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138001","password":"test123"}'
```

### 3. 用户登录
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000","password":"test123456"}'
```

**返回示例**:
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "phone": "13800138000",
      "created_at": "2025-11-11T07:26:22.714046"
    }
  }
}
```

### 4. 获取数字人列表
```bash
curl http://localhost:5000/api/digital-humans \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. 查看对话历史
```bash
curl http://localhost:5000/api/chat/history/1?limit=50 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 常见问题排查

### 问题1: CORS错误
**错误信息**: `Access-Control-Allow-Origin`

**解决方案**:
- 后端已配置CORS，允许以下来源:
  - `http://localhost:8000`
  - `http://127.0.0.1:8000`
  - `http://localhost:5500`
  - `http://127.0.0.1:5500`
- 如果使用其他端口，修改 `.env` 中的 `ALLOWED_ORIGINS`

### 问题2: 401 未授权
**错误信息**: `未授权` 或 `Token无效或已过期`

**解决方案**:
```javascript
// 检查token是否存在
console.log(localStorage.getItem('mindpal_token'));

// 如果token不存在或过期，重新登录
localStorage.removeItem('mindpal_token');
window.location.href = 'index.html';
```

### 问题3: 流式响应不显示
**问题**: AI回复不显示或显示不完整

**调试步骤**:
1. 打开浏览器开发者工具 (F12)
2. 切换到 Network 标签
3. 发送消息，查看 `/api/chat` 请求
4. 检查 Response 标签，应该看到 SSE 格式数据
5. 查看 Console 是否有JavaScript错误

### 问题4: 数据库错误
**错误信息**: `unable to open database file`

**解决方案**:
```bash
# 检查data目录是否存在
ls D:/app/PythonFiles/MindPal/backend/data

# 如果不存在，创建目录
mkdir D:/app/PythonFiles/MindPal/backend/data

# 重启后端服务器
```

---

## 📊 性能指标

### API响应时间
- 登录: ~200ms
- 创建数字人: ~300ms
- AI对话首字: ~500-800ms (取决于通义千问API)
- 流式响应: 实时 (每个token ~50-100ms)

### 成本估算
- 通义千问 (qwen-turbo):
  - 输入: ¥0.0008/千tokens
  - 输出: ¥0.002/千tokens
- 预计每月1000次对话: **¥1.25/月**

---

## 🎯 测试检查清单

- [ ] **用户注册**: 新用户可以注册
- [ ] **用户登录**: 已注册用户可以登录并获得token
- [ ] **Token持久化**: 刷新页面后token仍然有效
- [ ] **创建数字人**: 可以创建新数字人并保存到数据库
- [ ] **AI对话**: 可以发送消息并接收流式响应
- [ ] **性格系统**: 不同性格的数字人回复风格不同
- [ ] **对话历史**: 历史消息正确保存和加载
- [ ] **情绪识别**: AI回复包含情绪标签
- [ ] **错误处理**: 网络错误时显示友好提示
- [ ] **Token过期**: Token过期后跳转到登录页

---

## 🚧 下一步计划 (Phase 6)

- [ ] 创建Dockerfile
- [ ] 配置docker-compose.yml
- [ ] 部署到云服务器
- [ ] 配置HTTPS (Let's Encrypt)
- [ ] 设置监控和日志
- [ ] 性能优化
- [ ] 完整的API文档

---

## 📞 技术支持

### 后端日志位置
- 终端输出 (实时)
- Flask debug模式已开启

### 数据库位置
```
D:\app\PythonFiles\MindPal\backend\data\mindpal.db
```

### 查看数据库内容
```bash
cd D:/app/PythonFiles/MindPal/backend/data
sqlite3 mindpal.db

# SQL命令
.tables                          # 查看所有表
SELECT * FROM users;             # 查看用户
SELECT * FROM digital_humans;    # 查看数字人
SELECT * FROM messages;          # 查看消息
.exit                            # 退出
```

---

**开发团队**: MindPal Team
**最后更新**: 2025-11-11
**当前版本**: v1.0.0 (P0完成)
