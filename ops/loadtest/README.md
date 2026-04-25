## k6 压测（smoke/基线）

### 安装

- **k6**：按官方安装（Windows 可用 `choco install k6`）

### 运行

```bash
k6 run ops/loadtest/k6_smoke.js
```

可选参数：

```bash
BASE_URL="http://127.0.0.1:8000" VUS=50 DURATION="60s" k6 run ops/loadtest/k6_smoke.js
```

### 观测点

- **核心指标**：`/metrics` 中 `http_requests_total`、`http_request_duration_seconds`
- **判定**：默认阈值 `p95<1500ms` 且失败率 `<1%`

