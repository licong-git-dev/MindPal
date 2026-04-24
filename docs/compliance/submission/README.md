# 📦 备案提交专区

本目录是 **管理层视角** 的备案准备材料，面向创始人 / 法务 / 公司行政等非工程角色。

## 使用路径

```
T-4 周: 准备公司资质  → COMPANY_QUALIFICATION_CHECKLIST.md
T-3 周: 补齐工程 GAP   → 参考 ../02_ALGORITHM_SAFETY_SELF_ASSESSMENT.md "缺口清单"
T-2 周: 跑评测集       → 参考 ../evaluation/README.md
T-1 周: 律师审查法律文件 → ../legal/README.md
T-0:    最终自检        → SUBMISSION_PREFLIGHT.md
T-0:    打包提交        → SUBMISSION_PACKAGE_INDEX.md
T+4-12 周: 监管反馈 / 补正
T+12 周+: 拿到备案号 → 公示
```

## 文档清单

| 文件 | 职责 |
|-----|------|
| [COMPANY_QUALIFICATION_CHECKLIST.md](COMPANY_QUALIFICATION_CHECKLIST.md) | 公司资质材料准备清单（营业执照、法人身份证等）|
| [INCIDENT_RESPONSE_SLA.md](INCIDENT_RESPONSE_SLA.md) | 事件处置 SLA 文档（GAP-8）|
| [SUBMISSION_PREFLIGHT.md](SUBMISSION_PREFLIGHT.md) | 提交前 40 项自检 |
| [SUBMISSION_PACKAGE_INDEX.md](SUBMISSION_PACKAGE_INDEX.md) | 最终提交包目录结构与索引模板 |

## 全流程图

```
             ┌─────────────────────────────────────┐
             │ [代码仓已交付的]                    │
             │ - P0/P1/P2 全部技术功能 ✅         │
             │ - P3-2 内容审核 ✅                 │
             │ - P3-3 数据权利 ✅                 │
             │ - GAP-3/4/5/6/7/9 代码骨架 ✅      │
             │ - 自评估报告模板 ✅                │
             │ - 评测集 SOP + 种子题库 ✅         │
             │ - 法务文档模板 ✅                  │
             │ - 提交 checklist ✅ (本目录)       │
             └─────────────────────────────────────┘
                          ↓
             ┌─────────────────────────────────────┐
             │ [需要外部动作的]                    │
             │ - 运营招 2-3 人补齐题库             │
             │ - 运营跑评测 + 整改 + 复测          │
             │ - 法务委托律所定稿 3 份法律文件     │
             │ - 管理层准备公司资质 + 签字          │
             │ - 工程完成 GAP-1/2/4/5 真实接入     │
             └─────────────────────────────────────┘
                          ↓
                  [正式提交网信办]
                          ↓
              [4-12 周审核 + 补正]
                          ↓
                   [拿到备案号]
                          ↓
                  [frontend 公示]
```
