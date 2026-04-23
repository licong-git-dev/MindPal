# MindPal x HunyuanWorld 整合开发计划

> 基于腾讯混元3D世界模型的元宇宙数字人平台开发计划
> 生成时间: 2026-01-15

---

## 一、项目背景与愿景

### 1.1 MindPal 现状

**MindPal** 是一个面向元宇宙的智能体数字人交互平台，当前处于 **Phase 1 MVP验证阶段**：

| 模块 | 完成度 | 状态 |
|-----|--------|-----|
| 前端UI | 95% | 登录/列表/创建/对话/知识库页面完整 |
| 用户认证 | 100% | 手机号验证码登录已实现 |
| 后端框架 | 80% | FastAPI + SQLAlchemy架构完整 |
| 数字人创建 | 70% | 前端完整,后端API待完善 |
| LLM对话 | 50% | 通义千问基础集成 |
| 知识库RAG | 30% | 框架设计完成,实现待开发 |
| 语音交互 | 0% | Phase 2计划 |
| 3D虚拟场景 | 0% | Phase 4计划 |

### 1.2 HunyuanWorld-1.0 核心能力

腾讯混元3D世界模型是业界首个开源的**可沉浸漫游、可交互、可仿真**的世界生成模型：

**三大核心优势**:
1. **360°沉浸体验**: 全景图表征的2D→3D世界生成
2. **工业级兼容性**: 支持导出标准3D网格格式，无缝集成Unity/Unreal
3. **原子级交互**: 物体解耦建模，支持精准物体级交互控制

**技术架构**:
```
第一阶段: 全景世界代理生成
    - 扩散变换器(DiT)框架
    - 文本/图像输入 → 3D全景生成
    - 环形填充 + 渐进混合

第二阶段: 基于语义的世界分层
    - 语义层次化3D场景表征算法
    - 前景/背景分离、地面/天空分离

第三阶段: 分层世界重建
    - 分层3D网格生成
    - 标准格式导出 (OBJ/FBX/GLTF)
```

### 1.3 整合愿景

将HunyuanWorld-1.0的3D世界生成能力与MindPal的数字人交互能力结合，打造：

```
MindPal 2.0 = AI数字人对话 + 3D沉浸式虚拟场景

用户 ←→ 数字人AI对话 ←→ 3D可漫游虚拟世界
         (LLM+RAG)         (HunyuanWorld)
```

**核心价值**:
- 数字人从"聊天框"升级为"虚拟伙伴"
- 对话场景从2D页面升级为3D沉浸空间
- 实现商业计划中的"智能体小家"和"中央社交大厅"

---

## 二、技术整合方案

### 2.1 整合架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        MindPal 2.0 架构                          │
├─────────────────────────────────────────────────────────────────┤
│                         前端层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Web端      │  │  小程序端   │  │  3D客户端(Unity/WebGL)  │  │
│  │  (H5页面)   │  │  (微信)     │  │  HunyuanWorld集成       │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                         API网关层                                │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  FastAPI + CORS + JWT认证 + 限流                            ││
│  └─────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────┤
│                         服务层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  对话服务   │  │  世界生成   │  │  用户服务               │  │
│  │  - LLM推理  │  │  - 场景生成 │  │  - 认证/订阅/配额       │  │
│  │  - RAG检索  │  │  - 3D导出   │  │                         │  │
│  │  - 情感分析 │  │  - 物体交互 │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  语音服务   │  │  数字人服务 │  │  支付服务               │  │
│  │  - ASR识别  │  │  - 性格引擎 │  │  - 微信/支付宝          │  │
│  │  - TTS合成  │  │  - 记忆系统 │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                         AI引擎层                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ 通义千问    │  │ HunyuanWorld│  │ Embedding模型           │  │
│  │ qwen-turbo  │  │ DiT框架     │  │ text-embedding-v2       │  │
│  │ qwen-plus   │  │ 3D生成      │  │ 向量检索                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                         数据层                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ PostgreSQL  │  │ Redis       │  │ Qdrant/Milvus           │  │
│  │ 用户/对话   │  │ 缓存/会话   │  │ 向量存储                │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │  MinIO/OSS - 3D资产存储 (场景/模型/纹理)                    ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 HunyuanWorld 集成方案

#### 方案一：API服务化（推荐）

将HunyuanWorld部署为独立的3D生成服务：

```python
# backend_v2/app/services/world_generation/hunyuan_service.py

from typing import Optional
import httpx

class HunyuanWorldService:
    """HunyuanWorld 3D世界生成服务"""

    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    async def generate_scene_from_text(
        self,
        prompt: str,
        style: str = "realistic",
        resolution: str = "1024x1024"
    ) -> dict:
        """从文本描述生成3D场景"""
        response = await self.client.post(
            f"{self.base_url}/api/v1/generate/text2world",
            json={
                "prompt": prompt,
                "style": style,
                "resolution": resolution,
                "output_format": "glb"  # Unity兼容格式
            }
        )
        return response.json()

    async def generate_scene_from_image(
        self,
        image_path: str,
        depth_estimation: bool = True
    ) -> dict:
        """从单张图片生成3D场景"""
        with open(image_path, 'rb') as f:
            files = {'image': f}
            response = await self.client.post(
                f"{self.base_url}/api/v1/generate/image2world",
                files=files,
                data={"depth_estimation": depth_estimation}
            )
        return response.json()

    async def export_mesh(
        self,
        scene_id: str,
        format: str = "glb"  # glb/obj/fbx
    ) -> bytes:
        """导出3D网格文件"""
        response = await self.client.get(
            f"{self.base_url}/api/v1/export/{scene_id}",
            params={"format": format}
        )
        return response.content
```

#### 方案二：本地集成

直接调用HunyuanWorld的Python API：

```python
# backend_v2/app/services/world_generation/local_hunyuan.py

import sys
sys.path.append('/path/to/HunyuanWorld-1.0')

from hunyuan_world import WorldGenerator, SceneConfig

class LocalHunyuanService:
    """本地HunyuanWorld服务"""

    def __init__(self):
        self.generator = WorldGenerator(
            model_path="checkpoints/hunyuan_world_v1.0.pth",
            device="cuda"
        )

    def generate_panorama(self, prompt: str) -> bytes:
        """生成全景图"""
        config = SceneConfig(
            prompt=prompt,
            resolution=1024,
            steps=50,
            guidance_scale=7.5
        )
        panorama = self.generator.generate_panorama(config)
        return panorama

    def panorama_to_mesh(self, panorama: bytes) -> str:
        """全景图转3D网格"""
        mesh_path = self.generator.reconstruct_3d(
            panorama,
            semantic_layering=True,
            export_format="glb"
        )
        return mesh_path
```

### 2.3 3D场景应用场景

#### 场景一：数字人小家

用户创建数字人时，同时生成专属的3D虚拟空间：

```python
# 用户创建数字人流程
async def create_digital_human_with_home(
    user_id: int,
    dh_config: DigitalHumanConfig
) -> DigitalHuman:
    # 1. 创建数字人基础信息
    dh = await create_digital_human(user_id, dh_config)

    # 2. 基于数字人性格生成专属场景描述
    scene_prompt = generate_scene_prompt(dh_config)
    # 例如：温柔型 → "温馨舒适的现代简约客厅，暖色调灯光，柔软的沙发"
    # 活泼型 → "色彩明亮的创意工作室，充满艺术气息，阳光充足"

    # 3. 调用HunyuanWorld生成3D场景
    scene_result = await hunyuan_service.generate_scene_from_text(
        prompt=scene_prompt,
        style="realistic"
    )

    # 4. 存储场景资产
    dh.home_scene_id = scene_result['scene_id']
    dh.home_scene_url = scene_result['mesh_url']

    return dh
```

#### 场景二：沉浸式对话

在3D场景中与数字人进行对话：

```
用户进入3D小家
    ↓
数字人Avatar在场景中迎接
    ↓
用户语音/文字输入
    ↓
[ASR] 语音转文字
    ↓
[LLM] 生成回复 + 情绪分析
    ↓
[TTS] 文字转语音
    ↓
数字人Avatar播放语音 + 表情动画
    ↓
场景环境响应（灯光/物品交互）
```

#### 场景三：主题场景生成

基于对话内容动态生成场景：

```python
async def generate_contextual_scene(
    conversation: str,
    user_id: int,
    dh_id: int
) -> str:
    """基于对话内容生成主题场景"""

    # 1. 分析对话主题
    theme = await analyze_conversation_theme(conversation)
    # 例如：讨论旅行 → "海边度假村"
    #      讨论学习 → "安静的图书馆"
    #      讨论美食 → "温馨的咖啡厅"

    # 2. 生成场景描述
    scene_prompt = f"高品质3D场景：{theme}，适合两人交流的私密空间"

    # 3. 生成3D场景
    scene = await hunyuan_service.generate_scene_from_text(scene_prompt)

    return scene['mesh_url']
```

---

## 三、开发阶段规划

### 3.1 开发阶段总览

```
Phase 1: MVP完善 (4周) - 当前阶段
    └── 完成核心对话功能 + 基础商业化

Phase 2: SaaS平台 (8周)
    └── 语音交互 + RAG知识库 + 支付系统

Phase 3: HunyuanWorld集成 (8周) ★ 新增
    └── 3D场景生成 + WebGL渲染 + 数字人小家

Phase 4: PaaS开放 (12周)
    └── 开放API + SDK + 开发者生态

Phase 5: 元宇宙布局 (长期)
    └── VR支持 + 中央社交大厅 + 跨平台互通
```

### 3.2 Phase 1: MVP完善 (当前 → Week 4)

**目标**: 完成核心对话功能，实现可用的MVP产品

#### Week 1-2: 后端API完善

| 任务 | 优先级 | 状态 |
|------|--------|-----|
| 完善数字人CRUD API | P0 | 待开发 |
| 集成通义千问LLM对话 | P0 | 进行中 |
| 实现对话历史存储 | P0 | 待开发 |
| 性格引擎Prompt工程 | P0 | 待开发 |

```bash
# 核心文件
backend_v2/app/api/v1/digital_humans.py  # 数字人API
backend_v2/app/api/v1/chat.py            # 对话API
backend_v2/app/services/llm/qwen.py      # LLM服务
backend_v2/app/services/personality.py   # 性格引擎
```

#### Week 3-4: 前后端联调 + 测试

| 任务 | 优先级 | 状态 |
|------|--------|-----|
| 创建数字人流程联调 | P0 | 待开发 |
| 对话功能联调 | P0 | 待开发 |
| 知识库上传联调 | P1 | 待开发 |
| Bug修复与优化 | P0 | 待开发 |

### 3.3 Phase 2: SaaS平台 (Week 5-12)

**目标**: 打造完整的个人数字人SaaS产品

#### Week 5-6: 语音交互

| 任务 | 说明 |
|------|------|
| 集成科大讯飞ASR | 支持202种方言 |
| 集成阿里云TTS | 6种预设音色 |
| 前端语音UI | 按住说话、波形显示 |
| WebSocket流式处理 | 实时语音转文字 |

#### Week 7-9: 知识库RAG

| 任务 | 说明 |
|------|------|
| 部署Qdrant向量数据库 | Docker容器化 |
| 文档处理Pipeline | PDF/DOCX/TXT解析 |
| Embedding向量化 | text-embedding-v2 |
| RAG查询引擎 | 向量检索+重排序 |

#### Week 10-12: 商业化

| 任务 | 说明 |
|------|------|
| 支付系统集成 | 微信/支付宝 |
| 订阅系统完善 | 免费/高级/专业 |
| 配额管理 | 按量计费 |

### 3.4 Phase 3: HunyuanWorld集成 (Week 13-20) ★

**目标**: 将3D世界生成能力集成到MindPal

#### Week 13-14: 环境搭建

| 任务 | 说明 |
|------|------|
| HunyuanWorld模型部署 | GPU服务器(A100/4090) |
| 模型服务化封装 | FastAPI包装 |
| 3D资产存储方案 | MinIO对象存储 |

**硬件要求**:
```
GPU: NVIDIA A100 40GB 或 RTX 4090 24GB
CPU: 8核以上
内存: 64GB+
存储: 500GB+ SSD
```

#### Week 15-16: 场景生成API

| 任务 | 说明 |
|------|------|
| 文本生成场景API | text2world |
| 图片生成场景API | image2world |
| 场景导出API | GLB/OBJ格式 |
| 场景管理API | CRUD操作 |

```python
# 新增API端点
POST   /api/v1/world/generate/text      # 文本生成场景
POST   /api/v1/world/generate/image     # 图片生成场景
GET    /api/v1/world/scenes/{scene_id}  # 获取场景信息
GET    /api/v1/world/export/{scene_id}  # 导出场景文件
DELETE /api/v1/world/scenes/{scene_id}  # 删除场景
```

#### Week 17-18: 3D前端开发

| 任务 | 说明 |
|------|------|
| Three.js/Babylon.js集成 | WebGL 3D渲染 |
| 场景加载器 | GLB模型加载 |
| 相机控制 | 第一人称漫游 |
| 交互系统 | 物体点击/拖拽 |

```javascript
// frontend/js/3d-viewer.js
class MindPal3DViewer {
    constructor(container) {
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(75, ...);
        this.renderer = new THREE.WebGLRenderer();
        this.controls = new THREE.OrbitControls(...);
    }

    async loadScene(sceneUrl) {
        const loader = new THREE.GLTFLoader();
        const gltf = await loader.loadAsync(sceneUrl);
        this.scene.add(gltf.scene);
    }

    enableFirstPersonControls() {
        // 第一人称漫游模式
    }
}
```

#### Week 19-20: 数字人小家

| 任务 | 说明 |
|------|------|
| 创建数字人时生成小家 | 自动场景生成 |
| 小家定制编辑器 | 风格/主题选择 |
| 数字人Avatar渲染 | 2D→3D升级 |
| 沉浸式对话体验 | 3D场景中对话 |

### 3.5 Phase 4-5: PaaS + 元宇宙

详见 [`../roadmap/DEVELOPMENT_ROADMAP.md`](../roadmap/DEVELOPMENT_ROADMAP.md)

---

## 四、详细任务清单 (TODO List)

### 4.1 Phase 1 任务列表

```
[ ] 1. 后端API开发
    [ ] 1.1 数字人模块
        [ ] POST /api/v1/digital-humans - 创建数字人
        [ ] GET /api/v1/digital-humans - 获取列表
        [ ] GET /api/v1/digital-humans/{id} - 获取详情
        [ ] PUT /api/v1/digital-humans/{id} - 更新数字人
        [ ] DELETE /api/v1/digital-humans/{id} - 删除数字人

    [ ] 1.2 对话模块
        [ ] POST /api/v1/chat/send - 发送消息
        [ ] POST /api/v1/chat/stream - 流式对话
        [ ] GET /api/v1/chat/history/{dh_id} - 获取历史
        [ ] DELETE /api/v1/chat/history/{dh_id} - 清空历史

    [ ] 1.3 LLM服务
        [ ] 通义千问SDK集成
        [ ] System Prompt模板管理
        [ ] 性格引擎实现
        [ ] 对话上下文管理
        [ ] Token计数与限制

[ ] 2. 前后端联调
    [ ] 2.1 登录流程
        [ ] 验证码发送API对接
        [ ] 登录/注册API对接
        [ ] Token持久化

    [ ] 2.2 数字人流程
        [ ] 创建流程5步API对接
        [ ] 列表页API对接
        [ ] 详情页API对接

    [ ] 2.3 对话流程
        [ ] 消息发送API对接
        [ ] 历史消息加载
        [ ] 流式响应显示

[ ] 3. 测试与优化
    [ ] 3.1 功能测试
        [ ] 创建数字人E2E测试
        [ ] 对话功能E2E测试
        [ ] 登录流程测试

    [ ] 3.2 性能优化
        [ ] API响应时间<500ms
        [ ] LLM首Token延迟<1s
        [ ] 前端加载时间<3s
```

### 4.2 Phase 3 任务列表 (HunyuanWorld)

```
[ ] 1. HunyuanWorld部署
    [ ] 1.1 环境准备
        [ ] GPU服务器采购/租用
        [ ] CUDA/cuDNN环境配置
        [ ] Python环境 (3.10+)
        [ ] PyTorch 2.0+ 安装

    [ ] 1.2 模型部署
        [ ] 克隆HunyuanWorld仓库
        [ ] 下载模型权重 (HuggingFace)
        [ ] 依赖安装
        [ ] 推理测试

    [ ] 1.3 服务化
        [ ] FastAPI封装
        [ ] API文档编写
        [ ] Docker容器化
        [ ] 健康检查端点

[ ] 2. 后端集成
    [ ] 2.1 世界生成服务
        [ ] HunyuanWorldService类实现
        [ ] 文本生成场景方法
        [ ] 图片生成场景方法
        [ ] 场景导出方法

    [ ] 2.2 场景管理
        [ ] Scene数据库模型
        [ ] 场景CRUD API
        [ ] 场景资产存储 (MinIO)
        [ ] 用户场景关联

    [ ] 2.3 数字人小家
        [ ] 创建数字人时自动生成场景
        [ ] 场景风格与性格关联
        [ ] 场景定制选项

[ ] 3. 前端开发
    [ ] 3.1 3D渲染引擎
        [ ] Three.js集成
        [ ] GLB模型加载器
        [ ] 场景渲染管线
        [ ] 光照系统

    [ ] 3.2 交互系统
        [ ] 相机控制 (轨道/第一人称)
        [ ] 物体交互 (点击/拖拽)
        [ ] 触摸支持 (移动端)

    [ ] 3.3 沉浸式对话
        [ ] 3D场景中的对话UI
        [ ] 数字人Avatar显示
        [ ] 语音与场景联动

    [ ] 3.4 场景编辑器
        [ ] 主题选择面板
        [ ] 风格调整滑块
        [ ] 预览功能
        [ ] 保存/重置

[ ] 4. 性能优化
    [ ] 4.1 模型优化
        [ ] 模型压缩 (LOD)
        [ ] 纹理压缩
        [ ] 延迟加载

    [ ] 4.2 渲染优化
        [ ] GPU Instancing
        [ ] Occlusion Culling
        [ ] 移动端适配
```

---

## 五、技术规格

### 5.1 硬件要求

#### 开发环境
```
CPU: Intel i7 / AMD Ryzen 7 以上
内存: 32GB
GPU: NVIDIA RTX 3060 以上 (本地调试HunyuanWorld)
存储: 500GB SSD
```

#### 生产环境
```
应用服务器:
- CPU: 8核+
- 内存: 32GB+
- 存储: 200GB SSD

GPU推理服务器:
- CPU: 16核+
- 内存: 64GB+
- GPU: NVIDIA A100 40GB 或 RTX 4090 24GB
- 存储: 1TB SSD

数据库服务器:
- CPU: 8核+
- 内存: 64GB+
- 存储: 500GB SSD
```

### 5.2 软件依赖

#### 后端依赖 (新增)
```python
# requirements.txt 新增
# HunyuanWorld相关
torch>=2.0.0
torchvision>=0.15.0
diffusers>=0.25.0
transformers>=4.36.0
accelerate>=0.25.0
xformers>=0.0.23

# 3D处理
trimesh>=4.0.0
pygltflib>=1.16.0
open3d>=0.18.0

# 对象存储
minio>=7.2.0
```

#### 前端依赖 (新增)
```javascript
// package.json 新增
{
  "dependencies": {
    "three": "^0.160.0",
    "@types/three": "^0.160.0",
    "three-stdlib": "^2.28.0"
  }
}
```

### 5.3 API设计

#### 世界生成API

```yaml
# POST /api/v1/world/generate/text
Request:
  prompt: string          # 场景描述
  style: string           # realistic/cartoon/fantasy
  resolution: string      # 512/1024/2048

Response:
  scene_id: string        # 场景ID
  preview_url: string     # 预览图URL
  mesh_url: string        # 3D模型URL
  generation_time: float  # 生成耗时(秒)
```

```yaml
# POST /api/v1/world/generate/image
Request:
  image: file             # 输入图片
  depth_estimation: bool  # 是否估计深度

Response:
  scene_id: string
  preview_url: string
  mesh_url: string
  depth_map_url: string
```

```yaml
# GET /api/v1/world/export/{scene_id}
Query:
  format: string          # glb/obj/fbx

Response:
  file: binary            # 3D模型文件
```

---

## 六、风险与应对

### 6.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|-----|------|-----|---------|
| HunyuanWorld推理慢 | 用户体验差 | 中 | 预生成+缓存,异步处理 |
| GPU资源不足 | 无法部署 | 中 | 云GPU租用,按需扩容 |
| 3D模型过大 | 加载慢 | 高 | LOD压缩,渐进加载 |
| WebGL兼容性 | 部分设备不支持 | 低 | 优雅降级,提供2D备选 |

### 6.2 成本风险

| 项目 | 预估成本 | 说明 |
|-----|---------|------|
| GPU服务器(A100) | ¥15-20/小时 | 云租用 |
| 对象存储 | ¥0.12/GB/月 | 3D资产存储 |
| CDN流量 | ¥0.36/GB | 3D模型分发 |

**成本优化策略**:
1. 使用预生成+缓存减少实时推理
2. 压缩3D模型减少存储和带宽
3. 按用户等级分配资源

---

## 七、里程碑与验收

### 7.1 里程碑计划

| 里程碑 | 时间 | 交付物 |
|-------|------|--------|
| M1: MVP完善 | Week 4 | 可用的对话产品 |
| M2: 语音上线 | Week 6 | 语音交互功能 |
| M3: RAG上线 | Week 9 | 知识库问答功能 |
| M4: 支付上线 | Week 12 | 商业化闭环 |
| M5: 3D场景MVP | Week 16 | 基础场景生成 |
| M6: 数字人小家 | Week 20 | 沉浸式体验 |

### 7.2 验收标准

#### M1: MVP完善
- [ ] 100%用户可完成创建数字人
- [ ] 对话响应时间<3s
- [ ] 次日留存率≥30%

#### M5: 3D场景MVP
- [ ] 场景生成时间<60s
- [ ] 3D场景可在5种主流设备流畅运行
- [ ] 用户满意度≥4.0/5.0

#### M6: 数字人小家
- [ ] 每个数字人自动生成专属小家
- [ ] 支持第一人称漫游
- [ ] 3D场景内可进行对话

---

## 八、团队与分工

### 8.1 Phase 1-2 团队

| 角色 | 人数 | 主要职责 |
|-----|------|---------|
| 后端开发 | 1-2 | API开发,LLM集成 |
| 前端开发 | 1 | UI开发,联调 |
| 产品经理 | 0.5 | 需求管理 |

### 8.2 Phase 3 团队 (新增)

| 角色 | 人数 | 主要职责 |
|-----|------|---------|
| AI工程师 | 1 | HunyuanWorld部署,优化 |
| 3D开发 | 1 | Three.js,场景渲染 |
| 后端开发 | 1 | 服务集成,API开发 |

---

## 附录

### A. 参考资源

- [HunyuanWorld-1.0 GitHub](https://github.com/Tencent-Hunyuan/HunyuanWorld-1.0)
- [HunyuanWorld 官方文档](https://3d-models.hunyuan.tencent.com/world/)
- [Three.js 官方文档](https://threejs.org/docs/)
- [MindPal PRD文档](../PRD.md)
- [MindPal 开发路线图](../roadmap/DEVELOPMENT_ROADMAP.md)

### B. 术语表

| 术语 | 说明 |
|-----|------|
| DiT | Diffusion Transformer,扩散变换器 |
| GLB | GL Transmission Format Binary,3D模型格式 |
| LOD | Level of Detail,细节层次 |
| RAG | Retrieval-Augmented Generation,检索增强生成 |
| WebGL | Web Graphics Library,Web 3D图形API |

---

*文档版本: 1.0*
*最后更新: 2026-01-15*
*作者: MindPal AI开发团队*
