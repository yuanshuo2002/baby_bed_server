# /sensor/detect 接口说明文档

> 指导接口调用和数据验证

## 1. 接口概述

**接口路径**: `POST /api/v1/sensor/detect`

**功能**: 基于设备最新传感器数据进行五类状态分类，检测到状态变化时自动写入数据库

**调用场景**:
- 设备定时触发（如每30秒/1分钟）
- 检测到异常状态时立即触发
- 状态变化时自动记录

**认证方式**: 无需认证（硬件接口）

---

## 2. 请求格式

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| device_sn | string | 是 | 设备序列号 |

### 请求示例

```bash
# 标准请求
curl -X POST "http://localhost:8000/api/v1/sensor/detect?device_sn=SN001"

# 生产环境
curl -X POST "https://api.example.com/api/v1/sensor/detect?device_sn=SN001"
```

---

## 3. 响应格式

### 成功响应

```json
{
  "code": 0,
  "message": "检测完成",
  "data": {
    "device_sn": "SN001",
    "baby_id": 1,
    "status_type": "sleeping",
    "status_level": 0,
    "status_changed": true,
    "log_id": 123,
    "sensor_snapshot": {
      "breath_rate": 35.0,
      "heart_rate": 110.0,
      "body_movement": 0.2,
      "sound_db": 32.0,
      "pose_status": "supine",
      "expression": "peaceful"
    },
    "timestamp": "2026-05-27T10:30:00"
  }
}
```

### 哭闹状态响应（含 cry_event_id）

```json
{
  "code": 0,
  "message": "检测完成",
  "data": {
    "device_sn": "SN001",
    "baby_id": 1,
    "status_type": "crying",
    "status_level": 2,
    "status_changed": true,
    "log_id": 124,
    "cry_event_id": 456,
    "sensor_snapshot": {...},
    "timestamp": "2026-05-27T10:30:00"
  }
}
```

### 危险状态响应（含 danger_event_id）

```json
{
  "code": 0,
  "message": "检测完成",
  "data": {
    "device_sn": "SN001",
    "baby_id": 1,
    "status_type": "danger",
    "status_level": 3,
    "status_changed": true,
    "log_id": 125,
    "danger_event_id": 789,
    "sensor_snapshot": {...},
    "timestamp": "2026-05-27T10:30:00"
  }
}
```

### 无数据响应

```json
{
  "code": 0,
  "message": "检测完成",
  "data": {
    "device_sn": "SN001",
    "status": "no_data",
    "message": "无传感器数据"
  }
}
```

---

## 4. 五类状态说明

| 状态类型 | 说明 | 状态级别 | 触发条件示例 |
|---------|------|---------|-------------|
| `sleeping` | 熟睡 | 0 | 呼吸频率<40，心率<130，体动<0.3，声音<40dB |
| `awake` | 苏醒 | 0 | 体动>0.3，声音30-55dB |
| `playing` | 高兴玩耍 | 0 | 体动>2.0，声音>45dB |
| `crying` | 哭闹 | 1-3 | 声音>50dB，心率>130 |
| `danger` | 危险动作 | 1-3 | 站立/翻床/趴睡/靠近床边 |

### 哭闹级别

| 级别 | 说明 |
|------|------|
| 1 | 轻微哼唧 |
| 2 | 有节奏哭闹 |
| 3 | 剧烈大哭 |

### 危险级别

| 级别 | 说明 |
|------|------|
| 1 | 警告（靠近床边） |
| 2 | 危险（趴睡） |
| 3 | 紧急（站立/翻床） |

---

## 5. 测试指南

### 5.1 前提条件

测试前需确保设备已上传过传感器数据：

```bash
curl -X POST "http://localhost:8000/api/v1/sensor/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "device_sn": "SN001",
    "baby_id": 1,
    "collected_at": "2026-05-27T10:00:00",
    "breath_rate": 35.0,
    "heart_rate": 110.0,
    "body_movement": 0.2,
    "sound_db": 32.0,
    "pose_status": "supine",
    "expression": "peaceful"
  }'
```

### 5.2 完整测试流程

```bash
# Step 1: 上传熟睡状态数据
curl -X POST "http://localhost:8000/api/v1/sensor/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "device_sn": "TEST001",
    "baby_id": 1,
    "collected_at": "2026-05-27T10:00:00",
    "breath_rate": 35.0,
    "heart_rate": 110.0,
    "body_movement": 0.1,
    "sound_db": 30.0,
    "pose_status": "supine"
  }'

# Step 2: 触发检测（预期: sleeping）
curl -X POST "http://localhost:8000/api/v1/sensor/detect?device_sn=TEST001"

# Step 3: 上传哭闹状态数据
curl -X POST "http://localhost:8000/api/v1/sensor/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "device_sn": "TEST001",
    "baby_id": 1,
    "collected_at": "2026-05-27T10:01:00",
    "breath_rate": 38.0,
    "heart_rate": 155.0,
    "body_movement": 2.5,
    "sound_db": 68.0,
    "pose_status": "supine"
  }'

# Step 4: 触发检测（预期: crying + 创建 cry_event）
curl -X POST "http://localhost:8000/api/v1/sensor/detect?device_sn=TEST001"

# Step 5: 上传危险状态数据
curl -X POST "http://localhost:8000/api/v1/sensor/upload" \
  -H "Content-Type: application/json" \
  -d '{
    "device_sn": "TEST001",
    "baby_id": 1,
    "collected_at": "2026-05-27T10:02:00",
    "breath_rate": 40.0,
    "heart_rate": 130.0,
    "body_movement": 3.0,
    "sound_db": 50.0,
    "pose_status": "standing",
    "height_cm": 75.0
  }'

# Step 6: 触发检测（预期: danger + 创建 danger_event）
curl -X POST "http://localhost:8000/api/v1/sensor/detect?device_sn=TEST001"
```

---

## 6. 数据库表说明

### 6.1 baby_status_log（状态日志表）

记录所有状态变化，是主要的状态记录表。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| baby_id | bigint | 宝宝ID |
| device_sn | varchar(64) | 设备序列号 |
| status_type | enum | 状态类型 |
| status_level | int | 状态级别 |
| started_at | datetime | 状态开始时间 |
| ended_at | datetime | 状态结束时间 |
| duration_sec | int | 持续时长(秒) |
| breath_rate | decimal | 呼吸频率 |
| heart_rate | decimal | 心率 |
| sound_db | decimal | 声音分贝 |
| pose_status | varchar | 姿态 |
| expression | varchar | 表情 |

### 6.2 cry_event（哭闹事件表）

当检测到 `crying` 状态时自动创建。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| baby_id | bigint | 宝宝ID |
| device_sn | varchar(64) | 设备序列号 |
| cry_level | int | 哭闹级别(1-3) |
| cry_type | enum | 哭闹类型 |
| started_at | datetime | 开始时间 |
| sound_db | decimal | 声音分贝 |
| heart_rate | decimal | 心率 |
| body_movement | decimal | 体动活跃度 |
| expression | varchar | 表情 |

### 6.3 danger_event（危险事件表）

当检测到 `danger` 状态时自动创建。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| baby_id | bigint | 宝宝ID |
| device_sn | varchar(64) | 设备序列号 |
| danger_type | enum | 危险类型 |
| severity | int | 严重程度(1-3) |
| detected_at | datetime | 检测时间 |
| breath_rate | decimal | 呼吸频率 |
| heart_rate | decimal | 心率 |
| body_offset_cm | decimal | 身体偏移距离 |
| pose_status | varchar | 姿态 |

---

## 7. 数据验证 SQL

### 7.1 查看状态日志

```sql
-- 查看设备所有状态日志（最新在前）
SELECT id, status_type, status_level, started_at, ended_at, duration_sec
FROM baby_status_log
WHERE device_sn = 'TEST001'
ORDER BY started_at DESC;

-- 查看今天的状态变化
SELECT id, status_type, started_at, ended_at, duration_sec
FROM baby_status_log
WHERE device_sn = 'TEST001'
  AND started_at >= CURDATE()
ORDER BY started_at DESC;

-- 统计各状态时长
SELECT status_type, COUNT(*) as count, SUM(duration_sec) as total_sec
FROM baby_status_log
WHERE device_sn = 'TEST001'
  AND started_at >= CURDATE()
GROUP BY status_type;
```

### 7.2 查看哭闹事件

```sql
-- 查看哭闹事件列表
SELECT id, cry_level, started_at, duration_sec, sound_db, heart_rate
FROM cry_event
WHERE device_sn = 'TEST001'
ORDER BY started_at DESC;

-- 统计哭闹次数
SELECT COUNT(*) as cry_count, SUM(duration_sec) as total_cry_sec
FROM cry_event
WHERE device_sn = 'TEST001'
  AND started_at >= CURDATE();
```

### 7.3 查看危险事件

```sql
-- 查看危险事件列表
SELECT id, danger_type, severity, detected_at, duration_sec, pose_status
FROM danger_event
WHERE device_sn = 'TEST001'
ORDER BY detected_at DESC;

-- 查看紧急危险事件
SELECT id, danger_type, severity, detected_at, pose_status
FROM danger_event
WHERE device_sn = 'TEST001'
  AND severity >= 3
ORDER BY detected_at DESC;
```

---

## 8. 注意事项

### 8.1 状态变化才写入

只有当检测到状态与上次不同时，才会写入 `baby_status_log` 表。
- 如果状态未变化，`log_id` 不会出现在返回中
- 如果状态未变化，不会创建 `cry_event` 或 `danger_event`

### 8.2 上一个状态自动结束

当状态变化时，系统会自动结束上一个状态日志：
- 设置 `ended_at` 为当前时间
- 计算并设置 `duration_sec`

### 8.3 危险状态优先级最高

检测顺序：危险 > 哭闹 > 玩耍 > 苏醒 > 熟睡

### 8.4 需要提前上传传感器数据

`/sensor/detect` 依赖 `sensor_data_raw` 表中的数据：
- 必须先调用 `/sensor/upload` 上传数据
- 检测逻辑读取设备最新的传感器数据

---

## 9. 错误处理

| 错误类型 | 返回 message | 原因 |
|---------|-------------|------|
| 无传感器数据 | `{"status": "no_data", "message": "无传感器数据"}` | 设备未上传过数据 |
| 设备未绑定宝宝 | `{"status": "no_baby", "message": "设备未绑定宝宝"}` | baby_id 为空 |
| 状态未变化 | status_changed: false | 状态与上次相同 |

---

## 10. 接口变更历史

| 日期 | 版本 | 变更说明 |
|------|------|---------|
| 2026-05-27 | v1.0 | 新增 /sensor/detect 完整实现 |

> 文档版本: v1.0
> 最后更新: 2026-05-27