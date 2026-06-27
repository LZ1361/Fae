# 命运 MVP

“命运”把测试结果拆成两层：

1. 本地证据层：先计算星座、近似干支、五行权重、心理自评、置信度与边界。
2. 大模型解释层：模型只能解释证据层提供的内容，不能自由编造结论。

## 页面

- 测试页：`http://127.0.0.1:8787/`
- 模型管理页：`http://127.0.0.1:8787/models.html`

主测试页只负责输入出生信息、选择模型和展示报告。模型 Base URL、真实 Model ID、API Key、高级参数统一在模型管理页配置。

## 启动

```powershell
& 'C:\Users\17739\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' mingyun_app/app.py
```

## 测试

```powershell
& 'C:\Users\17739\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' -m unittest discover -s mingyun_app/tests -v
& 'C:\Users\17739\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe' --check mingyun_app/static/app.js
```

## 官方模型配置

### OpenAI

- Base URL：`https://api.openai.com/v1`
- 推荐接口：Responses API
- Endpoint：`POST /v1/responses`
- 默认模型：`gpt-5.5`
- API format：`openai_responses`

### DeepSeek

- Base URL：`https://api.deepseek.com`
- Endpoint：`POST /chat/completions`
- 默认模型：`deepseek-v4-pro`
- 低成本模型：`deepseek-v4-flash`
- API format：`openai_compatible`

### Anthropic

- Base URL：`https://api.anthropic.com`
- Endpoint：`POST /v1/messages`
- Header：`anthropic-version: 2023-06-01`
- 默认模型：`claude-opus-4-8`
- API format：`anthropic_messages`

## 安全边界

- API Key 不写入项目文件；当前 MVP 仅存储在浏览器 `localStorage`，属于当前电脑和当前浏览器配置，不会随软件交付给客户。正式售卖前应改为服务端加密存储或用户自带密钥。
- 后端会拒绝缺少 `base_url` 或 `model_id` 的远程模型。
- 后端会过滤 `model`、`messages`、`stream`、`response_format`、`input`、`text` 等不可由高级参数覆盖的核心字段。
- 正式报告生成会把过低的 `max_tokens` 自动抬高到 6000，避免 JSON 被截断后页面无法显示。

## DeepSeek 本地调试

可以复制 `.env.example` 为 `.env`，填入新生成的密钥：

把服务商后台复制的 Key 写入本机 `.env` 或系统环境变量即可；不要把真实 Key 写入仓库文件。

也可以在模型管理页中填写 API Key 并点击“测试连接”。这种方式只适合本机调试。
