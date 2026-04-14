# 前端工程说明（Vue 3 + TypeScript + Vite）

该前端项目基于 `Vue 3 + TypeScript + Vite` 构建，使用 Vue 3 的 `<script setup>` 单文件组件（SFC）模式。

## 快速开始

- 安装依赖：`npm install`
- 本地开发：`npm run dev`
- 生产构建：`npm run build`
- 本地预览构建产物：`npm run preview`

## TypeScript 约定

- 保持严格检查：已启用 `noUnusedLocals` 与 `noUnusedParameters`。
- 对于“有意未使用”的函数参数，统一使用 `_` 前缀命名（例如 `_ctx`），避免无意义告警。
- 全局类型声明建议放在 `env.d.ts` 或 `types/**/*.d.ts`，并由 `tsconfig.app.json` 的 `include` 自动纳入。
- 路径别名使用 `@/* -> src/*`，统一通过 `@/` 引用 `src` 下模块。

## 参考资料

- Vue `<script setup>` 文档：[https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup](https://v3.vuejs.org/api/sfc-script-setup.html#sfc-script-setup)
- Vue TypeScript 指南：[https://vuejs.org/guide/typescript/overview.html#project-setup](https://vuejs.org/guide/typescript/overview.html#project-setup)
