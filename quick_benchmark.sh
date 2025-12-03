#!/bin/bash
# 快速基准脚本 - 基于 benchmark_replay.py，从当前区块开始对指定区块数量发起 RPC 基准请求

set -e

RPC_URL=${RPC_URL:-"http://127.0.0.1:8545"}
BLOCK_RANGE=${1:-100}   # 要回放（基准）多少个区块
REPEAT=${2:-1}          # 每个区块重复请求次数（增加以降低噪声）
NO_WARMUP=${3:-0}       # 传 1 跳过 warmup
VERBOSE=${4:-0}         # 传 1 打印每次延迟

if [ "$BLOCK_RANGE" -le 0 ]; then
  echo "BLOCK_RANGE 必须大于 0"
  exit 1
fi

echo "======================================"
echo "🚀 快速 RPC 基准工具"
echo "======================================"

# 获取当前区块高度
echo "📊 正在查询当前区块高度..."
CURRENT_BLOCK_HEX=$(curl -s -X POST $RPC_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  | grep -o '"result":"0x[^"]*"' \
  | cut -d'"' -f4 || true)

if [ -z "$CURRENT_BLOCK_HEX" ]; then
    echo "❌ 错误: 无法连接到 RPC ($RPC_URL) 或解析区块高度失败"
    exit 1
fi

CURRENT_BLOCK=$((16#${CURRENT_BLOCK_HEX:2}))
START_BLOCK=$((CURRENT_BLOCK - BLOCK_RANGE + 1))
if [ "$START_BLOCK" -lt 0 ]; then START_BLOCK=0; fi

echo "✅ 当前区块: $CURRENT_BLOCK (0x${CURRENT_BLOCK_HEX:2})"
echo "📍 基准区块范围: $START_BLOCK -> $CURRENT_BLOCK ($BLOCK_RANGE 个区块)"
echo "🔁 每区块重复: $REPEAT 次"

# 运行 benchmark_replay.py
CMD=(python3 benchmark_replay.py --rpc "$RPC_URL" --start-block "$START_BLOCK" --end-block "$CURRENT_BLOCK" --repeat "$REPEAT")
if [ "$NO_WARMUP" -ne 0 ]; then
  CMD+=(--no-warmup)
fi
if [ "$VERBOSE" -ne 0 ]; then
  CMD+=(--verbose)
fi

echo "🔄 开始基准测试..."
echo "命令: ${CMD[*]}"

# 执行
"${CMD[@]}"

echo "✅ 基准测试完成"

