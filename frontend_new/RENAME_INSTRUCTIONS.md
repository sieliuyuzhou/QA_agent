# 重命名说明

## 当前状态

项目当前位于 `frontend_new` 目录，而不是最初的 `frontend` 目录。

**原因**：在创建项目时，`frontend` 目录被某个进程锁定，无法删除或重命名。

## 解决方案

### 方案 1：保持现状（推荐）

继续使用 `frontend_new` 作为项目目录：
- 所有功能已完整实现
- 项目已成功构建
- 只需在命令中使用 `frontend_new` 路径

### 方案 2：手动重命名

在关闭所有可能占用目录的程序后，执行：

```bash
cd E:\myProgram\QA_agent
rm -rf frontend  # 如果存在
mv frontend_new frontend
```

**注意**：可能需要关闭：
- 所有终端窗口
- 代码编辑器（VS Code、IDE 等）
- 文件管理器

### 方案 3：在新位置重新初始化

如果重命名困难，可以在 `frontend` 目录重新初始化：

```bash
cd E:\myProgram\QA_agent
mkdir frontend
cd frontend
# 然后按照 README.md 中的步骤重新初始化项目
```

## 相关文档

所有文档已更新为使用 `frontend_new` 路径：
- `docs/solution/customer-service-frontend-design.md`
- `docs/worklists/customer-service-frontend-worklist.md`
- `frontend_new/README.md`
