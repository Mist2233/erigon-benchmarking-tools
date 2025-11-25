# Erigon 实验环境搭建与运行指南

本文档描述了如何配置和运行 Erigon 的原版（Upstream）与实验版（Research），并配合软链接实现无缝切换。

## 1. 目录结构约定

为了配合自动化脚本，请确保你的工作目录结构如下：

```text
$HOME/
├── blockchain-data/               # 数据存储
│   └── mainnet/                   # Erigon 数据目录 (1.7TB)
│
└── workspace/                     # 代码工作区
    ├── erigon-upstream/           # 原版 Erigon (基准对照组)
    ├── erigon-research/           # 实验版 Erigon (包含修改)
    ├── transaction-replay/        # 本工具箱 (当前目录)
    └── erigon-target              # [软链接] 指向当前要运行的版本
```

## 2. 环境初始化

如果你尚未创建软链接，请执行以下命令初始化：

```bash
cd ~/workspace

# 默认先指向原版进行测试
ln -sfn erigon-upstream erigon-target

# 验证链接
ls -l erigon-target
# 应输出: erigon-target -> erigon-upstream
```

## 3. 编译 Erigon

在运行前，请确保两个版本的 Erigon 都已编译完毕：

```bash
# 编译原版
cd ~/workspace/erigon-upstream
make erigon

# 编译实验版
cd ~/workspace/erigon-research
make erigon
```

## 4. 切换与运行

我们使用 `transaction-replay` 目录下的启动脚本来运行节点。该脚本会自动寻找 `erigon-target` 指向的版本。

### 场景 A：运行原版 (Baseline)

```bash
# 1. 切换软链接指向原版
ln -sfn ~/workspace/erigon-upstream ~/workspace/erigon-target

# 2. 启动节点 (使用 screen 或 nohup)
cd ~/workspace/transaction-replay
./run_offline_erigon.sh
```

### 场景 B：运行实验版 (Experimental)

```bash
# 1. 切换软链接指向实验版
ln -sfn ~/workspace/erigon-research ~/workspace/erigon-target

# 2. 启动节点
cd ~/workspace/transaction-replay
./run_offline_erigon.sh
```

## 5. 验证运行版本

节点启动后，可以通过日志头部信息确认当前运行的版本：

- **原版**日志通常显示标准版本号 (e.g., `2.59.0`)
- **实验版**建议修改源码中的 Version 字符串，或者通过日志中的特有 Log 输出来区分。

---
**提示**：`run_offline_erigon.sh` 脚本默认使用 `--datadir $HOME/blockchain-data/mainnet` 和离线模式，确保不会进行 P2P 同步，仅用于 RPC 重放测试。