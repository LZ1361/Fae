# 命运 MingYun

命运是一款本地运行的 AI 辅助性格与命运解读软件。它会先根据出生日期、出生时间、出生地、历法、性别和心理自评计算可复核依据，再调用用户自行配置的大模型生成报告。

产品原则很简单：先有依据，再有解释；不为了情绪价值胡乱迎合，也不输出绝对化预测。

## 功能特点

- 生辰信息输入：支持公历/农历、闰月、出生时间精度、出生城市与性别。
- 本地证据计算：包含星座、近似四柱、生肖、节气、五行权重、十神关系、心理自评与置信边界。
- 大模型解释：支持 DeepSeek、OpenAI、Anthropic 与 OpenAI-compatible 模型。
- 模型管理页：用户自行配置 Provider、Base URL、Model ID、API Key、Temperature、Max tokens 与高级 JSON 参数。
- 报告展示：包含直白摘要、总体性格、事业、财运、感情、姻缘匹配、人生周期建议和可复核依据。
- 本地交付：可打包成 Windows `MingYun.exe`，用户双击后在本机浏览器使用。

## 安全与隐私

- 仓库不包含任何真实 API Key。
- `.env`、`.env.*`、构建产物和本地参考项目已被 `.gitignore` 排除。
- 用户在模型管理页填写的 API Key 只保存在当前电脑、当前浏览器的 `localStorage` 中。
- 生成报告时，API Key 只会随请求发送到本机 `127.0.0.1:8787` 后端进程，用于从本机调用对应模型服务商。
- 当前开源版不提供云端账号系统，也不会把用户 API Key 写入项目文件、Git 仓库或打包产物。

## 快速启动

```powershell
cd "D:\My_computer\桌面\Ai_Agent\算命"
python mingyun_app/app.py
```

启动后会自动打开浏览器。若未自动打开，可手动访问：

```text
http://127.0.0.1:8787/
```

模型管理页：

```text
http://127.0.0.1:8787/models.html
```

## 模型配置

进入“模型管理”，填写：

- Provider
- Base URL
- Model ID
- API Key
- Max tokens
- 高级请求参数 JSON

正式报告生成会把过低的 `max_tokens` 自动抬高到 `6000`，减少报告 JSON 被截断导致页面无法显示的问题。前端允许配置到 `16000`，但实际可用上限仍取决于你接入的模型服务商。

## 测试

```powershell
python -m unittest discover -s mingyun_app\tests
```

前端脚本语法检查：

```powershell
node --check mingyun_app/static/app.js
```

## 打包 Windows 可执行文件

```powershell
.\scripts\build_windows.ps1 -Python python -Name MingYun
```

生成文件：

```text
dist\MingYun.exe
```

用户双击 exe 后保持窗口打开，软件会自动打开浏览器到 `http://127.0.0.1:8787/`。

## GitHub Actions

仓库推送到 GitHub 后，`.github/workflows/windows-build.yml` 会自动构建 Windows exe，并上传为 Actions artifact。

## 开源协议

本项目使用 MIT License，详见 [LICENSE](LICENSE)。

## 免责声明

AI 生成内容仅供娱乐和自我反思参考，不构成医疗、投资、法律或重大人生决策建议。
