# 复现

[English](reproducibility.md) | **简体中文**

通过本仓库的两条路径。第一条只需要一份克隆。第二条要花钱。

---

## 环境要求

| | |
|---|---|
| 操作系统 | 任意（开发环境为 Windows 11） |
| Python | 3.13（固定在 `.python-version`） |
| 包管理器 | [uv](https://docs.astral.sh/uv/) |
| SDK | `typesafe-sdk`，固定在 `pyproject.toml` 与 `uv.lock` |

---

## 1. 完全离线 —— 不需要 API key，不需要网络

这是你应该走的路径。它复现的是*分析*，而那正是可以被精确复现的部分。

```console
git clone https://github.com/Charlie-Wang-03/jev-testbench.git
cd jev-testbench

uv sync --locked
uv run pytest
```

**完整离线测试套件全部通过，且不打开任何 socket。** 测试套件直接封锁 socket，因此一次意外的 API 调用会大声失败，
而不是悄悄花掉你的钱。在需要真正驱动客户端的地方，测试使用 `httpx2.MockTransport` 对接真实 SDK。

### 重建派生文件

```console
uv run python -m jev_lab report         # results/summary.csv, results/summary.md
uv run python -m jev_lab snapshot       # results/capability_snapshot.md
uv run python -m jev_lab final-report   # results/JEV_LOCAL_EVALUATION_FINAL.md
```

这些命令都不会调用 API、不需要 key，也不会写入日志。每一个数字都在输出时从已提交的权威日志重新计算，
因此重新生成的文件要么与日志一致，要么可被检测为过期 —— 派生文件永远无法成为第二个事实来源。

### 直接检查证据

```console
uv run python -m jev_lab list           # 实验、档位、调用上限、凭据状态
```

然后直接读日志。它们是 JSONL —— 每行一个自描述的对象：

```console
head -1 results/usage.jsonl
head -1 results/p3_boundary_locus/usage.jsonl
```

### 核验哈希

```console
sha256sum results/usage.jsonl                     # 38e67630a7c345...8dc40b1b   （42 条记录）
sha256sum results/p3_boundary_locus/usage.jsonl   # 17f36f7551d598...f34c5d78e   （12 条记录）
```

这些必须与 [FREEZE.md](../../FREEZE.md) 和[溯源记录](../EVIDENCE_PROVENANCE.md)中的值一致。
`.gitattributes` 固定了 `eol=lf`，正是为了让 Windows 上的检出无法重写行尾、从而悄悄改变这些哈希所
覆盖的字节。

### 每条记录里的标识符

每条记录都带有 `request_id`（每次调用）、`run_id`（每次 CLI 调用）和 `client_session_id`（每个连接池）。
打开日志时，这些是最先看起来可能敏感的字段，所以这里说明它们是什么：

- **它们不是凭据**，也不是由 API key 派生出来的。
- **它们保留在日志中是仓库所有者的决定** —— `OWNER_DECISION_PUBLIC_OK`。没有任何标识符被哈希、
  脱敏或删除，上面两个哈希覆盖的正是已发布的日志原文。
- **它们是不透明的，不是匿名的。** `request_id` 是通向 TypeSafe 自身请求历史的句柄；保留它，是因为
  正是它让一条已发布的记录可以被拿去与产生它的服务核对。所有者审阅并接受了这一取舍。

完整说明（包括对两份日志的扫描发现了什么、没发现什么）见
[SECURITY.md § Opaque identifiers in the canonical logs](../../SECURITY.md#opaque-identifiers-in-the-canonical-logs)。

### 不需要 key 就能检查的事

- P3 分析器的事后修正没有改变判定 —— `tests/test_p3_boundary_locus.py` 会对着真实日志断言这一点。
- 核心日志在冻结之后从未改变 —— `git diff e20fad5 bdcb637 --stat -- results/usage.jsonl` 是空的。

---

## 2. 真实运行 —— 需要 TypeSafe 账号，且会花真钱

> **成本警告。** 这些命令会针对真实账号发起真实 API 调用。请先读[凭据](credentials.zh-CN.md)，并看下面的
> [预算](#预算)。

```console
uv run python -m jev_lab list                    # 看看有什么，以及它的调用上限
uv run python -m jev_lab run 01_primitives       # 单个实验；默认上限 8 次调用
uv run python -m jev_lab run-all --tier core     # 整档运行；没有显式预算时拒绝启动
```

`list`、`report`、`snapshot` 和 `final-report` 从不调用 API。**只有 `run` 和 `run-all` 会花钱**，
它们的 `--help` 文本也是这么写的。

### 预算

- `run` 默认硬上限 **8** 次 API 调用。用 `--max-requests N` 覆盖。
- `run-all` 在 `--max-requests` 小于该档 case 数时**拒绝启动**。批量运行必须是明确的人类决定。
- `05_speculative_fanout` 带控制流，因此它声明的 4 个 case 可能变成 6 次调用。它的预算检查用的是声明的
  `call_ceiling`，永远不是 case 数。
- 任何地方都**没有无界循环**。重复类实验各上限 5 次。
- 认证失败会立即中止，而不是把剩余预算花掉。

### 把结果写到别处

每个命令都接受 `--results-dir`。把它指向一个临时目录，以避免向权威日志追加数据 —— 那些日志是冻结证据，
不得追加：

```console
uv run python -m jev_lab run 01_primitives --results-dir /tmp/jev-scratch
```

---

## 3. 「复现」在这里能与不能意味着什么

> **冻结的测量是历史测量，不是每次未来运行都必须精确复现的黄金输出。**

复现**方法**才是目标。复现**数字**不是这个设计能够承诺的事，原因有四，各自独立：

1. **别名会移动。** 默认请求的是 `jev-latest`；只有响应能说明是哪个模型回答的。冻结记录解析到的
   是 `jev-1.13.0`。未来的运行可能解析到别处。`model_requested` 与 `model_resolved` 都被记录，正是
   为了这个原因。
2. **它是一个概率模型。** 逐字节相同的请求返回了形状不同的分布 —— 胜出标签保持住了，它下面的分布移动了。
   见[发现 §1](../findings/findings.zh-CN.md)。
3. **底层环境不同。** 延迟是围绕单次 SDK 调用的墙钟时间，其中包含 DNS、TCP、TLS、连接池状态、服务端排队、
   上游负载与本地调度。不同的机器或不同的一天就是不同的测量。
4. **账号与会话不同。** 成本是基于单一公布价格表的本地估算；TypeSafe Console 账单才是权威。

所以：一次产生了不同数字的真实运行，**并没有**证伪那些冻结的数字；一次数字吻合的真实运行，也**没有**
验证它们。它只是产生了第二份测量。

### 为什么核心日志是冻结的，而不是持续追加的

`results/usage.jsonl` 持有 42 条记录和一个已公布的 SHA-256。向它追加数据会使该哈希失效并毁掉这次引用。
新的工作应当在它自己的目录里拥有自己的日志 —— P3 正是这么做的。如果你想添加测量，请使用 `--results-dir`。

### 重跑 P3

P3 不在 `EXPERIMENTS` 注册表里，正是为了让 `run-all` 无法运行它。它的设计冻结在
[预注册文档](../experiments/P3_BOUNDARY_LOCUS_PREREGISTRATION.md)中，并且它恰好做了十二次调用。再次
运行它，会在同一设计下产生一份*新的*测量 —— 这是完全正当的事情，但那是一个新实验，不是对冻结那次实验的
复现，而且它应当放进一份新的日志。

---

## 4. 故障排查

| 症状 | 原因 |
|---|---|
| `TYPESAFE_API_KEY: missing` | 环境里没有 key，也没有可读的 `.secrets/typesafe.env`。见[凭据](credentials.zh-CN.md)。 |
| `TYPESAFE_API_KEY: unusable (malformed \| duplicate-key \| unreadable)` | 文件存在但无法使用。加载器会 fail closed，而不是猜测。 |
| `refusing to run: N cases planned but --max-requests is M` | 预算小于 case 列表。如果那笔花费是有意的，请传更大的 `--max-requests`。 |
| pytest 无法创建临时目录 | pytest 使用项目内 basetemp（`--basetemp=.pytest-tmp`），因为系统 `%TEMP%` 在这个项目运行的部分环境中不可写。`.pytest-tmp/` 已被 gitignore。 |
| 设置 `TYPESAFE_LOG_LEVEL` 后答案看起来是空的或很奇怪 | 不要把它设为 `debug`。SDK 会脱敏密钥 *header*，但明确**不**脱敏请求 / 响应 *body*，因此 debug 日志会把你完整的 state 和每一个答案都打印出来。 |
