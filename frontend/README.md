# Frontend 开发说明

## 本地启动

```bash
npm install
npm run dev
```

## 后端联调配置

- 默认前端请求地址：`/api/v1`
- 默认 Vite 代理目标：`http://127.0.0.1:18000`

如需切换到其它后端端口（例如 `18000`），可在启动前设置环境变量：

```bash
VITE_API_PROXY_TARGET=http://127.0.0.1:18000 npm run dev
```

如果你希望前端直接请求绝对地址（不走代理），可设置：

```bash
VITE_API_BASE_URL=http://127.0.0.1:18000/api/v1 npm run dev
```
