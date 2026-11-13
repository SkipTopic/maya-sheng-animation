---
name: maya-sheng-animation
description: "This skill should be used when an AI needs to control Autodesk Maya through Maya MCP to turn a supplied character model and optional film/reference video into a reviewed animation. 覆盖 Maya/MCP 环境检查、人物模型与绑定验收、场景和姿态、分镜表、相机调度、头部/手部/道具动作、静帧与短段确认、playblast 序列、字幕音轨、编码验证、备份和交接。中文显示名称：玛雅生动画。"
agent_created: true
---

# 玛雅生动画：AI 控制 Maya 制作动画的全流程

## 目标

将人物模型、Maya 可执行文件路径、Maya MCP 配置和用户创意需求转化为可编辑、可复核、可继续接手的 Maya 动画项目。按阶段证明模型、绑定、姿态、分镜、相机、动作和最终序列真正生效，不把脚本执行成功当成视觉完成。

本 Skill 不包含 Maya 或 Maya MCP 本体，不自动下载安装，也不替用户决定是否扩大动画范围或直接渲染全片。

## 使用场景

在以下任务中使用：

- 提供人物模型，要求 AI 检查、绑定/修骨架并制作 Maya 动画。
- 提供电影片段、剧集片段、分镜表或文字剧情，要求复刻人物调度、景别、前后景和相机运动。
- 需要通过 Maya MCP 控制现有 Maya GUI，完成场景、相机、动作、试渲和交付。
- 需要排查“人物扭曲、相机关联失效、动画不入画、序列数量不对、旧帧混入”等全流程问题。

不要将其当作无骨架模型的通用一键自动绑定器。缺少骨架或蒙皮时，先进入绑定与权重验收阶段；已有修复后仍扭曲时，调用配套 `maya-character-pose-recovery` Skill。

## 必须向用户收集的输入

1. 人物模型路径和格式；是否带骨架、蒙皮、材质、贴图、morph/表情。
2. Maya 可执行文件完整路径和版本。
3. Maya MCP 名称、安装位置或现有连接方式；若未安装，参考 `references/maya-mcp-setup.md`。
4. 动画目标：原创、参考复刻、指定分镜或文字剧情。
5. 参考视频/图片、台词、目标时长、分辨率和帧率。
6. 允许和禁止的动作范围，尤其嘴型、手指、躯干、腿部和道具动作。
7. 输出目录、渲染方式、是否需要音轨/字幕，以及哪些节点需要用户确认。
8. 机器内存和可用磁盘；大型模型或长序列先估算资源。

信息不全时先检查已有项目；涉及创作方向、动作范围、发布或全片渲染的缺失信息再询问用户。

## 不可跳过的安全规则

- 保留原始模型和用户场景，所有修改另存为新版本。
- 不改变蒙皮网格父级来补偿骨架问题。
- 不清零整套关节；保留合法的非零中立姿态和坐标/单位转换。
- 不把局部欧拉角当成世界空间姿态。
- 不把 IK 手柄位置当成末端关节位置。
- 不用 Delta Mush、隐藏模型或随机相机扰动掩盖未定位的问题。
- 不把旧参考帧、旧相机缓存或旧输出目录混入新版本。
- 不在静帧和短段未确认时渲染全片。
- 不执行来源不明的 MCP Python 代码，不全局放开安全警告，不开放远程命令端口。
- 不在日志、备份或 Skill 中写入 MCP 凭据、账号令牌或其他秘密。

## 全流程阶段与门槛

### 阶段 0：建立任务简报和项目目录

创建独立项目目录和版本化子目录：

```text
scenes/             # 原始基线、工作版、验收版、生产版
references/         # 原片、抽帧和文字参考
plans/              # 分镜表、机位和动作设计
scripts/            # 当前项目脚本
logs/               # 执行日志和保存后回读
previews/           # 静帧、短段和对比图
frames/             # 按版本分开的序列
delivery/           # 最终成片和验证报告
backups/            # 用户确认后的阶段备份
```

写入任务简报，不得只依赖对话记忆。使用 `assets/project-brief-template.json`。

### 阶段 1：检查 Maya 和 MCP

读取 `references/maya-mcp-setup.md`。

- 核对 Maya 路径、版本、进程和当前场景修改状态。
- 核对 MCP 客户端配置、虚拟环境、服务脚本和工具列表。
- 先执行只读查询，再执行创建/修改。
- 处理 `connection refused`、安全警告和模态对话框，不持续重试同一请求。
- MCP 不可用时使用项目已有的可信本地执行通道；没有通道时先建立并审核，不伪造已连接状态。

### 阶段 2：检查人物模型、绑定和动画适用性

读取 `references/model-rig-and-pose-gate.md`。

- 检查网格、骨架、蒙皮、权重、材质、贴图、morph、单位和坐标系。
- 检查头、颈、脊椎、肩、肘、腕、髋、膝、踝和手指骨。
- 区分“模型可显示”和“模型可做目标动作”。
- 做小幅标准测试姿态，检查袖口、肩部、膝盖和脚底。
- 模型扭曲时停止动画，使用配套人物修复 Skill；不要带着坏姿态进入分镜和渲染。

### 阶段 3：搭建场景和可信姿态基线

- 设置 cm/m、时间单位、播放范围和参考帧率。
- 按参考确定桌椅、地面、道具、人物位置和朝向。
- 保存人物中立/落座/手部基准及世界矩阵。
- 输出正面、左侧、右侧、俯视和接触区域图。
- 保存后重新打开并复核。

### 阶段 4：建立分镜和逐镜设计

读取 `references/storyboard-and-camera-direction.md`。

复制 `assets/shotlist-template.csv` 和 `assets/shot-plan-template.json`，填写：

- 镜号、首尾帧、时长、景别、主体、说话者、听者。
- 动作、台词、前景人物、运镜、参考帧。
- 相机起止位置/瞄准点、焦距、180° 轴线。
- 头部、手部、道具动作和验收状态。

运行 `scripts/validate_shotlist.py` 检查连续性、重复、缺口、时长和帧范围。不要只按动作文本第一个人名推断说话者。

### 阶段 5：先做正式静帧和相邻短段

- 输出主要人物正式近景。
- 输出包含明确前景人物的镜头。
- 选择相邻 5–6 镜制作短段，检查正反打、切镜、视线、动作和运镜。
- 对复杂道具、站起/坐回或特殊动作另做专项测试。
- 将静帧和短段交给用户确认，未通过则回到对应阶段，不在坏画面上继续加产量。

### 阶段 6：制作头部、手部和道具动作

读取 `references/animation-props-and-performance.md`。

- 以验收姿态为基准，按剧情制作转头、点头、停顿和手势。
- 不套用统一幅度、统一首中尾模板或 root 摇摆。
- 需要两段 IK 时显式指定 start/middle/end，并验证实际末端。
- 检查道具数量、绑定、接触和切镜连续性。
- 只有头部/手部许可时，不自行加入站起、腿部或大幅躯干动画。

### 阶段 7：完成全部镜头并做生产验收

- 分批保存版本，每批重新打开检查。
- 确认每台相机真实存在、被实际使用且构图正确。
- 确认每镜帧数、相机起止关键帧和动作范围。
- 检查不同镜头不是无理由重复，图像不是相同缓存。
- 生成镜头映射、逐镜验收图和剩余问题清单。

### 阶段 8：用户确认后渲染和交付

读取 `references/render-encode-and-delivery.md`。

- 使用新版本生产场景和全新帧目录。
- 逐镜 playblast，立即核对 `end-start+1`。
- 运行 `scripts/verify_image_sequence.py` 检查总帧数、缺帧、重复和数字顺序。
- 最后添加字幕和确认过的音轨。
- 编码后核对帧率、宽高、帧数、时长、音轨、切点和关键动作抽帧。
- 交付 Maya 场景、镜头/动作设计、成片、验证报告和备份。

### 阶段 9：交接和恢复

阅读 `references/recovery-and-handoff.md`。只追加台账，记录实际文件、验证证据和未完成项。备份用户确认过的阶段，不把中间试验版标成最终版。

## 工具和资源索引

| 资源 | 用途 |
|---|---|
| `references/maya-mcp-setup.md` | Maya MCP 选择、安装、配置、连接和安全 |
| `references/model-rig-and-pose-gate.md` | 模型、绑定、权重、姿态和修复门槛 |
| `references/storyboard-and-camera-direction.md` | 分镜、前后景、轴线、运镜和视口证据 |
| `references/animation-props-and-performance.md` | 头部、手部、道具和动作范围 |
| `references/render-encode-and-delivery.md` | 序列、字幕、音轨、编码和最终验证 |
| `references/recovery-and-handoff.md` | 弹窗、崩溃、缓存、备份和接续 |
| `references/case-derived-rules.md` | 从真实项目失败中提炼的强制规则 |
| `scripts/inspect_maya_project.py` | 只读 Maya 场景和模型检查 |
| `scripts/maya_camera_tools.py` | 相机创建、运动关键帧、面板切换和逐镜 playblast |
| `scripts/validate_shotlist.py` | 分镜 CSV 结构和帧连续性验证 |
| `scripts/verify_image_sequence.py` | 序列缺帧、重复和每镜数量验证 |
| `assets/maya-mcp-config-template.json` | Maya MCP stdio 配置模板，不含凭据 |
| `assets/project-brief-template.json` | 用户需求和交付规格模板 |
| `assets/shotlist-template.csv` | 分镜表模板 |
| `assets/shot-plan-template.json` | 逐镜相机和动作设计模板 |

## 与人物修复 Skill 的协作

本流程在模型/姿态门槛失败时停止推进，并调用：

```text
maya-character-pose-recovery
```

在当前示例项目中，它位于：

```text
C:\Users\admin\Desktop\MayaProject\解决人物模型的 Skill\maya-character-pose-recovery
```

该路径只是当前项目示例，不是全流程 Skill 的硬编码依赖。迁移时使用单独分发的配套 Skill，不把绝对路径写进新用户的项目。

## 完成定义

只有模型、绑定、姿态、分镜、相机、动作、序列和编码均有相应证据，且用户已确认静帧/短段和最终生产范围，才可报告动画任务完成。任何阶段未完成，都明确标记为“进行中”“待验收”或“未开始”。