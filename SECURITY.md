# Security Policy

## API Key Handling

MingYun is designed as a local-first desktop/web app.

- Do not commit real API keys.
- Do not put real API keys in `.env.example`, README files, issues, screenshots, or release notes.
- `.env`, `.env.*`, build outputs, archives, local verification files, and the reference project are ignored by Git.
- API keys entered in the model manager are stored only in the current browser `localStorage`.
- During a reading request, the key is sent only to the local backend at `127.0.0.1:8787`, so the local process can call the selected provider.
- API keys are not written to `model_registry.json`, bundled assets, Git history, or the packaged executable.

If a key is accidentally exposed, revoke it immediately in the provider console and generate a new one.

## Reporting Security Issues

Please open a private report or contact the maintainer before publishing details of a vulnerability. Avoid including real API keys, personal birth data, or provider account information in public issues.
