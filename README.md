# 智能医疗分诊与报告解读 Agent

## 业务背景

医院里,患者挂号时经常「不知道该挂哪个科」,检验报告出来后又依赖医生逐份人工解读——慢、且占用医生资源。

本项目是一个医疗 AI 系统,围绕两个 Agent 解决这两个痛点:

- **分诊 Agent**:患者用自然语言描述症状("我头疼发烧三天了该挂什么科?"),系统结合**本院分诊指引(RAG)** 推荐**真实存在的科室**(而非模型瞎编的科室),支持多轮对话。
- **报告解读 Agent**:检验科录入结构化报告后,系统**异步**生成带知识引用的 AI 解读;患者还能就报告继续多轮追问。

## 技术栈

FastAPI · PostgreSQL(pgvector) · Redis · Celery · Vue3 · DeepSeek · DashScope embedding-3

## 系统架构

分诊 Agent 采用**固定工作流**编排(而非 LangChain 自主路由),每一步都是必执行的安全步骤:

```
患者症状
  ↓ ① 从 Redis 加载多轮历史
  ↓ ② RAG 检索分诊指引(pgvector 向量 + 全文检索 + RRF,Top3)
  ↓ ③ 查询本院真实科室(白名单约束)
  ↓ ④ 组装 Prompt(历史 + RAG 片段 + 科室列表)
  ↓ ⑤ DeepSeek 生成
  ↓ ⑥ 内容安全审核(免责声明/确定性诊断/用药建议)
  ↓ ⑦ 提取科室 → 匹配数据库真实科室
  ↓ ⑧ 写回 Redis
```

报告解读 Agent 采用 **Celery 异步解耦**:

```
检验科录入报告 → 报告先落库(pending)→ 快速返回
                              ↓
                    Celery Worker:RAG 检索 → DeepSeek 解读 → 审核 → 落库
                    (completed / failed,失败可重试,不丢原始报告)
```

## 评测指标

离线回归评测(10 例分层报告:正常 / 常见异常 / 多项异常 / 极端异常):

| 指标 | 说明 | 结果 |
|---|---|---|
| 解读成功率 | 10 例报告完成 AI 解读 | 10/10 |
| 免责声明通过率 | 生成内容含「仅供参考」 | 100% |
| 无越界表达通过率 | 无「确诊 / 建议服用」等越界表述 | 100% |
| 通俗易懂度(LLM-as-Judge) | 1–5 分 | 5.0/5 |
| 指标覆盖度(LLM-as-Judge) | 1–5 分 | 4.9/5 |

> 注:以上为 LLM-as-Judge 的**相对评测**,用于对比 Prompt / RAG 配置改动前后的效果;**不代表医学诊断准确率**。当前生成模型与评委模型同为 DeepSeek,测试集仅 10 例,后续仍需独立评委模型与更大测试集。

## 前端页面展示

界面截图见 `项目截图/` 目录(含分诊 Agent、知识库、科室/医生管理、报告解读、报告追问等 20 张)。

## 快速启动

### 后端(Docker Compose)

```bash
cd Backend
cp .env.example .env          # 填入 DeepSeek / DashScope API Key
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app python scripts/init_data.py
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec app python scripts/seed_drugs.py
```

### 前端

```bash
cd medical-admin && npm install && npm run dev    # 后台管理端 :3000
cd medical-client && npm install && npm run dev   # 患者端 :3001
```

### 踩坑记录

- **Docker 镜像加速**:国内需在 `/etc/docker/daemon.json` 配置 registry-mirrors(`docker.m.daocloud.io`、`docker.1ms.run`);若含失效镜像源(如 `docker.xuanyuan.me`),BuildKit 拉取 `python:3.12-slim` 会报 403 Forbidden。
- **代理变量**:`.env` 里若设置了 `HTTP_PROXY` / `HTTPS_PROXY`,Python `requests` 会自动读取并走代理,导致 Celery 调 DashScope 报 `ProxyError`;本地无代理时需注释掉这两行。

## 分支管理

采用 main / dev 双分支:

| 分支 | 用途 |
|---|---|
| main | 稳定可展示版本,clone 下来就能跑通 |
| dev | 日常开发、实验、评测先行落地 |

## 技术栈(详细)

- **编排**:自定义工作流 + RAG(不用 LangChain Agent;LangChain 仅用于文档切分)
- **LLM**:DeepSeek-chat(OpenAI 兼容,分诊 30s 超时 / 解读 60s 超时,指数退避重试)
- **Embedding**:DashScope `text-embedding-v3`;向量库 PostgreSQL + pgvector
- **检索**:向量检索 + 全文检索(jieba 分词 → tsvector)+ RRF 融合
- **后端**:FastAPI(全异步)+ SQLAlchemy(异步)+ Celery + Redis
- **前端**:Vue3 + TypeScript + Element Plus + Vite(管理端 / 患者端)
- **评测**:确定性规则检查 + LLM-as-Judge(`scripts/eval_agents.py`)
- **部署**:Docker Compose(API / Celery Worker / Celery Beat / PostgreSQL / Redis)+ Alembic 迁移

## 个人职责

- 基于「自定义工作流 + RAG」编排分诊、报告解读两个 Agent,将 RAG 检索、科室白名单匹配、内容安全审核固化为**必执行步骤**(而非 LangChain 自主路由),保证医疗场景的确定性与可审计。
- 自建混合检索 RAG:Markdown 结构感知切分 + 超长段落二次切分(400 字 / 60 字重叠),pgvector 向量检索 + jieba 全文检索 + RRF 融合;知识库按 `source_type` 隔离(分诊只检索分诊指引、解读只检索医学资料)。
- 搭建统一 LLM 网关:输入限制、指数退避重试、Redis 按日 Token 预算(80% 告警 / 100% 熔断)、Prompt 文件化 + 版本化、LLM/RAG 调用日志。
- 用 Celery 做报告解读异步解耦与幂等:状态机(pending / completed / failed)+ 状态检查,AI 失败不丢原始报告、支持失败重试。
- 实现医疗内容安全:Prompt 约束 + 生成后规则审核(免责声明 / 确定性诊断 / 用药建议),不合规回答以安全文案降级。
- 患者 / 后台双 JWT scope 隔离,后台按角色(医生 / 药师 / 收费员 / 检验科 / 管理员)后端授权。
