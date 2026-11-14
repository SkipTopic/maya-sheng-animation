# Maya MCP 安装、配置和安全接入

## 1. 本 Skill 使用哪一种 Maya MCP

当前案例项目实际使用并验证的是：

```text
PatrickPalmer/MayaMCP
官方仓库：https://github.com/PatrickPalmer/MayaMCP
当前案例本地 README 版本：v0.2.0
```

该实现通过 Maya 的本地 commandPort 通信，不要求在 Maya 内安装插件。官方文档标注测试过 Maya 2023、2025；当前案例在 Maya 2024 中也有实际使用记录。

Maya MCP 是本地控制桥，不是动画 AI 模型，也不负责自动完成分镜或表演。不要将其他同名仓库的安装路径、端口或工具名混入本指南。

安装前重新阅读官方 README；若上游变化，以官方文档和用户确认的版本为准。不要为了“最新版”自动更新已经可用的 MCP。

## 2. 本 Skill 不包含的内容

- 不包含 MayaMCP 源码或 ZIP。
- 不包含 Maya 安装包。
- 不包含 Python 虚拟环境。
- 不包含任何账号、令牌或凭据。
- 不自动执行下载、安装或全局安全配置修改。

需要安装时，先向用户说明官方来源、目标目录和下载动作，再按用户的网络与安全要求执行。

## 3. 官方安装要求

官方 README v0.2.0 要求 Python 3.10 或更高版本。典型步骤：

```bash
git clone https://github.com/PatrickPalmer/MayaMCP.git
cd MayaMCP
python -m venv .venv
```

Windows 激活：

```bash
.venv\Scripts\activate.bat
```

macOS/Linux：

```bash
source .venv/bin/activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

不要把本 Skill 的 `scripts/` 当成 MCP 的 `src/`。MCP 服务入口是：

```text
<MayaMCP项目>\src\maya_mcp_server.py
```

## 4. MCP 客户端 stdio 配置

通用 `mcpServers` 结构：

```json
{
  "mcpServers": {
    "MayaMCP": {
      "type": "stdio",
      "command": "C:/full/path/MayaMCP/.venv/Scripts/python.exe",
      "args": [
        "C:/full/path/MayaMCP/src/maya_mcp_server.py"
      ]
    }
  }
}
```

规则：

- 使用实际存在的绝对路径。
- 路径包含中文或空格时保持 JSON 字符串完整。
- 合并到现有 `mcpServers`，不要覆盖其他服务器。
- 不把凭据写进此配置；该 MCP 的本地案例不需要账号令牌。
- 修改前备份原配置。
- 修改后按客户端要求重启或启用，不要假设自动生效。

### WorkBuddy 配置位置

```text
~/.workbuddy/mcp.json
```

不是 `~/.workbuddy/.mcp.json`。

写入后在连接器管理页的自定义连接器入口找到新服务器，并按客户端流程点击“信任/启用”。不要由自动化脚本直接长期运行 MCP 服务来替代客户端配置。

### 当前案例机器的实际配置示例

```json
{
  "mcpServers": {
    "MayaMCP": {
      "type": "stdio",
      "command": "C:\\Users\\<用户>\\Tools\\MayaMCP\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\<用户>\\Tools\\MayaMCP\\src\\maya_mcp_server.py"
      ]
    }
  }
}
```

该路径只适用于当前案例机器。其他电脑必须替换。

## 5. Maya 侧通信

该实现利用 Maya 的 MEL commandPort。客户端发出 Python 操作时，MCP 会把它包装后经端口发送，再读取结果。

注意：

- Maya GUI 必须先运行。
- 客户端和 Maya 必须属于同一台机器的本地可信环境。
- 不把 commandPort 暴露到公共网络。
- 工具名称以客户端实际列表为准，不假设所有同名 MCP 都一样。

当前案例曾使用：

```text
scene_open
execute_python
capture_viewport
get_object_attributes
list_objects_by_type
```

官方 README 还列出 `create_object`、`get_object_attributes`、`set_object_attributes`、`scene_new`、`scene_save`、`select_object` 等。某些当前工具可能来自本地扩展；原版上游安装不应被假设一定包含 `execute_python` 或 `capture_viewport`。缺少通用执行/截图工具时，使用 Maya Script Editor 或审核过的本地文件通道，不要伪造调用成功。

## 6. 安全警告

官方 README 描述：首次通信会出现 Maya 安全警告，并建议为持续通信选择“Allow All”。

本 Skill 增加安全限制：

1. 不自动点击“全部允许”。
2. 先确认请求来自已安装的本地 MCP、代码内容已经审核。
3. 能逐次“允许”就不全局放开。
4. 高频弹窗阻塞时，优先使用项目已有的可信本地文件执行通道。
5. 如果用户明确选择“全部允许”，记录其适用范围，并确保端口只监听本机。
6. 不在安全警告出现时连续重试同一请求，避免堆积多个模态对话框。

## 7. 只读连接验收

接入后按以下顺序：

1. 查询 Maya 版本、当前场景、修改状态、单位和播放范围。
2. 查询网格、关节、相机和外部 reference。
3. 确认当前场景是否需要先保存。
4. 新建测试对象前另存工作版本，或使用明确的临时对象并清理。
5. 修改后读取实际属性并出图。
6. 保存后重新打开，再查一次。

不要在第一次连接时直接调用 `scene_new(force=True)`，否则会丢失未保存工作。

## 8. 常见故障

### `WinError 10061` / connection refused

含义通常是 Maya 未运行、端口未打开或 MCP 配置不匹配。检查进程、端口和工具配置，不要把它当成 Python 语法错误。

### 工具执行后无结果

- 检查是否出现第二个“读取结果”的安全警告。
- 检查模态对话框。
- 检查客户端 stdout/日志。
- 不无限重试；必要时改用本地文件通道。

### Maya 进程消失

记录未执行命令，重启 Maya，重新打开当前工作版本，再做轻量只读测试。不要假定重启前操作已保存。

### MCP 功能不够

优先使用客户端已提供的通用 Python 执行工具；若不存在，阅读官方扩展方法或建立审核过的本地执行通道。不要下载另一个同名 MCP 来碰运气。

## 9. MCP 验收记录模板

```text
MCP 官方来源：
本地版本/提交：
Maya 路径与版本：
Python 与 venv：
MCP 客户端配置文件：
服务 command/args：
实际工具列表：
只读查询结果：
安全警告处理方式：
故障与恢复：
未解决事项：
```

完成接入只代表可以通信，不代表模型、动画或渲染已完成。