# Maya Sheng Animation / 玛雅生动画

[中文快速开始](#中文快速开始) · [English Quick Start](#english-quick-start) · [Full Workflow / 全流程](#full-workflow--全流程) · [Failure Catalog / 故障目录](#failure-catalog--真实问题与解决方案) · [Validation / 验证](#validation--测试与跨-ai-可运行性)

**玛雅生动画**是一套让 AI 通过 Maya MCP 控制 Autodesk Maya，从人物模型和参考需求走到分镜、相机、动作、预览、渲染和交付的全流程 Skill。

**Maya Sheng Animation** is an end-to-end Skill for AI-directed Maya production: environment and MCP setup, model/rig gates, storyboards, cameras, character actions, playblast, rendering, validation, backup, and handoff.

**Skill ID:** `maya-sheng-animation`  
**Tested environment / 实测环境:** Maya 2024, Windows  
**MCP used in the source project / 原项目使用的 MCP:** `PatrickPalmer/MayaMCP` v0.2.0  
**MCP bundled? / 是否包含 MCP:** No / 不包含，必须单独安装或由用户提供。

---

## 1. This is a staged production system, not a one-click promise / 这是分阶段生产流程，不是虚假的一键承诺

本 Skill 可以帮助另一个 AI 真正执行流程，但不会承诺“任意模型、任意电脑、无需用户确认就能自动生成完美电影”。

The Skill gives another AI an executable procedure and tested tools. It does not claim that arbitrary models, hardware, references, and creative choices can produce a perfect film without review.

以下情况必须先停下来修复或询问用户：

- 模型没有骨架或蒙皮。
- 人物已经扭曲或袖口破裂。
- MCP 未安装、连接失败或出现安全警告。
- 分镜没有明确帧范围或动作范围。
- 静帧和短段尚未被用户确认。
- 最终分辨率、音轨或身体动作范围仍不明确。

---

## 2. Related repository / 配套仓库

人物模型已经扭曲、坐姿错误、IK 失灵或蒙皮破裂时，使用：

https://github.com/SkipTopic/maya-character-pose-recovery

`maya-character-pose-recovery` 负责“修复人物”；本仓库负责“从接入到动画交付的全流程”。  
The pose-recovery repository repairs the character; this repository manages the complete production workflow.

---

## 中文快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/SkipTopic/maya-sheng-animation.git
```

### 2. 收集输入

向 AI 提供：

- 人物模型路径、格式、是否带骨架/蒙皮/表情。
- Maya 可执行文件完整路径和版本。
- Maya MCP 名称、安装路径或现有配置。
- 参考视频、图片、分镜或文字剧情。
- 帧率、时长、分辨率和输出目录。
- 允许/禁止的动作：嘴型、手指、躯干、腿部、道具等。
- 是否需要字幕、原片音轨和最终全片。
- 机器内存、磁盘和下载限制。

复制并填写：

```text
assets/project-brief-template.json
assets/shotlist-template.csv
assets/shot-plan-template.json
```

不要把访问令牌写入任务简报。

### 3. 单独安装 Maya MCP

当前项目验证的是：

```text
https://github.com/PatrickPalmer/MayaMCP
版本：v0.2.0
```

官方基本要求为 Python 3.10+。典型安装：

```bash
git clone https://github.com/PatrickPalmer/MayaMCP.git
cd MayaMCP
python -m venv .venv
```

Windows 可直接使用虚拟环境 Python 安装依赖：

```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

MCP 配置模板见 `assets/maya-mcp-config-template.json`：

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

WorkBuddy 的配置位置是：

```text
~/.workbuddy/mcp.json
```

不是 `~/.workbuddy/.mcp.json`。合并到现有 `mcpServers`，不要覆盖其他服务。写入后按客户端流程信任/启用连接器。

官方说明该实现不需要在 Maya 内安装插件，使用本地 commandPort。安全警告不要自动点“全部允许”；先审核来源和代码。

完整指南：`references/maya-mcp-setup.md`。

### 4. 启动 Maya 并做只读检查

Maya 脚本必须在 Maya 内运行：

```python
import sys
sys.path.insert(0, r"<替换为仓库实际路径>/scripts")

from inspect_maya_project import inspect_project

report = inspect_project(
    joints=["Bip001Head"],  # 替换成实际骨名
    output_path="<项目路径>/logs/scene_audit.json",
)
```

先检查当前场景是否有未保存修改。不要在第一次连接时直接 `scene_new(force=True)`。

### 5. 模型和绑定门槛

阅读 `references/model-rig-and-pose-gate.md`：

- 无骨架：先规划骨架、绑定和权重。
- 有骨架：先检查坐标、父级、蒙皮和标准动作。
- 已扭曲：停止动画，调用人物修复 Skill。
- 大 morph 模型：先清理并保存资源可控的副本。

通过模型/姿态门槛后才制作正式分镜。

### 6. 校验分镜 CSV

主机端普通 Python 可运行：

```bash
python scripts/validate_shotlist.py \
  plans/shotlist.csv \
  --fps 24000/1001 \
  --report logs/shotlist_validation.json
```

原案例可额外检查 71 镜和 3512 帧：

```bash
python scripts/validate_shotlist.py \
  plans/shotlist.csv \
  --fps 24000/1001 \
  --expect-shots 71 \
  --expect-total 3512 \
  --report logs/shotlist_validation.json
```

`71` 和 `3512` 只是原案例，不是新项目默认值。

### 7. 创建相机并输出短段

```python
from maya_camera_tools import (
    create_shot_camera,
    keyframe_camera_move,
    playblast_shot,
)

camera = create_shot_camera(
    name="S001_CAM",
    eye=[120.0, 125.0, 180.0],
    aim=[0.0, 113.0, -105.0],
    focal_length=65.0,
)

keyframe_camera_move(
    camera,
    start=1,
    end=48,
    eye_start=[120.0, 125.0, 180.0],
    aim_start=[0.0, 113.0, -105.0],
    eye_end=[128.0, 126.0, 180.0],
    aim_end=[0.0, 113.0, -105.0],
)

result = playblast_shot(
    camera=camera,
    start=1,
    end=48,
    output_base="<项目路径>/frames/v01/raw/S001",
    width=854,
    height=480,
    off_screen=False,
)
```

始终使用 `create_shot_camera()` 返回的实际名称。默认使用可见主视口；离屏模式必须先通过黑帧和重复帧测试。

### 8. 核验连续图像序列

使用合并工具将 `<镜号>.<帧号>.png` 安全复制为连续数字帧，并校验源/目标哈希：

```bash
python scripts/merge_shot_sequences.py \
  --shotlist plans/shotlist.csv \
  --raw-dir frames/v01/raw \
  --output-dir frames/v01/continuous \
  --fps 24000/1001 \
  --report logs/merge_validation.json
```

然后运行：

```bash
python scripts/verify_image_sequence.py \
  frames/v01/continuous \
  --shotlist plans/shotlist.csv \
  --fps 24000/1001 \
  --width 854 --height 480 \
  --report logs/sequence_validation.json
```

该工具检查缺帧、数字帧名、每镜数量、总帧数、PNG 尺寸、重复帧和全片相同帧。它不能代替视觉审片。

### 9. 按验收门槛推进

```text
只读接入
→ 模型/绑定通过
→ 姿态四视图通过
→ 分镜与逐镜设计
→ 正式静帧
→ 相邻 5–6 镜短段
→ 复杂动作专项短段
→ 用户确认
→ 分批完成全部镜头
→ 保存后回读
→ 用户确认全片生产
→ 渲染、字幕、音轨、编码和最终验证
```

---

## English Quick Start

### 1. Clone

```bash
git clone https://github.com/SkipTopic/maya-sheng-animation.git
```

### 2. Provide inputs

Give the AI:

- Character paths, formats, skeleton/skin/morph status.
- Maya executable path and version.
- Maya MCP name, installation, or existing configuration.
- Reference video, images, shotlist, or written story.
- FPS, duration, resolution, and output directory.
- Allowed and forbidden actions: mouth, fingers, body, legs, props.
- Subtitle, original-audio, and full-render requirements.
- Memory, disk, network, and download constraints.

Fill `assets/project-brief-template.json`, `shotlist-template.csv`, and `shot-plan-template.json`. Never store tokens in the brief.

### 3. Install Maya MCP separately

The source project used:

```text
https://github.com/PatrickPalmer/MayaMCP
Version v0.2.0
```

Python 3.10+ is required by the upstream README:

```bash
git clone https://github.com/PatrickPalmer/MayaMCP.git
cd MayaMCP
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt  # Windows
```

Copy `assets/maya-mcp-config-template.json` into the client configuration structure, replace both absolute paths, and merge rather than overwrite other MCP servers.

For WorkBuddy, use `~/.workbuddy/mcp.json`, not `~/.workbuddy/.mcp.json`. Trust/enable the connector through the client. The upstream implementation uses local commandPort and does not require a Maya plugin.

Do not blindly select Allow All. Review the local source and code first.

### 4. Inspect Maya read-only

Run Maya scripts inside Maya:

```python
import sys
sys.path.insert(0, r"<actual-repository-path>/scripts")

from inspect_maya_project import inspect_project
report = inspect_project(
    joints=["Bip001Head"],
    output_path="<project-path>/logs/scene_audit.json",
)
```

Check unsaved work before any scene operation. Never begin with `scene_new(force=True)`.

### 5. Pass the model and rig gate

Read `references/model-rig-and-pose-gate.md`. Bind and test unrigged models before animation. Stop and use the pose-recovery Skill if the character is already distorted. Reduce large morph sets before production.

### 6. Validate the shotlist on the host

```bash
python scripts/validate_shotlist.py plans/shotlist.csv \
  --fps 24000/1001 --report logs/shotlist_validation.json
```

The source case used 71 shots and 3512 frames; those are not defaults for a new project.

### 7. Create cameras and render a short segment

Use `create_shot_camera`, `keyframe_camera_move`, and `playblast_shot` from `scripts/maya_camera_tools.py`. Always use the actual returned camera name. Start with `off_screen=False` and a visible, unobstructed production panel. Enable off-screen rendering only after black-frame and duplicate-frame tests pass.

### 8. Verify the continuous sequence

Merge per-shot files named `<shot>.<frame>.png` into a continuous numeric sequence and verify source/copy hashes:

```bash
python scripts/merge_shot_sequences.py --shotlist plans/shotlist.csv \
  --raw-dir frames/v01/raw --output-dir frames/v01/continuous \
  --fps 24000/1001 --report logs/merge_validation.json
```

Then run:

```bash
python scripts/verify_image_sequence.py frames/v01/continuous \
  --shotlist plans/shotlist.csv --fps 24000/1001 \
  --width 854 --height 480 --report logs/sequence_validation.json
```

The validator checks continuity, per-shot counts, dimensions, duplicates, and an all-identical sequence. Visual review is still required.

---

## Full Workflow / 全流程

| 阶段 / Stage | 必须产出 / Required evidence | 未通过时 / If not passed |
|---|---|---|
| 0. 任务简报 / Brief | 输入、范围、规格和确认点写入文件<br>Written brief and constraints | 不猜创作方向或动作范围<br>Ask instead of guessing |
| 1. Maya/MCP 接入 / Connection | 版本、路径、工具列表、只读查询<br>Read-only connection evidence | 排查进程、端口和弹窗<br>Fix connection first |
| 2. 模型与绑定 / Model and rig | 网格、骨架、权重、标准测试姿态<br>Model/rig audit and test poses | 修复或重新绑定，不做动画<br>Repair before animation |
| 3. 场景与姿态 / Scene and pose | 四视图、接触检查、保存后回读<br>Pose images and reopened-scene checks | 调用人物修复 Skill<br>Use pose recovery |
| 4. 分镜 / Storyboard | 连续帧范围、主体、台词、动作、运镜<br>Validated shotlist | 修正缺口、重叠和识别错误<br>Fix the plan |
| 5. 相机 / Cameras | 轴线、前景、焦距、起止 eye/aim、真实名称<br>Camera evidence | 不用随机机位凑数<br>No random camera filler |
| 6. 动作 / Performance | 头部、手部、道具、动作范围和关键帧<br>Action evidence | 简化或请求扩大范围<br>Simplify or ask |
| 7. 静帧与短段 / Review | 正式静帧、相邻短段、复杂动作短段<br>Still and clip review | 回到对应阶段，不渲全片<br>Do not render the full film |
| 8. 生产与编码 / Production | 每镜帧数、总序列、字幕、音轨、ffprobe<br>Sequence and encoding validation | 修复输出，不伪造完成<br>Fix before delivery |
| 9. 备份交接 / Handoff | 当前场景、日志、报告、SHA-256、遗留问题<br>Backup and handoff evidence | 标记进行中/待验收<br>Mark incomplete honestly |

---

## Failure Catalog / 真实问题与解决方案

以下故障均来自原项目、历史交接或本仓库工具自测。每一行同时提供中英文。  
These failures come from the source project, historical handoffs, or this repository's own tests. Every row is bilingual.

### A. MCP、Maya 与执行通道 / MCP, Maya, and execution

| 问题 / Problem | 如何遇到 / How it happened | 解决与预防 / Fix and prevention |
|---|---|---|
| **MCP 执行但无回传**<br>MCP executed without returning results | 启动钩子的 `echoOutput=False` 关闭了回传。<br>Output echo was disabled. | 核对 commandPort 和客户端读取逻辑，先做只读查询。<br>Verify commandPort and protocol handling with read-only calls. |
| **SafeMode 阻止 Python 文件操作**<br>SafeMode blocked Python I/O | `open/eval/exec/io.open` 失败，自动化无法读写。<br>Python I/O and exec failed. | 审核来源，使用可信本地通道；不把全局关闭安全当成默认。<br>Use audited local execution; do not disable security by default. |
| **响应终止符不匹配**<br>Response terminator mismatch | 回传以 `\n\x00` 结束，旧客户端只等 `\n`。<br>The client expected a different terminator. | 修协议读取，不把等待超时误判为 Maya 姿态问题。<br>Fix protocol handling before scene debugging. |
| **执行与结果读取各弹一次警告**<br>Execute and result-read each triggered a warning | 第一次允许后，第二个请求仍阻塞。<br>The second request remained blocked. | 检查所有模态窗口，不连续重试堆积请求。<br>Inspect all modal dialogs and avoid retry stacking. |
| **Connection refused / WinError 10061** | Maya 进程已退出，命令仍在队列等待。<br>Maya had exited while commands remained queued. | 重启 Maya、检查队列、做只读测试、打开最近确认版本。<br>Restart, inspect pending commands, test, and reopen the accepted scene. |
| **mayabatch/mayapy 本机崩溃**<br>Batch interpreters crashed | 非 GUI 自动化多次失败。<br>Non-GUI automation repeatedly failed. | 使用已启动的 Maya GUI；不要反复切换解释器碰运气。<br>Use the running GUI instead of repeated interpreter switches. |
| **自动更新破坏已验证环境的风险**<br>Automatic updates could break the working setup | 项目依赖特定 MCP、Maya 和脚本行为。<br>The project depends on tested versions and behavior. | 固定已验证版本，更新前备份并重新跑自测。<br>Pin the working setup and retest before updates. |

### B. 模型、绑定和姿态 / Model, rig, and pose

| 问题 / Problem | 如何遇到 / How it happened | 解决与预防 / Fix and prevention |
|---|---|---|
| **自动绑骨后立即做动画导致扭曲**<br>Animating immediately after rigging caused distortion | 没有分别验收骨架、权重和目标动作。<br>Rigging and target performance were not tested separately. | 将绑定和动画拆成两个门槛，先跑标准姿态。<br>Separate rigging and animation gates with standard test poses. |
| **重命名/重父级破坏蒙皮**<br>Rename/reparent operations broke skinning | 转换后修改层级、网格和骨架关系。<br>Import hierarchy was rewritten unsafely. | 从干净模型恢复，保留蒙皮网格父级。<br>Restore from a clean model and preserve mesh parenting. |
| **局部 Spine 小角度被误当世界直立**<br>Small local Spine angles were mistaken for an upright world pose | 实测局部 1.5° 对应世界约 42.29°，另一处 6° 对应约 46.6°。<br>Local and world values contradicted the assumption. | 用世界 Spine→Head 向量和世界矩阵诊断。<br>Measure world vectors and matrices. |
| **清零关节破坏非零中立姿态**<br>Zeroing joints destroyed the rest rig | FBX/MMD 有合法非零旋转、镜像和坐标转换。<br>The imported rig had non-zero rest transforms. | 从同一原始模型恢复中立数据。<br>Restore rest data from the same original model. |
| **旧 MMD 大角度弯臂破袖**<br>Old MMD cuffs tore during large bends | SDEF 辅助结构和分层袖壳在目标动作下穿插变黑。<br>The old SDEF/layered structure failed at the target bend. | 减少动作或更换模型，不用 Delta Mush 掩盖。<br>Simplify motion or replace the model; do not hide it with Delta Mush. |
| **高迭代 Delta Mush 增加内存**<br>High-iteration Delta Mush increased memory use | 参数尝试没有修好破袖，峰值约增加 2GB。<br>Parameters did not fix the cuff and consumed about 2GB. | 停止无效平滑，回到蒙皮/动作范围根因。<br>Stop ineffective smoothing and address the structural cause. |
| **完整 morph 导入卡死**<br>Full morph import stalled Maya | 新模型约 149 份 morph、合计约 426 万顶点，机器约 8GB 内存。<br>About 149 morphs and 4.26M vertices on an 8GB machine. | 使用清理过表情的单身体网格副本。<br>Use a validated body-only copy. |
| **IK 手柄到达但末端不动**<br>IK handle reached the target while the end joint did not | 手柄位置正确，脚踝仍停留旧位置。<br>The handle matched while the ankle remained wrong. | 使用显式两段 IK，读取实际末端和中间关节。<br>Use explicit two-bone IK and measure actual joints. |
| **四元数乘法顺序错误**<br>Wrong quaternion multiplication order | 世界增量左乘导致人物偏侧。<br>Left multiplication twisted the character. | Maya 行向量约定使用 `old_q * delta`，并在非单位父级下测试。<br>Right-multiply and test under rotated parents. |
| **修改髋部后手臂重新穿桌**<br>Changing hip height reintroduced table intersections | v4 为 0；v5 改髋部后马县长出现 78 个桌面内部顶点。<br>A body-height change altered the arm path. | 全身接触重新验收，不只检查被改部位。<br>Revalidate the full body after each pose change. |
| **抬高肘极点反而增加穿插**<br>Raising the elbow pole increased intersections | v6 桌面内部顶点增至 322。<br>The change increased interior vertices to 322. | 收近手腕并降低外侧极点；v7 回到 0。<br>Move the wrist nearer the edge and lower the outward pole. |

### C. 分镜和相机 / Storyboard and cameras

| 问题 / Problem | 如何遇到 / How it happened | 解决与预防 / Fix and prevention |
|---|---|---|
| **71 台相机只有 12 种位置/朝向**<br>Seventy-one cameras had only twelve unique transforms | 旧生成器只按主体、景别和左右移动生成，最大重复组 18 次。<br>The generator ignored narrative continuity. | 逐镜读取前景、视线、轴线和承接。<br>Design foreground, gaze, axis, and continuity per shot. |
| **前景人物要求没有进入画面**<br>Required foreground characters were absent | S003/S004 等需要前景头肩，旧逻辑只拍单人居中。<br>The old logic produced centered single-person shots. | 检查投影和运镜起止帧，不只在文档里写前景。<br>Verify projected foreground at both endpoints. |
| **动作文本第一个人名不等于说话者**<br>The first name in an action description was not always the speaker | 镜头外台词和反应镜头被启发式识别错误。<br>Off-screen dialogue broke the heuristic. | 看原片，分别记录主体、说话者和听者。<br>Record subject, speaker, and listener from the reference. |
| **未处理 180° 轴线**<br>The 180-degree axis was not handled | 只围绕人物计算方位，没有检查相邻镜头视线。<br>No relational axis or eyeline continuity was checked. | 建立对话关系轴，并用相邻短段验收。<br>Define the axis and review adjacent clips. |
| **相机名自动带后缀**<br>Maya appended camera-name suffixes | 后续脚本仍使用未带后缀的名称。<br>Scripts used the requested rather than actual name. | 使用 `cmds.camera()` 返回值并保存映射。<br>Use returned names and save a camera map. |
| **modelEditor 设置相机静默留下旧视口**<br>modelEditor silently left the old camera active | 文件生成但画面重复，未实际切换。<br>Images were produced from the old view. | 对可见生产面板执行 `lookThru` 并查询当前相机。<br>Use lookThru and query the active panel camera. |
| **离屏 playblast 在默认四视图下输出黑帧**<br>Off-screen playblast produced black frames in the four-panel layout | 本仓库自测首版 3 帧数量正确，但哈希相同且图像全黑。<br>The first camera test returned three identical black images. | 改为可见 `modelPanel4`、主视口和 `off_screen=False`；重测 3 帧非黑且哈希不同。<br>Use the visible main panel; the corrected test passed with three distinct images. |
| **四视图取景裁掉头部**<br>Review framing clipped the head | 把含落座补偿的组 Y 当成人物中心。<br>The compensated group origin was used as the body center. | 根据实际人物骨骼和包围盒取景。<br>Frame evaluated geometry and joints. |

### D. 动作、道具和范围 / Performance, props, and scope

| 问题 / Problem | 如何遇到 / How it happened | 解决与预防 / Fix and prevention |
|---|---|---|
| **统一转头/前倾模板冒充表演**<br>A repeated turn/lean template was presented as acting | 每镜使用固定角度，没有按台词和视线设计。<br>Every shot reused fixed angles. | 按剧情设置目标、停顿和幅度，禁止 root 摇摆替代。<br>Use narrative targets and holds; avoid root-sway substitutes. |
| **只做头手的许可被分镜身体描述冲淡**<br>A head-and-hand-only scope conflicted with body actions in the shotlist | 站起、坐回、前倾等描述需要身体/腿部动画。<br>Some shots requested standing or leaning. | 标记未执行并向用户确认，不自动扩大范围。<br>Mark these actions as not executed and ask before expanding scope. |
| **场景道具数量不足以支持剧情**<br>The scene lacked enough props for the described action | 原场景只有 1 杯、1 瓶、1 碗，却有碰杯/倒酒等动作。<br>One cup/bottle/bowl existed despite multi-character actions. | 先核对道具，必要时复制并做绑定/接触验收。<br>Audit, duplicate if approved, bind, and validate contact. |
| **只移动手腕不代表拿杯完成**<br>Moving a wrist did not move the cup | 没有保持世界位置的道具绑定。<br>No world-preserving prop binding existed. | 明确绑定驱动关系，检查切镜前后和桌面接触。<br>Bind explicitly and verify cuts and contact. |
| **手指和嘴型被默认加入的风险**<br>Unrequested finger and mouth animation could be added | 模型有手指骨和 blendShape，但用户可能禁止这些动作。<br>The rig had channels the user might forbid. | 将允许、禁止、待确认动作写入任务简报并检查动画节点。<br>Record scope and audit animated nodes. |

### E. 渲染、字幕、音轨和编码 / Rendering, subtitles, audio, and encoding

| 问题 / Problem | 如何遇到 / How it happened | 解决与预防 / Fix and prevention |
|---|---|---|
| **`frame=[f0,f1]` 只渲两帧**<br>A two-item frame argument rendered only two frames | 把帧列表误当成连续区间。<br>A frame list was mistaken for a range. | 使用正确 startTime/endTime 或完整 frame 列表，并立即核对数量。<br>Use proper ranges and verify counts immediately. |
| **旧帧目录混入新输出**<br>Old frame directories contaminated new output | 多版渲染复用相同目录。<br>Versions shared directories. | 每个版本使用新目录，不默认删除旧证据。<br>Use new versioned directories. |
| **字符串排序和截断隐藏序列错误**<br>String sorting and truncation hid sequence errors | 直接字符串排序，或用 `files[:3512]` 截断多余帧。<br>Extra frames were hidden by slicing. | 按数字帧号排序；数量错误必须查明，不得截断掩盖。<br>Sort numerically and investigate every mismatch. |
| **24fps 与原片 24000/1001 不一致**<br>Twenty-four fps did not match the 23.976 source | 旧编码脚本写死 `-framerate 24`。<br>The old encoder hard-coded 24fps. | Maya 打键前和编码时都确认时间基；使用 `24000/1001`。<br>Set and verify the timebase in Maya and ffmpeg. |
| **字幕压在浅色道具上难读**<br>Subtitles became unreadable over bright props | 白字和小描边覆盖白色碗碟。<br>White text overlapped bright objects. | 使用半透明底板或合适描边，改变分辨率时重新排版。<br>Use a backing plate/stroke and re-layout for the target resolution. |
| **音轨说明和真实文件不一致的风险**<br>Audio notes could contradict the actual source | 旧交付曾写无音轨；原片信息需要重新用 ffprobe 核实。<br>Historical notes required re-verification. | 不凭旧说明判断；检查源和成片音频流、时长和同步。<br>Probe both source and output audio streams and timing. |
| **幻想/缺失镜头没有明确标注**<br>Fantasy or missing shots were not marked | 旧流程把占位段混入普通宴会画面。<br>Placeholders looked like ordinary scene footage. | 按分镜使用黑场、镜号、剪影或批准的替代形式。<br>Use the approved placeholder treatment. |
| **未确认短段就渲全片**<br>The full film was rendered before short-segment approval | 只追求帧数，问题到全片才暴露。<br>Failures were discovered only after full production. | 静帧、相邻短段和复杂动作短段通过后才能渲全片。<br>Require still and clip approval before full rendering. |

### F. 验收、备份和交接 / Acceptance, backup, and handoff

| 问题 / Problem | 如何遇到 / How it happened | 解决与预防 / Fix and prevention |
|---|---|---|
| **8/8 PASS 仍是空镜/错误画面**<br>An 8/8 PASS report still represented unusable footage | 漏掉静止图、人物可见性、穿模和闪面。<br>The report omitted critical visual checks. | 区分节点存在、参数正确、渲染生效和视觉通过。<br>Separate existence, parameters, render activation, and visual acceptance. |
| **保存后节点或相机未按预期存在**<br>Saved scenes did not always preserve expected state | 只检查内存状态，没有重开文件。<br>Only in-memory state was checked. | 另存、重开、重算指标并重新出图。<br>Save, reopen, recompute, and rerender. |
| **中间试验版被误当最终版**<br>Intermediate experiments could be mistaken for final scenes | 文件名和版本很多，旧文档结论混杂。<br>Versions and historical notes were mixed. | 标记当前唯一有效版本，v1–v6 只作诊断，保留失败记录。<br>Mark the current valid version and retain rejected approaches as diagnostics. |
| **备份后修改文档导致哈希过期**<br>Editing documents after backup invalidated hashes | 备份完成后又追加交接内容。<br>Handoff notes changed after copying. | 同步更新文档副本、manifest 和 SHA-256，再复算。<br>Resynchronize documents and recompute hashes. |
| **路径和凭据影响迁移/安全**<br>Paths and credentials could break portability or leak secrets | 脚本含原项目绝对路径；MCP 配置可能含敏感信息。<br>Scripts and MCP configs can contain environment-specific data. | 迁移时修改 ROOT/SCRIPTS；不上传令牌、密码或完整全局配置。<br>Update paths during migration and exclude credentials. |

---

### G. 后续独立审计补充 / Additional independent audit findings

| 问题 / Problem | 如何遇到 / How it happened | 解决与预防 / Fix and prevention |
|---|---|---|
| **胶片孔径单位换算错误**<br>Film aperture was converted with the wrong unit | 近景比对中脸部比例不对；Maya 的胶片孔径使用英寸，曾被当成毫米。<br>Maya aperture was treated as millimetres instead of inches. | 显式处理英寸与毫米，做渲染对比，不仅核对镜头 mm 数。<br>Handle inch/mm conversion explicitly and compare rendered framing. |
| **场景有灯光但渲染未启用**<br>Lights existed but were not used by the viewport render | `displayLights=default`、`shadows=False`，亮度和明暗层次没有生效。<br>Default viewport lighting bypassed the intended lights and shadows. | 检查实际视口灯光、阴影和渲染设置，再比较原片。<br>Verify active lighting/shadows in rendered evidence. |
| **材质槽猜色与 UV 误判**<br>Material colours were guessed and UVs were misclassified | 无贴图材质槽无语义；裙甲 UV 被错误归类。<br>Untextured slots lacked semantics and armor UVs were misclassified. | 将配色和 UV 作为独立视觉任务，不声称模型贴图已恢复。<br>Treat colour and UV as separate visual tasks. |
| **旧成片帧数出现 3513/3512 偏差**<br>An old delivery had a 3513-versus-3512 discrepancy | 分镜总量、图像序列和 ffprobe 的 nb_frames 不一致。<br>Shot totals, sequence files, and ffprobe disagreed. | 同时核对每镜数量、全局序列、编码帧数和容器信息。<br>Cross-check per-shot, sequence, encoded, and container counts. |
| **生产场景出现集中黑帧**<br>A production scene produced a concentrated black-frame block | 后续 v03 曾在 S061–S064 出现 86 张黑帧，相邻静止帧却正常。<br>Later v03 logs recorded 86 black frames while nearby static frames were valid. | 将黑帧作为生产阻塞问题，不靠补图和日志掩盖；后续版本必须重新验证。<br>Block delivery on black frames and retest every later version. |
| **检测日志与真实输出矛盾**<br>Detection logs contradicted the real output | 同一目录曾同时出现 84 黑帧和 0 黑帧的报告；新证据目录还存在硬编码检测数量。<br>One directory had conflicting reports and hard-coded detection counts. | 检测必须读取当前实际帧，记录工具版本、参数和哈希。<br>Measure actual current frames and record tool version, arguments, and hashes. |
| **景深被用来遮掉手或网格问题**<br>Depth of field was used to hide hands or mesh issues | 小景深的头手检查会让真实穿插更难发现。<br>Shallow DOF obscured actual hand/mesh problems. | 验收时关闭遮挡性 DOF；创作 DOF 只能在验收后使用。<br>Review without obscuring DOF; add creative DOF only afterward. |
| **逐帧 currentTime 烘焙极慢**<br>Per-frame currentTime baking was extremely slow | 长分段曾耗费约 25 分钟，而批量关键点路径快得多。<br>A long segment took about 25 minutes versus a much faster batch-key path. | 比较烘焙方法，选择可验证的批量关键帧路径并抽帧核对。<br>Benchmark safe batch keying and verify sampled output. |
| **OCR/文本分镜与原片动作不一致**<br>OCR/text shot data diverged from the reference | S001–S012 的运镜曾被文本写成实际为静止的镜头；S056 也对不上。<br>Text described motion where the reference was static. | 文本表必须通过原片逐镜校验；相机运动和动作以真实帧为准。<br>Validate shot text against actual reference frames. |
| **黑帧检测被字幕边缘干扰**<br>Black-frame detection was affected by subtitle edges | 字幕区域改变了画面检测，可能掩盖真实黑帧。<br>Subtitle regions interfered with the detector. | 先审无字幕画面，再单独验证字幕；不依赖单一阈值。<br>Review picture without subtitles and validate subtitles separately. |
| **角色外观和场景简化不能被当作一比一还原**<br>Character/set simplifications were not one-to-one replication | 人物并非原演员形象，材质、道具和背景也有简化。<br>Characters, materials, props, and sets were simplified. | 在交付说明中明确风格化/简化范围，不夸大复刻度。<br>Document stylisation and simplification honestly. |
| **“批量渲染不可用”等绝对结论被后续实测推翻**<br>Absolute claims such as "batch rendering is impossible" were later disproved | 后续记录表明显示 Arnold 单帧和批量序列可以完成。<br>Later Arnold single-frame and batch-sequence tests succeeded. | 将失败限定到具体版本、工具和条件；不要泛化为永久不可行。<br>Scope failures to exact versions and conditions. |

这些补充用于防止旧文档中的绝对结论再次误导新 AI。它们不改变本仓库当前工具自测的有效范围。  
These additions prevent obsolete absolute claims from misleading a new AI. They do not expand the proven scope of this repository's current tool tests.

---

## Validation / 测试与跨 AI 可运行性

### 已执行的实际测试 / Tests actually executed

1. **Python 严格语法检查**<br>Seven Python files passed strict parsing.<br>7 个 Python 脚本通过严格语法检查。
2. **主机端工具自测**<br>Shotlist validation, per-shot merge, source/copy hashes, and continuous PNG verification passed on generated test data, including repeated-first-frame and cut-boundary checks.<br>分镜验证、逐镜合并、源/副本哈希和连续 PNG 验证在生成测试数据上通过，并覆盖重复首帧与切镜边界检查。
3. **真实分镜表验证**<br>The source shotlist passed at 24000/1001: 71 shots, frames 1–3512, no gaps or overlaps, no warnings.<br>真实 shotlist 在 24000/1001 下通过：71 镜、1–3512、无缺口、无重叠、无警告。
4. **Maya 只读审计**<br>The scene inspection script ran in Maya 2024 and produced a structured report.<br>只读审计脚本已在 Maya 2024 实际运行并生成报告。
5. **Maya 相机实测**<br>The corrected visible-panel test produced three non-black frames with three distinct hashes and correct frame count.<br>修正后的可见视口测试输出 3 张非黑图像，数量正确且哈希均不同。
6. **临时节点清理**<br>No temporary aim helpers remained after the camera test.<br>相机自测后无临时瞄准节点残留。
7. **官方 Skill 校验与 ZIP**<br>Official validation and packaging passed; ZIP CRC verification passed.<br>官方校验、打包和 ZIP CRC 检查通过。

证据位于 `tests/`。这些测试证明工具和流程具有可执行起点，**不代表任何新项目的整段动画已经自动验收**。  
Evidence is in `tests/`. These tests prove the tools run; they do not mean a new project's full animation has already been accepted.

### 另一个 AI 能否真正跑通 / Can another AI run it?

可以按仓库跑通工具和制作流程，但必须满足以下条件：

- 安装并运行 Maya；Maya 脚本在 Maya 内执行。
- 单独安装/配置 MCP，或使用审核过的本地执行通道。
- 把 `scripts/` 加入 Maya `sys.path`。
- 提供模型、参考、动作范围和输出规格。
- 替换示例骨名、坐标、帧数和分辨率。
- 按阶段门槛执行，不跳过模型/姿态验收。
- 使用真实相机名和可见生产面板。
- 将逐镜原始帧整理为连续数字帧后运行序列验证。
- 保存后重开场景，生成静帧和短段并交给用户确认。
- 未经确认，不直接渲染全片。

A new AI can run the tools and follow the workflow, but it must satisfy these prerequisites. The repository is not a standalone Maya executable, MCP server, auto-rigging guarantee, or substitute for creative review.

### 已知限制 / Known limitations

- Maya MCP 不包含在仓库中。<br>Maya MCP is not bundled.
- 自动绑定没有“一键适用所有拓扑”的保证。<br>There is no universal one-click auto-rig guarantee.
- 原项目的固定骨名、人物坐标和 71 镜参数不能直接复用。<br>Source-case names, coordinates, and shot counts are not portable defaults.
- playblast 依赖实际视口状态，黑帧/缓存检查不可省略。<br>Playblast depends on viewport state; black-frame/cache checks are mandatory.
- 数值验证不能代替视觉、动作节奏和音画同步检查。<br>Numeric checks do not replace visual, performance, or audio review.
- 最终全片需要用户明确确认。<br>Full rendering requires explicit user approval.

---

## Security / 安全

- 不保存 GitHub 令牌、MCP 凭据或其他秘密。<br>Never commit GitHub tokens, MCP credentials, or secrets.
- 不自动下载安装或更新 MCP。<br>Do not automatically download, install, or update MCP.
- 不默认全局允许 MCP 代码，不开放公共网络端口。<br>Do not blindly allow all MCP code or expose public network ports.
- 修改前备份场景和 MCP 配置。<br>Back up scenes and MCP configuration before editing.
- 所有生产修改使用版本化文件和新输出目录。<br>Use versioned scenes and new output directories.

**先读 `SKILL.md`，按阶段加载 references；不要只浏览 README 就宣称完成。**  
**Read `SKILL.md`, load references by stage, and do not claim completion merely from reading this README.**
