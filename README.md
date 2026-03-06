# traffic-burner

一个 **慢速、可控、带预设** 的 VPS 流量消耗脚本。

目标不是瞬间跑满带宽，而是：
- 慢慢烧
- 可控烧
- 到量自动停
- 需要时后台挂着跑

---

## 当前能力

### 预设档位
- `tiny`
  - 最低有效档
  - 下载约 `512 kbps` 起
- `low`
  - 轻度长期挂
- `medium`
  - 日常明显消耗
- `high`
  - 更积极的消耗模式

### 消耗模式
- `download`
- `upload`
- `mixed`

### 已支持功能
- 限速运行
- 多并发
- 实时统计
- 单次目标流量自动停
- 每日目标流量自动停
- 按时长自动停
- 指定允许运行时间段
- systemd 后台运行
- 手动主动停止
- 本地状态持久化

---

## 快速开始

### 本地运行

```bash
chmod +x run.sh menu.sh install-service.sh uninstall-service.sh stop-service.sh bootstrap.sh
./run.sh --preset low
```

### 交互菜单运行（中文版本，更省事）

```bash
./menu.sh
```

会直接给你这些中文选项：
- 轻度慢烧
- 长期挂机
- 今天烧 20GB
- 自定义前台运行
- 安装后台服务
- 停止后台服务
- 卸载后台服务

### 常见例子

#### 轻度慢烧
```bash
./run.sh --preset tiny
```

#### 跑够 5GB 自动停
```bash
./run.sh --preset low --target 5GB
```

#### 今天累计到 20GB 就停
```bash
./run.sh --preset low --target-per-day 20GB
```

#### 跑 1 小时自动停
```bash
./run.sh --preset medium --duration 3600
```

#### 只在 10:00 - 23:00 之间运行
```bash
./run.sh --preset low --start-hour 10 --end-hour 23
```

#### 只在夜间运行（跨天）
```bash
./run.sh --preset low --start-hour 22 --end-hour 6
```

---

## 参数说明

```bash
--preset tiny|low|medium|high
--mode download|upload|mixed
--download-rate-kbps 1024
--upload-rate-kbps 256
--concurrency 2
--interval 1
--target 5GB
--target-per-day 20GB
--duration 3600
--start-hour 10
--end-hour 23
--stats-interval 5
--state-file /root/.traffic-burner-state.json
```

---

## 实测档位参考

短测结果大概是：

- `tiny` ≈ `0.5 Mbps`
- `low` ≈ `1 Mbps`
- `medium` ≈ `4.6 Mbps`
- `high` ≈ `18 Mbps`

> 实际值会受 VPS 线路、对端源、网络状况影响。

粗略估算：
- `tiny`：一天约 5GB
- `low`：一天约 10GB
- `medium`：一天约 45~50GB
- `high`：一天约 180GB

---

## 实时统计

运行时会打印：
- 下载量
- 上传量
- 总量
- 今日累计
- 当前速率

例如：

```text
[stats] down=256.00 KB up=64.00 KB total=320.00 KB today=608.00 KB rate=143.70 KB/s
```

---

## 后台运行（systemd）

### 安装后台服务

```bash
sudo ./install-service.sh --preset low --mode mixed --target-per-day 20GB --start-hour 10 --end-hour 23
```

### 查看状态

```bash
systemctl status traffic-burner
journalctl -u traffic-burner -f
```

### 主动停止

```bash
sudo ./stop-service.sh
```

### 卸载服务

```bash
sudo ./uninstall-service.sh
```

---

## 一键安装脚本

如果仓库已经发布到 GitHub，可以直接这样装：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/LYISTR2/traffic-burner/main/bootstrap.sh)
```

默认会安装到：

```bash
/opt/traffic-burner
```

安装完后直接运行：

```bash
/opt/traffic-burner/run.sh --preset low --target 5GB
```

---

## 文件说明

- `run.sh`：参数式主入口
- `menu.sh`：交互菜单入口
- `install-service.sh`：安装 systemd 服务
- `stop-service.sh`：主动停止后台服务
- `uninstall-service.sh`：卸载后台服务
- `bootstrap.sh`：一键拉取安装
- `traffic_burner/burn.py`：主逻辑
- `traffic_burner/presets.py`：预设档位
- `traffic_burner/sources.py`：默认下载/上传源
- `traffic_burner/state.py`：每日统计状态

---

## 已知限制

- 当前流量统计是应用层统计，不是网卡级精确计量
- 上传/下载源目前是公开源，适合原型和测试
- 还没做随机波动速率
- 还没做更真实的网页/视频行为模拟
- 还没做 Web 管理面板

---

## 适合什么场景

适合：
- VPS 流量包太大用不完
- 想稳定慢烧
- 想每天按目标值消耗
- 想后台长期挂着

不适合：
- 想暴力跑满带宽
- 想做非常精确的运营商级流量控制
- 想模拟特别真实复杂的用户行为

---

## 当前状态

这个项目已经不是空壳原型了，当前已经具备：
- 可运行
- 可测试
- 可后台挂
- 可自动停
- 可按日控制

也就是说，已经能作为一个**实际可用的小工具**来用。
