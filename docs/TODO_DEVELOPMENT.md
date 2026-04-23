# MindPal 开发任务清单 (TODO)

> 基于 HunyuanWorld 整合计划的详细开发任务
> 更新时间: 2026-01-15

---

## 当前状态概览

```
Phase 1: MVP完善  ← 当前阶段
├── Week 1-2: 后端API开发 ← 当前
├── Week 3-4: 前后端联调

Phase 2: SaaS平台
├── Week 5-6: 语音交互
├── Week 7-9: 知识库RAG
├── Week 10-12: 商业化

Phase 3: HunyuanWorld集成
├── Week 13-14: 环境部署
├── Week 15-16: 场景生成API
├── Week 17-18: 3D前端开发
├── Week 19-20: 数字人小家
```

---

## Phase 1: MVP完善 (Week 1-4)

### 1.1 数字人模块 API (P0) ✅ 完成

```markdown
文件: backend_v2/app/api/v1/digital_humans.py
模型: backend_v2/app/models/digital_human.py
Schema: backend_v2/app/schemas/digital_human.py

[x] 创建数据库模型 DigitalHuman
    - id: int (主键)
    - user_id: int (外键)
    - name: str (数字人名字)
    - avatar_type: str (形象类型)
    - personality: str (性格类型)
    - personality_traits: JSON (特质滑块值)
    - custom_personality: str (自定义描述)
    - voice_id: str (声音ID)
    - domains: List[str] (擅长领域)
    - system_prompt: str (生成的系统提示词)
    - created_at: datetime
    - updated_at: datetime

[x] 创建 Pydantic Schema
    - DigitalHumanCreate (创建请求)
    - DigitalHumanUpdate (更新请求)
    - DigitalHumanResponse (响应)
    - DigitalHumanList (列表响应)

[x] 实现 API 端点
    [x] POST /digital-humans - 创建数字人
    [x] GET /digital-humans - 获取用户的数字人列表
    [x] GET /digital-humans/{id} - 获取数字人详情
    [x] PUT /digital-humans/{id} - 更新数字人
    [x] DELETE /digital-humans/{id} - 删除数字人

[x] 实现性格引擎
    文件: backend_v2/app/services/personality_engine.py
    - generate_system_prompt(config) - 生成System Prompt
    - 6种预设性格模板
    - 特质滑块参数应用
    - 领域专长Prompt
```

### 1.2 对话模块 API (P0)

```markdown
文件: backend_v2/app/api/v1/chat.py
服务: backend_v2/app/services/llm/qwen.py

[ ] 完善 LLM 服务
    文件: backend_v2/app/services/llm/qwen.py
    [ ] 通义千问 SDK 集成
    [ ] generate(prompt, context) - 普通生成
    [ ] generate_stream(prompt, context) - 流式生成
    [ ] 上下文管理 (最近N条历史)
    [ ] Token计数与限制
    [ ] 错误处理与重试

[ ] 实现对话 API
    [ ] POST /chat/send - 发送消息
        请求: {dh_id, message}
        响应: {response, emotion, tokens_used}

    [ ] POST /chat/stream - 流式对话 (SSE)
        请求: {dh_id, message}
        响应: Server-Sent Events

    [ ] GET /chat/history/{dh_id} - 获取对话历史
        参数: limit, offset
        响应: [{role, content, timestamp, emotion}]

    [ ] DELETE /chat/history/{dh_id} - 清空对话历史

[ ] 对话历史存储
    模型: DialogueMessage (已存在)
    [ ] 存储用户消息
    [ ] 存储AI回复
    [ ] 存储情绪分析结果
    [ ] 存储Token消耗
```

### 1.3 用户认证完善 (P0)

```markdown
文件: backend_v2/app/api/v1/auth.py

[ ] 验证码发送 API
    [ ] POST /auth/sms/send - 发送验证码
    [ ] 集成短信服务 (阿里云/腾讯云)
    [ ] 验证码存储 (Redis, 5分钟有效)
    [ ] 频率限制 (60秒间隔)

[ ] 登录/注册 API
    [ ] POST /auth/login - 手机号+验证码登录
    [ ] 新用户自动注册
    [ ] 返回JWT Token

[ ] Token 管理
    [ ] POST /auth/refresh - 刷新Token
    [ ] GET /auth/me - 获取当前用户
```

### 1.4 前后端联调 (P0) ✅ 部分完成

```markdown
[ ] 登录流程
    前端: frontend/index.html
    [ ] 验证码发送按钮对接
    [ ] 登录API对接
    [ ] Token存储到LocalStorage
    [ ] 登录状态检测
    [ ] 自动跳转到列表页

[x] 数字人创建流程
    前端: frontend/create-dh-step1.html ~ step5.html
    [x] Step1: 名字+形象 → 暂存
    [x] Step2: 性格选择 → 暂存
    [x] Step3: 声音选择 → 暂存
    [x] Step4: 领域选择 → 暂存
    [x] Step5: 预览+确认 → 调用创建API (已对接)

[x] 数字人列表
    前端: frontend/dh-list.html
    [x] 加载用户数字人列表 (已对接)
    [x] 卡片渲染 (已对接)
    [x] 点击进入对话 (已对接)

[x] 对话功能
    前端: frontend/chat.html
    [x] 加载数字人信息 (已对接)
    [x] 发送消息API对接 (已对接)
    [x] 响应渲染 (已对接)
    [x] 流式显示支持 (已对接)
    [ ] 历史消息加载 (需后端支持)
```

### 1.5 测试任务 (P1)

```markdown
[ ] 单元测试
    目录: backend_v2/tests/
    [ ] test_auth.py - 认证API测试
    [ ] test_digital_humans.py - 数字人API测试
    [ ] test_chat.py - 对话API测试
    [ ] test_llm_service.py - LLM服务测试

[ ] 集成测试
    [ ] 创建数字人完整流程
    [ ] 对话完整流程
    [ ] 登录→创建→对话E2E

[ ] 性能测试
    [ ] API响应时间 < 500ms
    [ ] LLM首Token延迟 < 1s
    [ ] 并发10用户稳定
```

---

## Phase 2: SaaS平台 (Week 5-12)

### 2.1 语音交互 (Week 5-6)

```markdown
[ ] ASR 集成 (科大讯飞)
    文件: backend_v2/app/services/voice/asr.py
    [ ] 讯飞SDK集成
    [ ] 流式语音识别
    [ ] WebSocket实时传输
    [ ] 方言支持配置

[ ] TTS 集成 (阿里云)
    文件: backend_v2/app/services/voice/tts.py
    [ ] 阿里云TTS SDK
    [ ] 6种预设音色
    [ ] 流式合成
    [ ] 音频格式处理

[ ] 语音 API
    [ ] POST /voice/asr - 语音识别
    [ ] POST /voice/tts - 语音合成
    [ ] WebSocket /voice/stream - 实时语音

[ ] 前端语音UI
    文件: frontend/js/voice-chat.js
    [ ] 按住说话按钮
    [ ] 语音录制
    [ ] 实时波形显示
    [ ] TTS音频播放
```

### 2.2 知识库 RAG (Week 7-9)

```markdown
[ ] 向量数据库部署
    [ ] Qdrant Docker部署
    [ ] 配置连接参数
    [ ] 创建Collection

[ ] 文档处理
    文件: backend_v2/app/services/knowledge/
    [ ] PDF解析 (PyPDF2)
    [ ] DOCX解析 (python-docx)
    [ ] TXT处理
    [ ] 文本分块 (Chunking)

[ ] Embedding服务
    文件: backend_v2/app/services/memory/embedding.py
    [ ] text-embedding-v2 集成
    [ ] 批量向量化
    [ ] 向量存储

[ ] RAG查询引擎
    文件: backend_v2/app/services/knowledge/rag_engine.py
    [ ] 向量检索
    [ ] 相关度评分
    [ ] 上下文组装
    [ ] 答案生成

[ ] 知识库 API
    [ ] POST /knowledge/upload - 上传文档
    [ ] GET /knowledge/list - 文档列表
    [ ] DELETE /knowledge/{id} - 删除文档
    [ ] POST /knowledge/query - RAG查询

[ ] 前端知识库页面
    文件: frontend/knowledge.html
    [ ] 文件上传组件
    [ ] 上传进度显示
    [ ] 文档列表管理
    [ ] 删除确认
```

### 2.3 商业化 (Week 10-12)

```markdown
[ ] 支付系统
    文件: backend_v2/app/services/payment/
    [ ] 微信支付集成
    [ ] 支付宝集成
    [ ] 支付回调处理
    [ ] 订单管理

[ ] 订阅系统
    模型: Subscription, UserQuota
    [ ] 套餐管理API
    [ ] 配额检查中间件
    [ ] 配额消耗记录
    [ ] 配额警告提示

[ ] 前端会员页面
    [ ] pricing.html - 套餐选择
    [ ] subscription.html - 会员中心
    [ ] 支付弹窗
    [ ] 配额显示
```

---

## Phase 3: HunyuanWorld集成 (Week 13-20)

### 3.1 环境部署 (Week 13-14)

```markdown
[ ] GPU服务器准备
    [ ] 云服务器选型 (A100/4090)
    [ ] CUDA 12.x 安装
    [ ] cuDNN 安装
    [ ] Python 3.10+ 环境

[ ] HunyuanWorld部署
    [ ] 克隆仓库
    [ ] 下载模型权重
    [ ] 安装依赖
    [ ] 推理测试验证

[ ] 服务化封装
    文件: hunyuan_world_service/
    [ ] FastAPI服务框架
    [ ] 模型加载管理
    [ ] GPU内存管理
    [ ] 健康检查端点

[ ] Docker容器化
    [ ] Dockerfile编写
    [ ] docker-compose配置
    [ ] GPU透传配置
```

### 3.2 场景生成API (Week 15-16)

```markdown
[ ] HunyuanWorld服务
    文件: backend_v2/app/services/world_generation/
    [ ] hunyuan_service.py
        - generate_scene_from_text()
        - generate_scene_from_image()
        - export_mesh()

[ ] 场景数据模型
    文件: backend_v2/app/models/scene.py
    [ ] Scene模型
        - id, user_id, dh_id
        - prompt, style
        - preview_url, mesh_url
        - status, created_at

[ ] 场景API
    文件: backend_v2/app/api/v1/world.py
    [ ] POST /world/generate/text
    [ ] POST /world/generate/image
    [ ] GET /world/scenes
    [ ] GET /world/scenes/{id}
    [ ] GET /world/export/{id}
    [ ] DELETE /world/scenes/{id}

[ ] 资产存储
    [ ] MinIO部署
    [ ] 上传/下载服务
    [ ] CDN配置
```

### 3.3 3D前端开发 (Week 17-18)

```markdown
[ ] Three.js集成
    文件: frontend/js/3d-viewer.js
    [ ] Three.js库引入
    [ ] WebGLRenderer初始化
    [ ] 场景/相机/灯光

[ ] 模型加载
    [ ] GLTFLoader集成
    [ ] 加载进度显示
    [ ] 错误处理

[ ] 相机控制
    [ ] OrbitControls (轨道)
    [ ] FirstPersonControls (第一人称)
    [ ] 触摸支持

[ ] 交互系统
    [ ] Raycaster物体检测
    [ ] 点击高亮
    [ ] 拖拽移动

[ ] 3D场景页面
    文件: frontend/3d-home.html
    [ ] 3D视口容器
    [ ] 控制面板
    [ ] 对话输入框
```

### 3.4 数字人小家 (Week 19-20)

```markdown
[ ] 自动生成场景
    [ ] 创建数字人时生成
    [ ] 性格→场景描述映射
    [ ] 异步生成任务

[ ] 场景编辑器
    [ ] 主题选择面板
    [ ] 风格调整滑块
    [ ] 重新生成按钮
    [ ] 预览功能

[ ] 沉浸式对话
    [ ] 3D场景中的对话UI
    [ ] 数字人Avatar占位
    [ ] 语音播放位置化

[ ] 性能优化
    [ ] LOD细节层次
    [ ] 纹理压缩
    [ ] 延迟加载
    [ ] 移动端适配
```

---

## 开发规范

### 代码规范

```python
# Python规范
- PEP 8 风格
- Type Hints 类型注解
- Docstring 文档字符串
- 异步优先 (async/await)

# 示例
async def create_digital_human(
    user_id: int,
    config: DigitalHumanCreate,
    db: AsyncSession
) -> DigitalHuman:
    """
    创建数字人

    Args:
        user_id: 用户ID
        config: 创建配置
        db: 数据库会话

    Returns:
        创建的数字人实例
    """
    ...
```

```javascript
// JavaScript规范
- ES6+ 语法
- async/await 异步
- JSDoc 注释
- 模块化组织

// 示例
/**
 * 发送消息到数字人
 * @param {number} dhId - 数字人ID
 * @param {string} message - 消息内容
 * @returns {Promise<Object>} 响应结果
 */
async function sendMessage(dhId, message) {
    ...
}
```

### Git规范

```bash
# 分支命名
feature/xxx   # 新功能
fix/xxx       # 修复
refactor/xxx  # 重构

# Commit格式
feat: 添加数字人创建API
fix: 修复登录Token过期问题
docs: 更新API文档
refactor: 重构LLM服务

# 示例
git checkout -b feature/digital-human-api
git commit -m "feat: 实现数字人CRUD API"
```

### API规范

```yaml
# RESTful设计
GET    /resource      # 列表
POST   /resource      # 创建
GET    /resource/{id} # 详情
PUT    /resource/{id} # 更新
DELETE /resource/{id} # 删除

# 响应格式
{
  "code": 200,
  "message": "success",
  "data": {...}
}

# 错误响应
{
  "code": 400,
  "message": "参数错误",
  "detail": "name字段必填"
}
```

---

## 优先级说明

```
P0 (紧急): 阻塞主流程，必须立即处理
P1 (高):   核心功能，当前Sprint必须完成
P2 (中):   重要功能，计划内完成
P3 (低):   优化项，有空再做
```

---

## 快速开始

### 今日任务 (Day 1)

```bash
# 1. 创建数字人模型
cd backend_v2
# 编辑 app/models/digital_human.py

# 2. 创建数据库迁移
alembic revision --autogenerate -m "add digital_human table"
alembic upgrade head

# 3. 实现基础API
# 编辑 app/api/v1/digital_humans.py

# 4. 测试API
python -m pytest tests/test_digital_humans.py
```

### 本周目标

- [ ] 完成数字人CRUD API
- [ ] 集成通义千问LLM
- [ ] 实现基础对话功能
- [ ] 完成前后端联调

---

*最后更新: 2026-01-15*
