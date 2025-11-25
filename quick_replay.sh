#!/bin/bash
# 快速交易重放脚本 - 自动获取当前区块高度，并回放指定数量的区块

set -e  # 遇到错误立即退出

# 配置参数
RPC_URL="http://127.0.0.1:8545"
BLOCK_RANGE=${1:-100}  # 扫描的区块数量
MAX_TRACES=${2:-500}     # 最多收集的交易数量

echo "======================================"
echo "🚀 以太坊交易重放工具"
echo "======================================"

# 1. 获取当前区块高度
echo "📊 正在查询当前区块高度..."
CURRENT_BLOCK_HEX=$(curl -s -X POST $RPC_URL \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  | grep -o '"result":"0x[^"]*"' \
  | cut -d'"' -f4)

if [ -z "$CURRENT_BLOCK_HEX" ]; then
    echo "❌ 错误: 无法连接到 Erigon RPC ($RPC_URL)"
    echo "请确保 Erigon 正在运行"
    exit 1
fi

CURRENT_BLOCK=$((16#${CURRENT_BLOCK_HEX:2}))
START_BLOCK=$((CURRENT_BLOCK - BLOCK_RANGE))

echo "✅ 当前区块: $CURRENT_BLOCK (0x${CURRENT_BLOCK_HEX:2})"
echo "📍 扫描范围: $START_BLOCK -> $CURRENT_BLOCK ($BLOCK_RANGE 个区块)"
echo "🎯 最多收集: $MAX_TRACES 笔交易"
echo ""

# 2. 生成输出文件名（带时间戳）
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="router_stats_${BLOCK_RANGE}blocks_${TIMESTAMP}.json"
LOG_FILE="logs/trace_${TIMESTAMP}.log"

echo "📁 输出文件: $OUTPUT_FILE"
echo "📝 日志文件: $LOG_FILE"
echo ""

# 3. 运行重放脚本
echo "🔄 开始重放交易..."
echo "======================================"
echo ""

python3 router_trace_collector.py \
  --rpc $RPC_URL \
  --start-block $START_BLOCK \
  --end-block $CURRENT_BLOCK \
  --output $OUTPUT_FILE \
  --max-traces $MAX_TRACES \
  --log-file $LOG_FILE

# 4. 输出路径处理（自动添加 results/ 前缀）
if [[ "$OUTPUT_FILE" != /* ]] && [[ "$OUTPUT_FILE" != results/* ]]; then
  OUTPUT_FILE="results/$OUTPUT_FILE"
fi

# 5. 检查结果文件是否生成
if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo "======================================"
    echo "✅ 重放完成！"
    echo "======================================"
    
    # 使用 Python 快速分析结果
    python3 -c "
import json
with open('$OUTPUT_FILE') as f:
    data = json.load(f)

print(f'📊 收集统计')
print(f'  • 区块范围: {data[\"range\"][\"startBlock\"]:,} -> {data[\"range\"][\"endBlock\"]:,}')
print(f'  • 总交易数: {len(data[\"transactions\"])} 笔')
print(f'')
print(f'💾 各合约 SLOAD 统计:')

for contract, aggregate in sorted(data['aggregate'].items(), 
                                   key=lambda x: aggregate.get('SLOAD', 0) if 'aggregate' in dir(x) else 0, 
                                   reverse=True):
    tx_count = sum(1 for tx in data['transactions'] if tx['target'] == contract)
    sload = aggregate.get('SLOAD', 0)
    sstore = aggregate.get('SSTORE', 0)
    if tx_count > 0:
        print(f'  • {contract}')
        print(f'    - 交易数: {tx_count}')
        print(f'    - SLOAD:  {sload:>6,} (平均 {sload/tx_count:>5.1f}/tx)')
        print(f'    - SSTORE: {sstore:>6,} (平均 {sstore/tx_count:>5.1f}/tx)')
" 2>/dev/null || echo "⚠️  无法解析结果文件"
    
    echo ""
    echo "📂 查看完整结果: cat $OUTPUT_FILE | jq ."
    echo "📜 查看日志: tail -f $LOG_FILE"
else
    echo "❌ 重放失败，未生成输出文件"
    exit 1
fi
