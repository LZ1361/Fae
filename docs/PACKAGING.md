# 命运：打包与开源发布说明

## 本地打包 Windows exe

在项目根目录运行：

```powershell
cd "D:\My_computer\桌面\Ai_Agent\算命"
.\scripts\build_windows.ps1 -Python "C:\Users\17739\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -Name MingYun
```

打包完成后，可执行文件位于：

```text
dist\MingYun.exe
```

用户双击 `MingYun.exe` 后，保持窗口打开。软件会自动打开浏览器；若未自动打开，可手动访问：

```text
http://127.0.0.1:8787/
```

## API Key 交付原则

API Key 不写入项目文件，也不会随 exe 一起交付。用户需要在“模型管理”页面自行配置自己的 API Key。

开源版的 API Key 处理边界：

- 用户填写的 Key 只保存在当前电脑、当前浏览器的 `localStorage` 中。
- 生成报告时，Key 只会发送到本机 `127.0.0.1:8787` 后端进程，用于调用用户选择的模型服务商。
- Key 不写入 `model_registry.json`、`.env.example`、Git 仓库、GitHub Actions artifact 或打包后的 exe。
- 如果需要做商业云服务，应改为服务端加密存储、权限隔离和审计日志。

## GitHub 开源发布

推荐流程：

```powershell
git init
git add .
git commit -m "Initial open-source release of MingYun"
git branch -M main
git remote add origin https://github.com/<your-name>/mingyun.git
git push -u origin main
```

推送后，GitHub Actions 会自动运行 `.github/workflows/windows-build.yml` 并上传 `MingYun.exe` 构建产物。

## 正式发布 Release

1. 在 GitHub 仓库进入 Releases。
2. 点击 Draft a new release。
3. 标签建议使用 `v0.1.0`。
4. 上传 Actions 产物中的 `MingYun.exe`。
5. 在说明中写清楚：AI 生成内容仅供娱乐和自我反思，不构成医疗、投资、法律或重大人生决策建议。
