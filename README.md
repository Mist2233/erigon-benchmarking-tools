# Erigon Transaction Replay & Trace Collector

这是一个用于从 Erigon 节点收集特定智能合约（如 Uniswap Router）操作码轨迹（Opcode Traces）的工具。它通过重放历史区块中的交易，统计 SLOAD、SSTORE 等关键指令的执行频率，用于 EVM 存储优化研究。

## 🚀 功能特性

- **双模式运行**：支持快速 Shell 脚本模式和 Python 高级参数模式。
- **实时进度显示**：使用 `tqdm` 显示双重进度条（交易收集进度 + 区块扫描进度）。
- **智能日志管理**：详细日志自动转存至 `logs/`，终端仅显示关键信息（支持 `--verbose` 开启详细输出）。
- **结构化输出**：结果自动保存为 JSON 格式至 `results/` 目录，便于后续分析。
- **灵活输入**：支持十进制（`23000000`）和十六进制（`0x16abb73`）区块号。
- **跳跃式采样**：通过 `--block-interval` 按间隔采样区块，扩大时间跨度同时控制耗时。

## 🔧 安装与依赖

确保你的环境中安装了 Python 3。推荐安装 `tqdm` 以启用进度条功能：

```bash
pip3 install tqdm requests --user
# 或者
pip3 install -r requirements.txt --user
```

## 📖 快速开始 (Quick Start)

### 方式 1：使用快速脚本 (推荐)

我们提供了一个封装好的 Shell 脚本 `quick_replay.sh`，适合快速测试。

```bash
# 赋予执行权限
chmod +x quick_replay.sh

# 默认运行：扫描最近 10,000 个区块，收集 500 笔交易
./quick_replay.sh

# 自定义运行：扫描 50,000 个区块，收集 1,000 笔交易
./quick_replay.sh 50000 1000
```

### 方式 2：使用 Python 脚本 (高级用法)

直接运行 Python 脚本可以获得完全的控制权（指定 RPC 地址、精确区块范围等）。

**基本用法：**

```bash
python3 router_trace_collector.py \
  --rpc http://127.0.0.1:8545 \
  --start-block 23762019 \
  --end-block 23772019 \
  --output my_experiment.json \
  --max-traces 500
```

**采样重放（长时间跨度）:**

在 10,000 个区块的范围内，每 100 个区块采 1 个样（用于压力测试缓存局部性）。

```bash
python3 router_trace_collector.py \
  --rpc http://127.0.0.1:8545 \
  --start-block 23780000 \
  --end-block 23790000 \
  --block-interval 100 \
  --output sampled_10k_blocks.json
```

提示：区块范围为“包含尾区块”。当跨度正好为 10,000 且步长为 100 时，采样区块数为 101。如果你需要严格采样 100 个区块，请将 `--end-block` 设置为 `start_block + 9900`。

**后台运行模式 (无进度条)：**

适合使用 `nohup` 挂机运行大规模任务。

```bash
nohup python3 router_trace_collector.py \
  --start-block 23000000 --end-block 23100000 \
  --max-traces 5000 \
  --no-progress &

# 查看日志
tail -f logs/trace.log
```

## ⚙️ 参数说明

| 参数            | 缩写 | 说明                             | 默认值                            |
| --------------- | ---- | -------------------------------- | --------------------------------- |
| `--rpc`         |      | Erigon 节点的 RPC 地址           | `http://127.0.0.1:8545`           |
| `--start-block` |      | 开始区块高度 (支持 hex/dec)      | 最新区块 - 1000                   |
| `--end-block`   |      | 结束区块高度 (支持 hex/dec)      | 最新区块                          |
| `--output`      | `-o` | 结果文件名 (自动存入 `results/`) | `router_opcodes_{timestamp}.json` |
| `--max-traces`  | `-m` | 收集达到此交易数量后停止         | 100                               |
| `--verbose`     | `-v` | 在终端显示详细日志               | False                             |
| `--no-progress` |      | 禁用进度条 (适合日志重定向)      | False                             |
| `--block-interval` |      | 采样区块间隔（100 表示每 100 个区块采 1 个） | 1 |

## 📂 输出文件结构

### 1. 结果文件 (`results/*.json`)

生成的 JSON 包含元数据、单笔交易详情和聚合统计：

```json
{
  "range": {
    "startBlock": 23762019,
    "endBlock": 23772019
  },
  "contracts": {
    "0x881d40237659c251811cec9c364ef91dc08d300c": "Metamask Swap Router"
  },
  "aggregate": {
    "Metamask Swap Router": {
      "SLOAD": 4250,
      "SSTORE": 1391,
      "tx_count": 50
    }
  },
  "transactions": [
    {
      "txHash": "0x...",
      "blockNumber": 23762019,
      "target": "Metamask Swap Router",
      "opcodeCounts": {
        "PUSH1": 757,
        "SLOAD": 64,
        "SSTORE": 21
      }
    }
  ]
}
```

### 2. 日志文件 (`logs/trace.log`)

所有详细的调试信息、错误堆栈和单笔交易捕获记录都会保存在这里。

## 📊 性能参考

在本地 Erigon 节点上的大概运行速度：

| 区块范围 | 收集交易数 | 预计耗时 | 输出大小 |
| -------- | ---------- | -------- | -------- |
| 100      | ~10        | < 5 秒   | 50 KB    |
| 10,000   | 500        | ~25 秒   | 1.2 MB   |
| 100,000  | 2000       | 2-3 分钟 | 5 MB     |

## 🛠 故障排查

**Q: 提示 "Connection refused" 或无法连接 RPC**
> 检查 Erigon 是否已在离线模式启动，并且 `--http` 端口配置正确。
> ```bash
> # 测试连接
> curl -X POST http://127.0.0.1:8545 \
>   -H "Content-Type: application/json" \
>   -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
> ```

**Q: 脚本权限不足**
> ```bash
> chmod +x quick_replay.sh
> ```

**Q: SSH 终端里进度条乱码**
> 尝试添加 `--no-progress` 参数运行，或检查终端的 UTF-8 支持。

## 💡 数据分析技巧 (jq)

使用 `jq` 命令行工具快速分析 `results/` 下的 JSON 文件：

**1. 统计特定合约的交易数：**
```bash
cat results/result.json | jq '.transactions[] | select(.target == "1inch Aggregation Router V6")'
```

**2. 找出 SLOAD 消耗最多的前 5 笔交易：**
```bash
cat results/result.json | jq '.transactions | sort_by(.opcodeCounts.SLOAD) | reverse | .[0:5]'
```
