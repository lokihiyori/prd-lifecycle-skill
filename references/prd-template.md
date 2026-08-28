# Canonical Living PRD Template

Use this shape as a baseline and adapt headings to the product. Keep the marker comments unchanged when deterministic tracking is desired.

```markdown
# <Product> 产品需求文档（Living PRD）

## 0. 文档控制与本周期执行面板

| 字段 | 内容 |
|---|---|
| PRD 文档版本 | v0.1.0 |
| 目标产品版本 | <release> |
| 文档状态 | Draft |
| 当前周期 | <start> 至 <end> |
| 下一次评审 | <date> |
| 产品负责人 | — |
| 技术负责人 | — |
| 权威副本 | — |

### 0.1 本周期可以直接开工 / 下一步推荐

<!-- PRD-LIFECYCLE:NEXT-STEPS:START -->
| ID | 推荐动作 | 原因 | 建议负责人 | 目标日期 | 完成证据 |
|---|---|---|---|---|---|
| FR-EXAMPLE-001 | 开始该需求 | P0 且没有未解决依赖 | 需求负责人 | 待排期 | 首个可验证交付物 |
<!-- PRD-LIFECYCLE:NEXT-STEPS:END -->

### 0.2 功能需求实施进度

<!-- PRD-LIFECYCLE:FUNCTIONAL-PROGRESS -->
| ID | 需求项 | 优先级 | 状态 | 负责人 | 完成日期 | 依赖 | 备注/证据 |
|---|---|---|---|---|---|---|---|
| FR-EXAMPLE-001 | <requirement> | P0 | Not Started | — | — | — | — |

### 0.3 技术需求实施进度

<!-- PRD-LIFECYCLE:TECHNICAL-PROGRESS -->
| ID | 需求项 | 优先级 | 状态 | 负责人 | 完成日期 | 依赖 | 备注/证据 |
|---|---|---|---|---|---|---|---|
| TR-EXAMPLE-001 | <requirement> | P0 | Not Started | — | — | — | — |

### 0.4 依赖、风险与决策状态

<!-- PRD-LIFECYCLE:DEPENDENCY-REGISTER -->
| ID | 类型 | 事项 | 状态 | 负责人 | 截止日期 | 备注/证据 |
|---|---|---|---|---|---|---|
| Q-001 | Decision | <decision> | Open | — | <date> | — |

## 1. 执行摘要

## 2. 背景与问题定义

## 3. 产品目标、非目标与指标

## 4. 术语表

## 5. 用户、角色与权限

## 6. 当前版本范围

## 7. 核心用户旅程

## 8. 功能需求

## 9. P0/P1 需求详情与验收标准

## 10. AI 行为与安全边界（适用时）

## 11. 风险、矛盾与决策

## 12. 发布门槛与路线图

## 13. 来源映射

## 附录 A：变更历史

<!-- PRD-LIFECYCLE:CHANGELOG -->
| 版本 | 日期 | 更新人 | 变更内容 | 证据 |
|---|---|---|---|---|
| v0.1.0 | <date> | <actor> | 创建初稿 | <source> |
```

## Status labels

Use the English canonical values in marker-managed tables for script compatibility:

- `Not Started`
- `In Progress`
- `Blocked`
- `Reported Complete`
- `Verified`

The surrounding narrative may include Chinese translations, but do not alter the canonical table values.
