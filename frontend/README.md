# MindPal 前端项目

> 你的数字灵魂伴侣 - 基于原生Web技术的AI数字人对话平台

## 📋 项目概述

MindPal 是一个创新的数字人交互平台，提供情感陪伴、知识服务和智能对话功能。本项目采用原生HTML/CSS/JavaScript开发，无需框架依赖，轻量快速。

## ✨ 核心特性

### 🎨 视觉设计
- **玻璃拟态设计语言** - 现代感的毛玻璃效果
- **渐变紫蓝主题** - #6366F1 → #8B5CF6
- **流畅动画** - 呼吸、眨眼、打字机、淡入淡出等30+动画
- **响应式布局** - 完美适配桌面端和移动端

### 🧠 核心功能
- **5步数字人创建流程** - 形象、性格、声音、知识库、确认
- **智能对话界面** - 60vh数字人展示 + 对话区域
- **情绪识别显示** - 实时展示数字人情绪状态
- **语音交互** - 支持语音输入和输出（UI完成）
- **知识库管理** - 文档上传、URL导入
- **数据持久化** - LocalStorage本地存储

## 📁 项目结构

```
frontend/
├── index.html                    # 登录页
├── onboarding.html              # 新用户引导页
├── create-dh-step1.html         # 创建数字人-步骤1（选择形象）
├── create-dh-step2.html         # 创建数字人-步骤2（设置性格）
├── create-dh-step3.html         # 创建数字人-步骤3（选择声音）
├── create-dh-step4.html         # 创建数字人-步骤4（设置知识库）
├── create-dh-step5.html         # 创建数字人-步骤5（确认创建）
├── dh-list.html                 # 数字人列表页
├── chat.html                    # 主对话页（灵魂页面）
├── knowledge.html               # 知识库管理页（待开发）
├── profile.html                 # 个人中心（待开发）
├── subscription.html            # 会员订阅页（待开发）
├── css/
│   ├── variables.css            # 设计Token（颜色、间距、字体等）
│   ├── base.css                 # CSS重置和基础样式
│   ├── components.css           # 可复用UI组件
│   └── animations.css           # 动画效果库
├── js/
│   ├── app.js                   # 应用初始化（待开发）
│   ├── chat.js                  # 对话功能模块（待开发）
│   └── utils.js                 # 工具函数（待开发）
└── assets/
    └── avatars/                 # 数字人头像资源
```

## 🚀 快速开始

### 1. 直接打开
无需构建，直接用浏览器打开 `index.html` 即可使用。

```bash
# 方法1：直接双击 index.html

# 方法2：使用本地服务器（推荐）
cd frontend
python -m http.server 8000
# 访问 http://localhost:8000

# 方法3：使用 VS Code Live Server
# 右键 index.html -> Open with Live Server
```

### 2. 测试流程

1. **登录页** (`index.html`)
   - 输入手机号和密码登录
   - 或点击"立即注册"进入引导流程

2. **新用户引导** (`onboarding.html`)
   - 4步引导：欢迎 → 使用场景 → 数字人类型 → 个性化设置
   - 完成后自动创建首个数字人

3. **创建数字人** (`create-dh-step1.html` 到 `step5.html`)
   - 步骤1：选择形象（8种预设+自定义上传）
   - 步骤2：设置性格（6种类型+5维特质调节）
   - 步骤3：选择声音（6种音色+参数调节）
   - 步骤4：设置知识库（文档上传+URL导入，可跳过）
   - 步骤5：命名并确认创建

4. **数字人列表** (`dh-list.html`)
   - 查看所有已创建的数字人
   - 点击卡片进入对话
   - 创建新数字人

5. **主对话页** (`chat.html`)
   - 60vh数字人展示区（呼吸动画）
   - 对话消息列表
   - 文字/语音输入
   - 情绪状态显示

## 🎨 设计规范

### 颜色系统
```css
/* 主色调 - 渐变紫蓝 */
--color-primary-1: #6366F1;
--color-primary-2: #8B5CF6;
--gradient-primary: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);

/* 辅助色彩 */
--color-secondary-pink: #F472B6;
--color-secondary-blue: #60A5FA;
--color-secondary-green: #34D399;

/* 中性色 - 深色模式 */
--color-bg-dark: #0F172A;
--color-bg-card: rgba(30, 41, 59, 0.7);
--color-text-primary: #F1F5F9;
```

### 间距系统（8px网格）
```css
--spacing-xs: 4px;
--spacing-sm: 8px;
--spacing-md: 16px;
--spacing-lg: 24px;
--spacing-xl: 32px;
--spacing-2xl: 48px;
```

### 圆角系统
```css
--radius-sm: 4px;
--radius-md: 8px;
--radius-lg: 12px;
--radius-xl: 16px;
--radius-2xl: 24px;
--radius-full: 9999px;
```

## 💾 数据存储

### LocalStorage 键名规范
```javascript
// 用户数据
'mindpal_user'              // 用户登录信息
'mindpal_remember'          // 记住登录
'mindpal_onboarded'         // 是否完成引导

// 数字人数据
'mindpal_digital_humans'    // 数字人列表
'mindpal_dh_drafts'         // 数字人草稿

// 对话数据
'mindpal_messages_{dhId}'   // 特定数字人的对话记录

// 引导数据
'mindpal_onboarding_data'   // 新用户引导数据
```

### SessionStorage 键名规范
```javascript
// 创建流程临时数据
'create_dh_data'            // 创建数字人的临时数据
```

## 🔧 开发指南

### 添加新组件
1. 在 `css/components.css` 中定义组件样式
2. 遵循BEM命名规范
3. 使用CSS变量确保一致性

### 添加新动画
1. 在 `css/animations.css` 中定义@keyframes
2. 使用CSS变量控制动画时长
3. 为动画添加工具类（如 `.fade-in`）

### 添加新页面
1. 复制已有页面模板
2. 引入必要的CSS文件
3. 添加底部导航（如需要）
4. 实现页面特定的JavaScript逻辑

## 🎯 待开发功能

### 高优先级（P0）
- [ ] 后端API集成
- [ ] 实际的AI对话功能
- [ ] 语音识别和合成
- [ ] 知识库向量检索

### 中优先级（P1）
- [ ] knowledge.html - 知识库管理页完整实现
- [ ] profile.html - 个人中心页
- [ ] subscription.html - 会员订阅页
- [ ] 数字人编辑功能
- [ ] 对话历史导出
- [ ] 多语言支持

### 低优先级（P2）
- [ ] 3D数字人模型
- [ ] 更多动画效果
- [ ] 主题切换（浅色模式）
- [ ] PWA支持
- [ ] 离线功能

## 📱 浏览器兼容性

- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ⚠️ IE 不支持

## 🔒 安全注意事项

1. **生产环境部署前必须**：
   - 添加HTTPS支持
   - 实现真实的后端API
   - 添加CSRF保护
   - 实现真实的用户认证
   - 添加输入验证和过滤
   - 敏感数据加密存储

2. **当前限制**：
   - 数据存储在LocalStorage（易被清除）
   - 无用户认证（模拟登录）
   - 无数据加密
   - 仅适用于开发和演示

## 📖 相关文档

- [PRD产品需求文档](../PRD.md)
- [DESIGN_SPEC设计规范](../docs/product/DESIGN_SPEC.md)
- [后端API文档](../backend/README.md)（待创建）

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 开源协议

MIT License - 详见 [LICENSE](../LICENSE) 文件

## 👥 团队

- **产品经理** - 需求分析和PRD编写
- **UI/UX设计师** - 视觉设计和交互设计
- **前端工程师** - 前端代码实现
- **AI工程师** - AI对话引擎（待开发）
- **后端工程师** - API接口（待开发）

## 📞 联系方式

- 项目地址：https://github.com/yourusername/mindpal
- 问题反馈：https://github.com/yourusername/mindpal/issues
- 邮箱：support@mindpal.com

---

Made with ❤️ by MindPal Team
