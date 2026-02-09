# traffic-burner

按目标速率消耗下行流量的脚本（默认约 0.5 MB/s），支持按小时运行和手动停止。

> 仅用于你拥有或明确授权的网络环境测试。

## 功能

- 目标速率控制（默认 `0.5 MB/s`）
- 运行时长按小时设置（如 `--hours 2.5`）
- 支持手动停止：`Ctrl+C` / `kill` / `stop.flag`
- 自动切换下载源，源异常时重试退避
- 实时打印：累计流量、瞬时速度、剩余时间

## 一键启动（小白推荐）

### Linux

```bash
chmod +x oneclick.sh
./oneclick.sh
```

### macOS（双击版）

```bash
chmod +x oneclick.command
# 然后可在 Finder 双击 oneclick.command
```

脚本会自动：创建虚拟环境、安装依赖、询问时长和速率、启动任务。

## 安装（手动方式）

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 用法

### 默认运行（1小时，0.5 MB/s）

```bash
python3 traffic_burner.py
```

### 运行 3 小时，目标 0.5 MB/s

```bash
python3 traffic_burner.py --hours 3 --rate 0.5
```

### 使用自定义 URL 列表

```bash
python3 traffic_burner.py --hours 2 --rate 0.5 --urls-file urls.example.txt
```

## 手动停止

### 1) Ctrl+C
直接在前台终端按 `Ctrl+C`。

### 2) 后台进程 kill

```bash
pkill -f traffic_burner.py
```

### 3) stop 文件
默认检测 `stop.flag`，创建后脚本会优雅退出：

```bash
touch stop.flag
```

## 参数

- `--hours`：运行小时数（浮点，默认 `1.0`）
- `--rate`：目标速率 MB/s（默认 `0.5`）
- `--chunk-kb`：读取块大小 KB（默认 `64`）
- `--urls-file`：URL 列表文件
- `--connect-timeout`：连接超时秒（默认 `10`）
- `--read-timeout`：读取超时秒（默认 `20`）
- `--log-interval`：日志间隔秒（默认 `5`）
- `--stop-file`：停止标记文件（默认 `stop.flag`）

## 注意

- 实际速度会受网络抖动、源站限制影响，脚本会尽量贴近目标值。
- 请遵守网络服务提供商和目标站点使用条款。
