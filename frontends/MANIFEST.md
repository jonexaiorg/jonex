# 前端子应用清单

> ⚠️ DOCUMENTATION ONLY：本文档仅作记录，当前未被任何脚本自动消费。
> 子应用 ≥ 3 个时再考虑改为 manifest.yaml 并做 Nginx 配置自动生成。

## Shell 应用（入口）
- 路径：`/`
- 职责：唯一登录入口、全局导航、路由守卫、多子应用切换
- 开发端口：5173
- 状态：✅ 开发中

## 业务子应用


### core-business（核心业务）
- 挂载路径：`/core-business/`
- API 前缀：`/api/v1/`
- 状态：✅ 开发中
- 开发端口：5175

### platform-management（平台管理）
- 挂载路径：`/platform-management/`
- API 前缀：`/api/v1/`
- 状态：✅ 开发中
- 开发端口：5177

### ecosystem-management（生态管理）
- 挂载路径：`/ecosystem-management/`
- API 前缀：`/api/v1/`
- 状态：✅ 开发中
- 开发端口：5176

### knowledge-base（知识库）
- 挂载路径：`/kb/`
- API 前缀：`/api/v1/knowledge-base/`
- 状态：⏸️ 规划中
- 本体能力：知识库管理后台含本体 TBox schema 配置、本体实体 / 关系可视化图谱、本体查询调试等页面（待开发）
