# 渲染、序列、字幕、音轨和交付

## 1. 渲染前必须具备的确认

- 模型/绑定和初始姿态已通过。
- 正式静帧已通过。
- 相邻短段和复杂动作短段已通过。
- 用户确认进入全片生产。
- 分辨率、帧率、音轨、字幕和输出目录已确认。
- 生产场景已经另存，不覆盖基线或验收版。

任何一项缺失，都停留在预览阶段。

## 2. 新版本使用新目录

```text
frames/<version>/raw/
frames/<version>/continuous/
frames/<version>/subtitled/
previews/<version>/
delivery/<version>/
```

不得混用旧项目的 `frames_raw3`、`frames_all3` 或其他历史目录。渲染前检查目录是否已有文件；不要默认删除，优先创建新版本目录。

## 3. 逐镜 playblast

使用 `scripts/maya_camera_tools.py` 中的 `playblast_shot()`：

```python
result = playblast_shot(
    camera=camera_map["S003"],
    start=104,
    end=193,
    output_base=r"<项目>/frames/v01/raw/S003",
    width=854,
    height=480,
)
```

要求：

- 使用真实相机名。
- 默认使用可见且未被遮挡的主透视面板和 `lookThru`；离屏 playblast 必须先通过黑帧/重复帧测试。
- 多视图同时可见时显式选择生产面板，不要默认取列表第一个。
- `clearCache=True`、`viewer=False`、`showOrnaments=False`。
- 每镜立即检查 `end-start+1` 个文件。
- 预热帧单独输出，不进入正式序列。
- 保存日志，记录实际相机、帧范围和输出。

## 4. 帧范围陷阱

```python
frame=[f0, f1]
```

只表示首末两个帧，不是连续区间。使用正确的 `startTime/endTime`，或显式传完整帧列表。

不得：

- 只检查脚本是否报错。
- 只看目录里是否有 PNG。
- 用 `files[:expected_total]` 截断多余帧。
- 用字符串排序代替数字帧号排序。

## 5. 连续序列核验

将每镜帧按镜号和数字帧号整理为连续序列后运行：

```bash
python scripts/verify_image_sequence.py \
  frames/v01/continuous \
  --shotlist plans/shotlist.csv \
  --report logs/sequence_validation.json
```

可添加预期宽高：

```bash
--width 854 --height 480
```

检查：

- 缺失帧。
- 非数字帧名。
- 每镜实际数量。
- 总帧数。
- PNG 尺寸。
- 相同哈希帧组。
- 全片是否所有帧完全相同。

静态镜头可以有相同帧，不能仅因重复帧就判错；但全片相同、跨所有切镜相同或所有镜头首帧相同必须报警。

## 6. 帧率

常见原片为 `24000/1001`。如果原片如此：

- Maya 在打键前设置为 23.976fps。
- 图像序列编码使用：

```bash
-framerate 24000/1001 -start_number 1
```

不要沿用写死 24fps 的旧脚本。不要只改容器帧率而不检查动画时间轴。

## 7. 字幕

- 字幕在画面和剪辑确认后最后添加。
- 字幕文本和帧范围来自当前分镜表。
- 改变分辨率时重新排版和生成。
- 检查白字在浅色背景上的可读性，必要时加半透明底板或描边。
- 不做嘴型不等于不做字幕，二者分开。

## 8. 音轨

是否回贴原片音轨由用户确认。若启用：

- 使用原片音轨，不生成新配音，除非用户另行要求。
- 记录起始偏移和采样率。
- 检查台词与镜头同步。
- 检查音轨时长和容器时长。
- 验证成片实际包含音频流。

## 9. 编码示例

仅视频序列的示例：

```bash
ffmpeg -y \
  -framerate 24000/1001 \
  -start_number 1 \
  -i frames/v01/subtitled/%04d.png \
  -c:v libx264 -preset medium -crf 17 \
  -pix_fmt yuv420p -movflags +faststart \
  delivery/v01/animation.mp4
```

添加音轨前必须确认来源和映射，不直接复制旧项目命令。使用 `-shortest` 前检查它是否会截断预期内容。

## 10. ffprobe 和视觉复核

至少查询：

```bash
ffprobe -v error \
  -show_entries stream=index,codec_type,width,height,r_frame_rate,nb_frames,duration \
  -show_entries format=duration,size \
  -of json delivery/v01/animation.mp4
```

核对：

- 分辨率。
- 帧率。
- 帧数。
- 视频和音频时长。
- 容器时长。
- 文件大小是否合理。

再抽取首帧、末帧、每个切点和复杂动作帧。编码成功不等于内容正确。

## 11. 交付包

至少包含：

```text
生产 Maya 场景
当前分镜表和逐镜设计表
相机映射
最终成片
序列和编码验证报告
静帧/短段验收证据
依赖和版本说明
剩余问题
备份 manifest 与 SHA-256
交接记录
```

不把所有失败中间场景混入正式交付；保留在明确的历史诊断区。

## 12. 完成定义

最终成片必须与实际生产场景、相机映射、帧序列和验证报告一致。不得只凭“71 台相机”“3512 帧”“脚本无报错”或“文件能播放”宣布完成。