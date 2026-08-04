# Mnemovela-open - 宣传材料（中文）

将 `{LINK}` 替换为 `https://github.com/axisrobo/mnemovela-open`。

---

## 微博（3篇）

### 微博 1（产品介绍）

给你的 AI Agent 装上"长期记忆"。

Mnemovela 开源了——一个专门为 AI 编程 Agent 设计的认知运行时。支持记忆存储、知识图谱、工作区状态，跨 session 保持上下文。

- Python / TypeScript / Go / CLI 全支持
- MCP / JSON-RPC / REST / gRPC 四种协议
- 14 种认知记忆类型（事实、决策、约束、模拟、知识等）
- Apache-2.0 协议，预编译二进制直接下载

GitHub：{LINK}

#AI工具 #开源 #Agent开发 #AgentMemory

---

### 微博 2（场景化）

AI 编程助手每次新 session 都"失忆"？

Mnemovela 让 Agent 学会记住：
- 上次改了哪些文件 —— 不用重新翻代码
- 做了哪些决策 —— 不用再讨论一遍
- 踩了哪些坑 —— 不用再 debug 一次
- 项目有哪些约束 —— 改动前自动提醒

关了 IDE，记忆还在。下次打开，上下文自动恢复。

{LLINK}

#开发工具 #AI编程

---

### 微博 3（极简，适合配图转发）

AI Agent 的三件套：
1. 推理（LLM）
2. 工具（Function Call）
3. 记忆（Mnemovela）—— 今天刚开源

Apache-2.0，GitHub 见 → {LINK}

---

## LinkedIn（2篇，中文版）

### 第 1 篇 —— 产品发布

Mnemovela 正式开源（Apache-2.0）：一个 Agent 认知运行时，为 AI 编程助手提供跨 session 的长期记忆、知识图谱和工作区状态。

工作原理：
- Agent 在查文件之前先调 `mnemovela.search_memory()`
- 工作过程中用 `capture_decision()`、`capture_error()`、`add_fact()` 记录
- 会话结束时 `session_end()` 写入摘要、变更文件、决策列表
- 下次会话开始时 Agent 已经知道项目状态

支持 MCP 协议，兼容 OpenCode、Claude Code、Codex。

客户端 SDK 覆盖 Python、TypeScript、Go，提供 CLI 工具、API 文档、预编译二进制（Windows/Linux/macOS）。

底层：Git 式分支/合并语义、14 种类型化认知帧、可替换存储后端、混合检索（词汇 + 语义 + 关系 + 时间）。

{LLINK}

---

### 第 2 篇 —— 架构角度

大多数"Agent 记忆"项目是向量数据库 + 搜索。Mnemovela 不同。

它建模了 14 种认知记忆类型，每种都有独立的 Schema、检索策略和保留策略：

- **event（事件）**：发生了什么（5W2H + 证据 + 角色绑定）
- **knowledge（知识）**：稳定的真理（声明 + 置信度 + 时间上下文）
- **experience（经验）**：行动后的反思（结果 + 显著性）
- **simulation（模拟）**：假设推演（初始状态 + 操作符 + 可能结果）
- **emotion（情绪）**：情感状态（效价 / 唤醒度 / 威胁评分）
- **procedure（过程）**：可复用的操作指南（前置条件 + 顺序步骤）
- **intention（意图）**：Agent 目标（目标状态 + 截止日期 + 成功标准）
- **belief（信念）**：可修正的世界观（前一当前状态 + 置信度）
- **mission（任务）**：多阶段跟踪（阶段事件 + 进度）
- **preference（偏好）**：风格偏好（认知 / 交互 / 执行）
- **workspace_state（工作区状态）**：临时任务上下文
- **decision（决策）**：归档的设计选择及理由
- **constraint（约束）**：未来工作必须遵守的项目不变式
- **relationship（关系）**：知识图谱实体间的边

全部通过 MCP 协议接入 —— OpenCode、Claude Code、Codex 即插即用。

{LLINK}

---

## CSDN（技术博客，约800字）

### 标题：AI编程Agent缺的不是智商，是记忆 —— Mnemovela开源认知运行时介绍

**一、Agent 的"失忆症"**

用过 AI 编程工具（OpenCode、Claude Code、Codex 等）的人一定熟悉这个流程：打开新 session、描述任务、Agent 检索文件、理解项目、完成工作、关闭——下次再开，Agent 又"忘了一切"，从头开始。

这本质上是**上下文断裂**的问题。session 内的上下文窗口有限，跨 session 的上下文则完全不存在。

Mnemovela 解决的就是这个"跨 session 上下文"问题。

**二、Mnemovela 是什么**

Mnemovela 是一个**Agent 认知运行时**，提供：
- 长期记忆存储：Agent 每次工作的内容、决策、错误、发现都可持久化
- 知识图谱：模块依赖、文件关系、项目约束以结构化方式存储
- 工作区状态：当前活跃文件、待定决策、测试状态等临时上下文
- 混合检索：词汇 + 语义 + 关系 + 时间四维搜索

它不是"文档数据库"，而是一个**认知模型**——理解事件、知识、经验、模拟等 14 种不同的记忆类型。

**三、Agent 怎么用 Mnemovela**

会话开始 → Agent 先调 `search_memory()` 查历史
工作过程 → Agent 记录决策、错误、发现
会话结束 → Agent 写入摘要、变更文件列表、关键决策
下次会话 → 上下文自动恢复

内置 MCP Server，支持 OpenCode、Claude Code、Codex 即插即用。也支持 JSON-RPC、REST、gRPC。

**四、开源信息**

- 协议：Apache-2.0
- GitHub：{LINK}
- 客户端：Python / TypeScript / Go / CLI
- 预编译二进制：Windows / Linux / macOS（amd64/arm64）

---

## 微信公众号（4段式推文）

### 标题：给你的 AI 编程助手装上"长期记忆" —— Mnemovela 开源

**（第1段 —— 痛点）**

用 AI 写代码的人都有一个共同的体验：Agent 在单个 session 里很强，但只要关掉窗口，下次打开——它什么都不记得了。你又要重新解释项目结构、描述任务背景、提醒它上次做到哪了。这不是 Agent 不够聪明，而是它缺乏**长期记忆**。

**（第2段 —— 产品）**

Mnemovela 就是专门解决这个问题的。它是一个开源的**Agent 认知运行时**，为 AI Agent 提供：跨 session 记忆持久化、结构化知识图谱、工作区状态保存、混合检索。今天正式以 Apache-2.0 协议开源。

**（第3段 —— 场景）**

Agent 在 Mnemovela 的加持下，工作流程变成：会话开始先查历史记忆 → 工作过程实时记录决策和错误 → 会话结束写回摘要和变更列表 → 下次会话上下文自动恢复。支持 OpenCode、Claude Code、Codex（通过 MCP 协议即插即用）。提供 Python、TypeScript、Go 三种 SDK。

**（第4段 —— 获取 + CTA）**

GitHub：{LINK}。Apache-2.0 完全开源。预编译二进制已就绪。文档齐全：SDK 文档、API 参考、Agent 集成 Guide。如果你在开发 AI Agent，试试 Mnemovela —— 别让 Agent 每次从头开始。

---

## 通用 slogan / 一句话

| 用途 | 文字 |
|------|------|
| 定位一句话 | Mnemovela：给 AI Agent 装上长期记忆 |
| 技术一句话 | Git 式分支语义 x 14 种认知记忆类型 x 混合检索 —— 为 AI Agent 而生 |
| 对比定位 | 不是向量数据库，不是聊天记录。是 Agent 的记忆模型。 |
