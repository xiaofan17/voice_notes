# Voice Notes - Home Assistant 语音笔记集成

这是一个 Home Assistant HACS 集成，允许您通过语音指令创建和管理笔记。

## 功能特性

- 🎤 语音指令创建笔记
- 💾 永久性笔记存储
- 📊 笔记统计传感器
- 🔄 自动状态更新
- 🌐 支持中文语音指令

## 安装方法

### 通过 HACS 安装（推荐）

1. 确保已安装 [HACS](https://hacs.xyz/)
2. 在 HACS 中搜索 "Voice Notes"
3. 点击安装
4. 重启 Home Assistant

### 手动安装

1. 下载最新版本的 `voice-notes.zip`
2. 解压到 `custom_components/voice_notes/` 目录
3. 重启 Home Assistant

## 配置步骤

### 1. 添加集成

1. 进入 Home Assistant 设置 → 设备与服务
2. 点击"添加集成"
3. 搜索"Voice Notes"
4. 按照向导完成配置

### 2. 配置语音意图

在您的 `configuration.yaml` 文件中添加以下配置：

```yaml
# 配置语音意图
intent:

# 配置对话代理（如果使用 Assist）
conversation:
  intents:
    AddNoteIntent:
      - "记个笔记 内容是 {content}"
      - "添加笔记 {content}"
      - "新建笔记 内容 {content}"
      - "记录 {content}"

# 配置意图脚本
intent_script:
  AddNoteIntent:
    speech:
      text: "好的，我已经为您记录了笔记：{{ content }}"
    action:
      - service: voice_notes.add_note
        data:
          content: "{{ content }}"
```

### 3. 重启 Home Assistant

配置完成后，重启 Home Assistant 以使配置生效。

## 使用方法

### 语音指令

对您的语音助手说：
- "记个笔记 内容是 明天要记得浇花"
- "添加笔记 买牛奶和面包"
- "新建笔记 内容 下午3点开会"

### 实体说明

集成会创建以下实体：

#### 传感器
- `sensor.voice_notes_count` - 显示活跃笔记数量
- `sensor.voice_notes_list` - 显示笔记列表详情

#### 服务
- `voice_notes.add_note` - 添加新笔记
- `voice_notes.complete_note` - 标记笔记为完成
- `voice_notes.delete_note` - 删除笔记

### 自动化示例

```yaml
# 每日笔记提醒
automation:
  - alias: "每日笔记提醒"
    trigger:
      platform: time
      at: "09:00:00"
    condition:
      condition: numeric_state
      entity_id: sensor.voice_notes_count
      above: 0
    action:
      service: tts.speak
      data:
        entity_id: media_player.living_room
        message: "您有 {{ states('sensor.voice_notes_count') }} 条待办笔记"
```

## 故障排除

### 语音指令不工作

1. 确保已正确配置 `configuration.yaml`
2. 检查语音助手是否正常工作
3. 查看 Home Assistant 日志中的错误信息

### 笔记未保存

1. 检查 Home Assistant 的存储权限
2. 确保集成已正确安装和配置
3. 重启 Home Assistant

### 传感器未显示

1. 确保集成已添加到设备与服务中
2. 检查实体是否被禁用
3. 刷新浏览器缓存

## 开发与贡献

### 本地开发

1. 克隆仓库到 `custom_components/voice_notes/`
2. 修改代码
3. 重启 Home Assistant 测试

### 提交问题

如果遇到问题，请在 GitHub 上提交 Issue，包含：
- Home Assistant 版本
- 集成版本
- 错误日志
- 复现步骤

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持语音笔记创建
- 基础传感器功能
- HACS 集成支持


 
 

