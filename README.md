# 智能医疗预约诊疗系统

基于大模型与 RAG 的智能医疗系统,提供**智能分诊**、**报告解读**两个 AI Agent,并覆盖挂号、接诊、处方、发药、收费的完整业务流程。

## ✨ 核心功能

### AI 能力

- **智能分诊 Agent**:患者描述症状后,通过「RAG 检索 + 真实科室白名单 + DeepSeek」推荐挂号科室,支持多轮对话与端到端流式输出
- **报告解读 Agent**:检验报告录入后由 Celery 异步生成 AI 解读,患者可基于报告进行多轮追问
- **混合检索 RAG**:pgvector 向量检索 + PostgreSQL 全文检索(jieba 分词)+ RRF 融合排序

### 业务能力

- **患者端**:注册登录、智能分诊挂号、病历 / 处方 / 账单 / 检查报告查询、处方支付
- **管理端**:医生接诊开方、药师发药、收费员结算、检验科录入报告、管理员维护科室 / 医生 / 药品 / 知识库

## 🛠 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python · FastAPI · SQLAlchemy · PostgreSQL(pgvector) · Redis · Celery |
| 前端 | Vue3 · TypeScript · Element Plus · Vite |
| AI | DeepSeek · DashScope(Embedding) · LangChain(仅文档切分) |
| 部署 | Docker · Docker Compose · Alembic |

## 🏗 架构设计

- **自定义工作流 + RAG**(而非 LangChain Agent):将 RAG 检索、科室匹配、内容审核固化为必执行步骤,保证医疗场景的确定性与可审计
- **统一 LLM 网关**:输入限制、指数退避重试、Redis 按日 Token 预算、调用日志、Prompt 文件化与版本化
- **异步解耦**:Celery 执行报告解读、知识库向量化,任务状态机 + 幂等,AI 失败不丢核心业务数据
- **内容安全**:Prompt 约束 + 生成后规则审核(免责声明 / 确定性诊断 / 用药建议)
- **双 JWT scope**:患者与后台两套 token 隔离,后台按角色(医生 / 药师 / 收费员 / 检验科 / 管理员)授权

## 📁 项目结构

```
├── Backend/            # FastAPI 后端
│   ├── app/
│   │   ├── api/        # 路由层(client / backoffice)
│   │   ├── services/   # 业务层(分诊 / 报告解读 / RAG / LLM)
│   │   ├── models/     # SQLAlchemy 数据模型
│   │   ├── schedule/   # Celery 任务
│   │   └── prompts/    # Prompt 文件(版本化)
│   ├── migrations/     # Alembic 数据库迁移
│   └── scripts/        # 数据初始化 / 离线评测脚本
├── medical-admin/      # 后台管理端(Vue3)
└── medical-client/     # 患者端(Vue3)
```

## 🚀 快速开始

### 后端(Docker Compose)

```bash
cd Backend
cp .env.example .env   # 填写 DeepSeek / DashScope API Key
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

## 📸 界面截图

见 `项目截图/` 目录。
