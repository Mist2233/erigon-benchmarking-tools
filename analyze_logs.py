import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict
import argparse
from tqdm import tqdm
import os

def load_data(filepath):
    print(f"📂 Loading data from {filepath}...")
    header = pd.read_csv(filepath, nrows=0)
    cols = list(header.columns)
    usecols = ['BlockNum', 'Address']
    if 'Type' in cols:
        usecols.append('Type')
    if 'SlotKey' in cols:
        usecols.append('SlotKey')
    df = pd.read_csv(filepath, usecols=usecols)
    print(f"✅ Loaded {len(df):,} records.")
    return df

def analyze_hotspots(df):
    """分析热点合约"""
    print("\n🔥 Analyzing Top 10 Hot Contracts...")
    
    # 统计每个地址出现的次数
    counts = df['Address'].value_counts().head(10)
    
    print(f"{'Rank':<5} {'Address':<45} {'Access Count':<15} {'% of Total'}")
    print("-" * 80)
    
    total_access = len(df)
    for i, (addr, count) in enumerate(counts.items(), 1):
        percentage = (count / total_access) * 100
        print(f"#{i:<4} {addr:<45} {count:<15,} {percentage:.2f}%")
        
    return counts

class LRUCacheSim:
    """简单的 LRU Cache 模拟器"""
    def __init__(self, capacity):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.hits = 0
        self.misses = 0
    
    def access(self, key):
        if key in self.cache:
            self.hits += 1
            self.cache.move_to_end(key) # 标记为最近使用
        else:
            self.misses += 1
            self.cache[key] = True
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False) # 移除最久未使用的
                
    def get_hit_rate(self):
        total = self.hits + self.misses
        return (self.hits / total) * 100 if total > 0 else 0

def simulate_cache_strategies(df, sizes):
    """模拟不同大小的 Cache 表现"""
    print("\n🧪 Simulating LRU Cache Performance...")
    
    results = {}
    addresses = df['Address'].tolist() # 转为列表以提高遍历速度
    
    for size in sizes:
        print(f"   Running simulation for Capacity = {size:,} ...")
        sim = LRUCacheSim(size)
        
        # 模拟访问流
        for addr in addresses:
            sim.access(addr)
            
        hit_rate = sim.get_hit_rate()
        results[size] = hit_rate
        print(f"   -> Hit Rate: {hit_rate:.2f}%")
        
    return results

def compute_wss_per_block(df):
    print("\n🔍 Computing per-block unique key counts (Working Set Size)...")
    addr = df['Address'].astype(str).str.lower()
    if 'SlotKey' in df.columns:
        slot = df['SlotKey'].astype(str).str.lower()
        key = addr + '_' + slot
        key_desc = '(Address, SlotKey)'
    elif 'Type' in df.columns:
        typ = df['Type'].astype(str).str.lower()
        key = addr + '_' + typ
        key_desc = '(Address, Type)'
    else:
        key = addr
        key_desc = '(Address)'
    wss = df.assign(_key=key).groupby('BlockNum')['_key'].nunique()
    print(f"   Key granularity: {key_desc}")
    desc = wss.describe()
    p50 = float(wss.quantile(0.50))
    p90 = float(wss.quantile(0.90))
    p95 = float(wss.quantile(0.95))
    p99 = float(wss.quantile(0.99))
    print("\n   WSS Summary per block:")
    print(f"   • Blocks: {int(desc['count'])}")
    print(f"   • Mean:   {desc['mean']:.2f}")
    print(f"   • Std:    {desc['std']:.2f}")
    print(f"   • Min:    {desc['min']:.0f}")
    print(f"   • P50:    {p50:.0f}")
    print(f"   • P90:    {p90:.0f}")
    print(f"   • P95:    {p95:.0f}")
    print(f"   • P99:    {p99:.0f}")
    print(f"   • Max:    {desc['max']:.0f}")
    return wss

def plot_wss_distribution(wss):
    print("\n📊 Plotting WSS distribution...")
    plt.figure(figsize=(10, 6))
    plt.hist(wss.values, bins=50, color='steelblue', edgecolor='black')
    plt.title('Per-Block Working Set Size (Unique Keys)')
    plt.xlabel('Unique Keys per Block')
    plt.ylabel('Block Count')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('wss_per_block.png')
    print("   Saved 'wss_per_block.png'")

def plot_results(hotspots, cache_results):
    """生成图表并保存"""
    print("\n📊 Generating Plots...")
    
    # 图 1: 热点合约分布
    plt.figure(figsize=(12, 6))
    hotspots.plot(kind='bar', color='orange')
    plt.title('Top 10 Hot Contracts Access Distribution')
    plt.xlabel('Contract Address')
    plt.ylabel('Access Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('top10_hotspots.png')
    print("   Saved 'top10_hotspots.png'")
    
    # 图 2: Cache 大小 vs 命中率
    plt.figure(figsize=(10, 6))
    sizes = list(cache_results.keys())
    rates = list(cache_results.values())
    
    plt.plot([str(s) for s in sizes], rates, marker='o', linestyle='-', linewidth=2)
    plt.title('LRU Cache Hit Rate vs Capacity')
    plt.xlabel('Cache Capacity (Number of StateObjects)')
    plt.ylabel('Hit Rate (%)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # 在点上标数值
    for i, rate in enumerate(rates):
        plt.text(i, rate + 0.5, f"{rate:.1f}%", ha='center')
        
    plt.savefig('cache_hit_rate.png')
    print("   Saved 'cache_hit_rate.png'")

def main():
    parser = argparse.ArgumentParser(description="Analyze Erigon IntraBlockState Access Logs")
    parser.add_argument('--file', type=str, default='access_log.csv', help='Path to CSV log file')
    args = parser.parse_args()
    
    if not os.path.exists(args.file):
        print(f"❌ Error: File {args.file} not found.")
        return

    # 1. 加载数据
    df = load_data(args.file)
    
    # 2. 热点分析
    hotspots = analyze_hotspots(df)
    
    # 3. 计算每区块唯一 Key 数量（Working Set Size）
    wss = compute_wss_per_block(df)
    plot_wss_distribution(wss)

    # 4. 模拟不同 Cache 大小
    # 测试容量：1000, 5000, 10000, 50000, 100000, 以及无限大(模拟)
    test_sizes = [1000, 5000, 10000, 50000, 100000]
    cache_results = simulate_cache_strategies(df, test_sizes)
    
    # 5. 画图
    plot_results(hotspots, cache_results)
    
    print("\n✅ Analysis Complete!")

if __name__ == "__main__":
    main()
