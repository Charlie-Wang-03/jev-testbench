# Style audit — the Chinese narrative rewrite (P5-E1)

**Audited document:** [`jev-as-probabilistic-decision-primitive.zh-CN.md`](jev-as-probabilistic-decision-primitive.zh-CN.md)
**Style source:** `khazix-writer/SKILL.md` (414 lines), `references/style_examples.md` (428 lines),
`references/content_methodology.md` (136 lines), read in full from
`github.com/KKKKhazix/khazix-skills` during P5-D. The four-layer self-check below is the skill's own
(`SKILL.md` §"自检输出格式"), run by hand against the rewritten text.
**Article archetype:** `调查实验型 × 方法论分享型`, primary 调查实验型. Recorded before writing; unchanged in P5-E.
**Audit date:** 2026-09-27 · **Auditor:** the author · **API calls made during the audit: 0.**
**Revision:** 3 — recomputed in P5-E1 against the P5-E1 text, and extended with an **Over-stylization
check** that revision 2 did not have. Supersedes revision 2 (P5-E), which superseded the P5-D revision,
whose two colloquial-expression counts (11 and 35) contradicted each other and are withdrawn.

**What this file is not.** It is not a claim audit. Whether a sentence is *permitted* is decided by
[`BLOG_CLAIM_CONTRACT.md`](../evidence/v0.1.0/BLOG_CLAIM_CONTRACT.md) and recorded in
[`jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md`](jev-as-probabilistic-decision-primitive.CLAIM_AUDIT.md),
and whether a sentence is *correctly attributed to a person* is decided in
[`…PROCESS_ATTRIBUTION_AUDIT.zh-CN.md`](jev-as-probabilistic-decision-primitive.PROCESS_ATTRIBUTION_AUDIT.zh-CN.md).
A sentence can pass every layer below and still be a claim defect or an attribution defect, and the
three audits are kept separate for that reason. Where style and the evidence contract pull against
each other, §"Evidence-contract overrides" records which won.

**Two hard limits on this audit.** It checks style only, and it makes no statement about whether the
article is *good* — that judgment belongs to a human reader. And the style was applied as a set of
writing rules, not as an impersonation: no author identity, life story, fixed footer, or contact
address was reproduced, and every remaining first-person statement in the article is a decision the
owner actually took, per the process attribution audit.

---

## What changed in this revision

**P5-E1 was a subtraction pass, and the style metrics were allowed to fall.** Nine passages were
corrected, none was added, and the work order forbade introducing any new colloquial device —
no new catchphrase, no new self-deprecation, no new `？？？`, no new one-line punchline. The explicit
instruction was that **style serves content, not the reverse**, and that a metric which drops because a
sentence got more accurate is a metric that did its job. One metric did drop: **口语化表达 33 → 32**.
The lost entry is `撑不住`, which lived in a 删故事 paragraph that P5-E1 deleted as a duplicate. Nothing
was added to replace it, and nothing should have been.

**The article got longer, which is the opposite of what a subtraction pass looks like.** 14,789 →
14,928 characters (narrative body 14,252 → 14,391). Three corrections are longer than what they
replaced — the canonical-log sentence, the cost/latency sentence and the manifest sentence each trade a
compressed phrase for a precise one. This is the trade the stage was asked to make, and the length
change is a consequence of it rather than a target.

**The figures that moved, and the figures that did not.**

| Figure | P5-E | P5-E1 | Direction |
|---|---:|---:|---|
| 口语化表达 | 33 | **32** | down — one deleted with its sentence, none added |
| 单句成段 | 107 | **106** | down — one paragraph deleted, none split |
| 15 字以内短拍 | 34 | **34** | flat — the deleted paragraph's `是删故事的能力。` survives as a beat |
| 扣主线句 | 10 | **10** | flat |
| 疑问句刹车 | 6 个 / 7 次 | **6 个 / 7 次** | flat |
| 正文中文冒号 | 0 | **0** | flat |
| 破折号 / 弯引号 | 0 / 0 | **0 / 0** | flat |
| 独立成段的 `不是。` | 1 | **1** | flat |
| 情绪标点 | 0 | **0** | flat, by rule |

**The P5-D revision's numbers were wrong, and that history still matters.** Revision 1 reported
colloquial expressions as "35 个不同条目" in one table and "11 个" in the summary of the same layer — an
internal contradiction that P5-E's work order named and required be resolved by recomputation from the
current text. Every figure below is recounted from the P5-E1 article by the same script that reproduced
revision 2's numbers exactly, so the deltas above compare like with like. The count is one number, **32**,
with the full list printed in L2-3 so a reader can check it rather than trust it.

**Context from P5-E, retained because P5-E1 did not change it.** The P5-D → P5-E movement was
13,172 → 14,789 characters, and it was the intended direction of P5-E's own §22: deliberate punchline and
one-line-reversal density came down by roughly a third while the closing movement — the AI-involvement
disclosure, the cognitive-debt working concept, and the metaphor — was added. `不是。` as an independent
paragraph went 5 → 1, and the single survivor is the one §23 protects. The four-instance `第N个故事没了`
drumbeat is gone entirely. Fullwidth colons in prose went 0 → 7 in the P5-E draft, all seven caught by
revision 2 and rewritten to 0 before that audit was finalised, leaving one in the H1 (a heading, recorded
as a technical exception). **P5-E1 introduced no colon and inherited none.**

---

## 质检报告

**L1 硬性规则** ✅

- 禁用词：0 处命中（`说白了` / `意味着什么` / `这意味着` / `本质上` / `换句话说` / `不可否认` /
  `综上所述` / `总的来说` / `值得注意的是` / `不难发现` / `首先…其次…最后` 全部零命中）
- 禁用标点：正文散文中 0 处（中文冒号 `：` 0，破折号 `——` 0，弯引号 `""` / `""` 0；H1 标题内的
  一个 `：` 见"Technical exceptions"）
- 结构套话：0 处命中（无 `让我们来看看` / `在当今…的时代` / `随着…的发展`）
- 空泛工具名：0 处（见下方 L1-4 说明）

**L2 风格一致性** ✅

- 开头 ✅
- 节奏 ✅（单句成段 106 处，其中 15 字以内的短拍 34 处；扣主线句 10 处；疑问句刹车 6 个不同问句 /
  7 次出现；无小标题）
- 口语化 ✅（不同口语化表达 32 个，全表列出；论述中的故意打破 5 处；自嘲/承认不足 4 处；
  情绪标点 0 处 —— 这是 L2-3 四项里唯一未做到的一项，理由见 §"Evidence-contract overrides"）
- 标点禁令二次确认 ✅

**L3 内容质量** ✅

- 观点支撑 ✅
- 知识输出 ✅
- 文化升维 ✅（按类型取材，见说明）
- 对立面与同理心 ✅
- 类型专项 ✅（调查实验型）
- 逐一展示 ✅
- 人物画像法 **NOT_APPLICABLE**（不是通过，也不是未通过）

**L4 活人感** ✅

- 温度感 ✅
- 独特性 ✅
- 姿态 ✅
- 心流 ✅（两处刻意减速，见说明）

**总评**：4 层全部通过。L2-3 四项中有一项按规则未做，这是唯一一处低于满分的地方，理由记在
§"Evidence-contract overrides"。L1 与 L2-4 是全项零命中，不是"接近通过"。

**修复优先级**：无强制修复项，**P5-E1 也没有新增任何一项**。P5-D 记下的两条可选打磨项中，(1) 结尾
删故事回扣"收得略快"在 P5-E 已被重写，回扣现在落在最后一个 `不是。` 上并接披露段，P5-E1 又把两处
近义回扣压到一处，这一项现在比 P5-E 更干净；(2) 三条工程经验仍以"第一件/第二件/第三件"分条，仍是
全文最接近结构化写法的一处，保留。

---

## Over-stylization check

《SKILL.md》的自检是**下限检查**：够不够口语、够不够短、够不够有节奏。它不回答反过来的问题 ——
**这些手段是不是已经开始盖住内容本身。** 这一节是 P5-E1 按工作令要求新增的反向检查，四个问题逐条回答，
答案是这四项里的任意一项。

**问题一：一行反转是不是过密？**

**不是。11 处，平均每 46 行一处**（正文 505 行）。逐处列出，位置是行号：

`所以这是复现，不是发现。`(105)、`这个读法站不住。`(137)、`效应很大 ≠ 原因已确定。`(288)、
`实验没坏。`(312)、`分析器坏了。`(314)、`答案是不要。`(386)、`但这个仓库现在没有资格回答。`(420)、
`但这个结果比预期好。`(436)、`但还有一个故事要删。`(454)、`不是。`(462)、
`但它们不会自动变成人的理解。`(490)。

判定依据不是这个数小，而是**分布**：间隔为 32 / 151 / 24 / **2** / 72 / 34 / 16 / 18 / 8 / 28 行。
唯一一处相邻反转是 312 与 314 的 `实验没坏。` / `分析器坏了。`，那是有意成对的一组 —— 先否定"结果坏了"，
再给出真正坏掉的东西，拆开会失去对照。其余最小间隔 8 行（`但还有一个故事要删。` 与 `不是。`），
那是全文最大的两次反转，靠得近是对的。**最大间隔 151 行，说明反转是落在关键节点上的，不是按节拍铺的。**

**问题二：`不是。` 是不是只出现在必要处？**

**是，只有一处，而且它是全文唯一一处非它不可的地方。** P5-D 有 5 处独立成段的 `不是。`，P5-E 压到 1 处，
P5-E1 没有动它。剩下的这一处在 AI 参与披露段：前一句是 `它是这样的。这是一个完全掌握之后亲手做出来的
项目。`，这一处 `不是。` 否掉的是**文章自己刚立起来的一个论断**，而不是一个外部对手的观点。
换成 `并非如此。` 或并入下一段都会削弱这个自我否定。**这是一处结构性的必要，不是口头禅。**

**问题三：`故事` 回扣是不是重复？**

**P5-E 时是重复的，P5-E1 修掉了，现在是 6 次出现、一条线。** 出现位置：163（四个候选的结算）、
434（`54 次调用之后，最好看的几个故事基本都没留下来。`）、438（`后来才发现，这个仓库真正积累的，
不是故事。`）、440（`是删故事的能力。`）、454（`但还有一个故事要删。`）、458（`这个故事是关于这个
项目本身的。`）。**434 到 458 是一个连续的回扣段，P5-E 在这个段里说了两遍同一件事** —— 438–442 那三行
（`因为一个评估仓库真正应该帮你做的…` / `后来才发现…` / `是删故事的能力。`）里，第一行与后两行是同一个
意思的两种说法。P5-E1 删掉了第一行。**删掉之后，回扣变成一次命名（438/440）接一次升级（454），中间不再
有第二遍铺垫**，`但还有一个故事要删。` 因此比以前更直接地跟着 `这个仓库积累的是删故事的能力` 出现。
**这一条是这次检查里唯一一处真正的过密，也是 P5-E1 唯一一处风格上的净删减。**

**问题四：口语化手段是不是开始盖住内容？**

**没有，而且这一版是往反方向走的。** 三条证据：

1. **口语化总数下降，且没有补位。** 33 → 32，减少的一项（`撑不住`）随它所在的句子一起被删，没有为了
   维持计数而新加一个。工作令明确允许甚至预期这个数下降。
2. **本版改动的方向是把口语换成精确。** 三处最长的修改 —— canonical log 那句、成本/延迟那句、
   manifest 那句 —— 都是把模糊的短说法换成更长的准确说法（`本地推的` → `由 token 用量和价格表推算，
   是本地推导，不是账单`）。**这是"内容压过风格"的直接证据**，也是这篇文章变长的唯一原因。
3. **技术术语进入了正文而不是被口语替换掉。** `demonstration threshold`、`Python policy`、
   `canonical log`、`wall-clock`、`benchmark` 五个英文术语现在直接写在散文里。它们在 L2 的"口语化"
   这一层是减分的，在 L3 的"知识输出"和 claim 准确性这一层是加分的。**这里风格让位，是这次检查
   要确认的那件事。**

**这一节的结论。** 四个问题里，只有一个（回扣重复）在 P5-E 答案是"是"，P5-E1 把它变成了"否"。另外三个
在 P5-E 就已经是否定的，P5-E1 没有让它们变差。**本版审计的判断是：这篇文章的风格现在服务于内容，而不是
反过来 —— 判据不是 32 这个数，而是这一版每一次风格指标下降都能指到一句因此变准确的话。**

---

## L1 明细

**L1-1 禁用词。** 全文扫描零命中。`首先` 与 `其次` 各 0 处；`最后` 出现 2 处，两处都是实指（`也是
最后被删的一个` 指第四个候选的序号；`最后真的被执行了` 指 K1 的执行时点），不是"首先…其次…最后"
这种结构套话，不属于本项射程。

**L1-2 禁用标点。** 中文冒号、破折号、弯引号在正文散文里各 0 处。正文引语一律用 `「」`，共 32 处
（`「字面阅读」「未解决」「没有人做过」「官方 vs 实际」「登记但未运行」「这个结果会很受欢迎」` 等）。
代码围栏内的 `K1:` 与表格内的分隔符是技术例外，见下。**这一项在 P5-E 初稿上是 7 处，不是 0 处**：
改写过程中引入的七个中文冒号（分布在背景、测量台、七个候选各段）在本审计运行时被逐一发现并改写为
句号，之后重跑本层确认归零。写在这里而不是略过，因为"零命中"只有在说明它曾经不是零的时候才有信息量。

**L1-3 结构性套话。** 正文散文里没有连续 bullet（全文唯一的连续列表是结尾的证据链接附录，共 8 行，
由工作令允许）；散文里加粗只有 3 处（语言切换行，以及 Table B 里 `**0.31**`、`**0.36**` 两个中位数），
不构成"大段加粗"。

**L1-4 工具名。** 被点名的具体对象有 Jev、TypeSafe、`jev-1.13.0`、`jev-latest`、`primitives.md`、
`jev-testbench`、`routing.py`、`experiments.py`，以及 `01_primitives` 到 `13b_ambiguous_repeatability`
等实验 ID。开头有一处泛指的"模型"（`如果模型天生就是拿来做 classify、route、score、gate 的`），
它出现在一个思维实验里，指的是这一整类模型而不是某个被藏起来的具名产品，审查后判定不构成空泛表述。
**本项通过，但这一处是全文唯一一处需要判断的地方，所以在这里写明。**

---

## L2 明细

**L2-1 开头。** 从一件具体的事切入 —— Jev 不返回散文，只返回带类型的概率答案 —— 而不是从"随着大模型
的发展"。开篇没有第一人称：`Jev 有意思的地方，不是它又拿了什么 benchmark。` 后接一个短促的陈述，
`是它压根不打算跟你聊天。`，制造"然后呢"的拉力。没有教科书式开头。**P5-D 的开头是 `我第一次看到
Jev 的时候`，P5-E 改成了这一版**，理由不是风格而是归属：见 §"Evidence-contract overrides" 第 6 条。

**L2-2 节奏。**

- 单句成段：106 处；其中 15 字以内的短拍 34 处（`54 次。` / `漂亮。` / `不是。` / `实验没坏。` /
  `分析器坏了。` / `到底是谁动的？` / `为什么？` / `答案是不要。` / `关于这件事，有一个比喻。` 等）。
  规则要求 3 次，实际是其 35 倍以上，本项不存在"接近不达标"的问题。
- 扣主线句：10 处（`先说一分钟背景` / `好，回到实验。` / `到这一步` / `写到这里` / `跑完这些` /
  `还有一件做得挺狠的事` / `而且这还不是唯一一次` / `顺便说一句` / `顺带一提` / `回到开头。`）。
- 疑问句刹车：6 个不同问句，7 次出现（`那 Agent 会不会真的好写一点？` / `那个边界，到底是
  instructions 在承载，还是 criteria 在承载？` / `到底是谁动的？` / `I 比 C 低，是不是 instructions
  更重要？` / `为什么？` ×2 / `到底要不要因为 sunk cost 把它跑掉？`）。
- 小标题：正文 0 个。全文只有一级标题。这条是《SKILL.md》与工作令一致的地方，两边都要求不用
  `##`/`###`。

**L2-3 口语化。**

口语化表达 **32 个不同条目**（规则要求 8–10 个），逐条在文中确认存在后列出：`压根`、`完了`、
`稍微绕`、`差点搞混`、`挺直白`、`最要命`、`顺便说一句`、`漂亮`、`吃掉`、`稳如泰山`、
`底下的水一直在晃`、`挺尴尬`、`挺狠`、`顺带一提`、`顺手`、`一个字都没多`、`锤子`、`钉子`、
`愿意签字`、`混了`、`走回去`、`站不住`、`扎心`、`撞上`、`朴素`、`反过来`、`晃`、`拍板`、
`好看`、`挺`、`搞`、`硬`。

**这张表是这一版审计的产物。** P5-D 那一版在同一层给出了 11 和 35 两个互相矛盾的数，且都没有列出
可核对的清单。现在两个数合成一个，方法也写清楚：先声明候选条目，再逐条回文确认，未出现的候选不计入
（因此这个数只会因为清单变化而变化，不会因为重新数一遍而变化）。若把通用高频词（`就是`、`其实`、
`直接`、`根本`）也算进来，数字会更大，但那些词不是口语化标记，计入会让这个指标失去意义。

**P5-E → P5-E1 的减少一项，逐项说明。** 减少的是 `撑不住`，它只出现在被 P5-E1 删掉的那句
（`删掉那些证据撑不住的故事`）里。**没有为补位新增任何一项**，这是工作令 §15 的直接要求。注意文中
仍有 `支撑不了` 两处（`不能…` 与 `n = 3…` 两段），但那是标准书面表达，从来不在本清单里，也不应
因为这一处删除而被追认为口语化标记 —— 清单不变，数字只会随文本变。

论述中的故意打破 5 处：`这个读法站不住。` 独立成段打断一个正在成立的论断；`实验没坏。` 与
`分析器坏了。` 两段之间没有连接词；`12 次。一条都不许多。` 用重复加强而不是推进；
`这个效应大到足以让人立刻动笔。但它有两个问题。` 在同一段里硬转折；`但还有一个故事要删。`
在结论已经收束之后重新开题。

自嘲/承认不足 4 处：`这个 45 / 45 一开始写错过`、`这里有两件事一开始差点搞混`、
`然后又出了一件挺尴尬的事`、`这件事不打算写成英雄叙事`。

**未做到的一项：情绪标点。** 规则要求 `。。。` / `？？？` / `= =` 至少出现一种，本文 0 处。
理由记在 §"Evidence-contract overrides"。按《SKILL.md》的通过标准，本层四项中三项通过即算通过，
所以 L2-3 判 ✅，但这一项的空缺被明确写出来而不是略过。

**L2-4 二次确认。** 改写过程中最容易被重新引入的就是这三类标点，因此这一项是在全部编辑完成之后重跑的，
不是在初稿上跑的。重跑结果同上：0 处。中文冒号是在这一步被抓出来的（见 L1-2）。

---

## L3 明细

**L3-1 观点支撑。** 每个核心论断都带具体数字或具体代码位置，没有只有论断没有例证的空泛段落。
`效应很大 ≠ 原因已确定` 是全文最像格言的一句，它前面是 K1 的 `0.05 < 0.10`，后面是两个被明确拒绝
的总结，支撑是够的。

**L3-2 知识输出。** 三种原语的介绍走的是"先花一分钟说清楚 Jev 到底是个什么东西，不然下面看不懂"，
然后一段一个，全部控制在一两句以内，是《SKILL.md》说的"聊着聊着顺手掏出来"，不是"下面我来介绍一下"。
calibration 的分组作用域、cookbook 的标签翻转、chaos test 的 jitter floor 都是随论述顺带带出的，
没有一节是科普节。**P5-E 在这一层新增了一处技术说明而不是一处科普**：Choice 的展示层量化 —— API 返回
值按两位小数显示时个别记录相加不严格等于 1。它是被人工评审确认的事实修复，写在背景段而不是单独成节。

**L3-3 文化升维。** 按类型取材，从具体事件连到更大的参照物，但参照物是方法论的而不是文学的。
`删故事的能力` 连到"一个用来检验发现的仓库收到了否定的检验结果"；结尾连到 Agentic Engineering 与
认知负债。**没有引用任何文学作品、历史人物或哲学概念**：一个测量仓库没有资格借用它们，硬借就是
"不能因为手上有锤子就把问题看成钉子"的镜像违例。P5-E 新增的唯一比喻是猩猩与火，它是全文唯一一次
比喻性升维，出现一次，不扩写，也不承担论断。

**L3-4 对立面与同理心。** 每一层拆解都先把最诱人的读法完整说出来，再拆 —— `这么写出来，听起来像
模型在一个很微妙的边界上做了判断。` / `这个结果太容易写成「模型不敢执行」了。` / `看到这里，很容易
产生一个冲动。` / `I 比 C 低，是不是 instructions 更重要？`。读者如果正是这么想的，会先看到自己的
立场被准确复述，然后才看到它为什么站不住。

**L3-5 类型专项（调查实验型）。** 层层递进的发现仍在，四层，每层都先给数字再拆：批处理 4.2647× →
稳定标签 → 0.61 门槛 → 路由 4/4。P5-E 在这一层做了一处结构性修改：第四个候选之后不再逐个宣告
"第 N 个故事没了"，而是在四段之后用一段把四个候选的出局原因一并结算，并明确区分"被 prior art
降级"和"本来就不是关于 Jev 的发现"两类。**这既是密度调整，也是事实修复** —— 见 §"Evidence-contract
overrides" 第 7 条。

**L3-6 逐一展示。** 四个候选逐条展示、逐条拆解，每条都带自己的说明，不是一次性罗列。五个退休实验
只留两个展开（`10_state_length`、`11_language_pair`），剩下三个不逐一铺开。

---

## L4 明细

**L4-1 温度感。** 情绪表达全部是对**过程**的陈述，不是对作者内心的陈述，也不是知识性描述：`这里有两件
事一开始差点搞混`、`这条在四个候选里看起来最有意思`、`然后又出了一件挺尴尬的事`、`这个效应大到足以让人
立刻动笔`。**没有一处体感描写**（没有"愣住了"、没有"拍桌子"），也**没有一处心理断言**（没有"我当时
很想"、"我意识到"）。P5-D 有几处这类心理陈述，P5-E 逐条改成了对材料或过程的陈述，理由记在 §"Evidence-
contract overrides" 第 6 条。一件真的发生过的事，过程本身就够。

**L4-2 独特性。** 这个角度换一个 AI 博主写不出来，而且 P5-E 之后更难仿：它的独特之处不在文风上，
在素材上 —— 一个附预注册、附带缺陷并被保留的分析器、附勘误表、附两条不可变日志的测量台，**外加一条
诚实的生产关系披露**。别人可以模仿这个语气，但模仿不了"四个自己写好的候选全部被删掉"这件事，也模仿
不了"这是一篇主要由 AI 起草、作者决定它说什么的文章，而文章自己把这件事写在正文里"。

**L4-3 姿态。** 全文没有滑进"导师在教学生"：三条工程经验用的是"手上剩下三条能迁移到别处的东西"，
不是"你应该这样做"；风险陈述用的是"这条限制是写下来的"，不是"大家一定要注意"。也没有滑进营销姿态 ——
`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET` 是一次去推广，不是一次推广。**P5-E 新增的结尾是这一层最
容易翻车的地方**：把认知负债写成本项目的方法论输出，就会变成推销一个概念。处理方式是把它明确降级为
工作概念、明确声明不可测量、并把"外部机制不是理解"作为该段落的结论而不是余韵，因此它落在自省而不是
主张上。

**L4-4 心流。** 两处刻意减速：`07_instruction_precision` 的转折点（`到底是谁动的？`），以及 P3 的
12 次上限（`12 次。一条都不许多。` 单独成段）。两处减速之后都立刻回到主线，没有留在情绪里。结尾新增
的披露段是第三处减速，但它不是情绪性的 —— 它是全文语速最平的一段，这是有意的。

---

## Technical exceptions

允许的技术例外，逐条列出实际用到的地方。**这些是形式上的破例，不是风格上的破例**：`##` 标题禁令、
引号规则、口语规则都不适用于下列内容，因为没有可替代的中文写法。

| Exception | Where it appears | Why it is permitted |
|---|---|---|
| H1 标题内的中文冒号 | `# 54 次 Jev 调用之后：一个 Agentic Engineering 实验台和一笔认知负债` | 标题不是散文；冒号是工作令 §18 推荐的标题形式 |
| Markdown 链接 | 语言切换行；结尾证据链接附录的 8 条；勘误表、claim contract、AGENTIC 文档与 `LICENSE` 的行内链接 | 链接不是散文 |
| 文件路径与仓库相对路径 | `results/usage.jsonl`、`results/`、`experiments.py`、`routing.py`、`docs/evidence/v0.1.0/` 下的产物 | 路径是标识符，改写会改变指向 |
| commit / SHA / 哈希 | 两个 canonical 日志的 SHA-256 前缀 `38e67630…`、`17f36f75…`；`git show` | 哈希是标识符，必须逐字节准确 |
| state string | `PUBLIC_NOVELTY_UNRESOLVED`、`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`、`P3_KILL_NO_SINGLE_FIELD_ATTRIBUTION`、`FIELD_ALIGNMENT_CAVEAT`、`ACTUAL_HANDLER_EXECUTION_UNTESTED`、`SUSPENDED` | 冻结证据与审计里的规范字符串，改动即失真 |
| 代码块 | `K1: \|I_med − C_med\| < 0.1 → 归因失败`；`\|I − C\| = 0.05` 与 `threshold = 0.10`；四个 state string；认知负债的非正式表示 | 代码块内的 `:` 是语法，不是中文冒号 |
| 数学运算符 | `≠`、`×`、`−`、`→`、`2×2`、`k=3`、`n = 3`、`0–3`、`≈` | 符号是技术记号 |
| 实验 ID | `01_primitives` 至 `13b_ambiguous_repeatability`、`07_instruction_precision`、`10_state_length`、`11_language_pair`、`04_confidence`、`06_composite_scoring`、`12_function_routing` | 注册表里的规范 ID |
| 英文原样引文 | `nothing in the docs says 0.8 is the right line`、`P(yes)`、`accept`、`other`、`human_review`、`needs_human_review`、`usage`、`evidence layer` | 代码注释与 API 字段的字面值 |
| **Table A** — P3 的 2×2 设计 | 一个 4 行 3 列表 | 需要保留的设计表 |
| **Table B** — P3 原始测量值 | 一个 4 行 4 列表 | 需要保留的测量表 |
| 证据链接附录整体 | `---` 之后的"证据与复现"一段 | 非叙事风格，附录被排除在字符预算之外 |
| License | 结尾一行，链接 `LICENSE` | 只写许可名或链接，禁止任何宽泛的许可措辞 |

**全文除以上各处外没有表格。**

---

## Evidence-contract overrides

优先顺序是：冻结证据 > `BLOG_CLAIM_CONTRACT` > 历史 provenance > 风格。下面每一处都是这条顺序真正
产生代价的地方。**每一次都是证据或归属赢。**

**1. 风格要一个"卧槽"的结果，这篇的诚实结局是一个 null。**
《SKILL.md》的写作原型把文章推向一个回报时刻。这个项目真实的回报是 P3 的负结果，外加一行
`NO_STRONG_JEV_SPECIFIC_NOVEL_FINDING_YET`。处理方式是把文章结构改成**表观成果逐一拆解** ——
升番曲线还在往上走，但往上走的是拆解的质量，不是发现的体量。

**2. 风格要"敢下判断"，合同禁止其中大多数。**
文章确实下判断，但下的是关于**方法**的判断，而证据完全支撑它。关于 Jev 的判断严格限制在合同划定的
范围内。

**3. L2-3 的情绪标点按规则未做。**
`。。。` / `？？？` / `= =` 这类标点在这篇里只有两种来源：伪造的情绪，或者刻意模仿的网红口癖。两者
都被排除。这是 L2-3 四项里唯一未做到的一项，代价被记在这里而不是被抹平。

**4. 人物画像法 = `NOT_APPLICABLE`。**
《SKILL.md》的 L3 有一节人物画像法，把冷数字变成有温度的人。这个项目里没有第三个人可以画像 ——
全部 state 是合成的，全部调用是 agent 发出的，没有任何人出现在这些证据里。禁止为了通过检查而编造
一个。**这一项判 `NOT_APPLICABLE`，不是"通过"，也不是"未通过"。**

**5. 固定尾部、署名与联系方式属于《SKILL.md》的作者，不使用。**
文章以删故事的回扣结束，以作者自己的判断收尾，没有借用任何不属于这个仓库的收尾元素。

**6. P5-E 新增：风格想要的"我心路历程"，归属审计不允许。**
P5-D 有一批第一人称心理与履历陈述 —— `我当时冒出来的问题特别朴素`、`我当时是真的觉得这条挺有意思`、
`大到我看到它的第一反应，是想赶紧写点什么`、`我不是第一次做实验`。它们在风格上是有效的（L4-1 温度感
靠它们撑），但它们是**关于作者内心的断言，而作者无法为自己作证，仓库也无法核对它们**。P5-E 逐条改成
了对材料或过程的陈述：`一开始的疑问很朴素`、`这条在四个候选里看起来最有意思`、`这个效应大到足以让人
立刻动笔`，履历句整句删除。**代价是真实的** —— 文章的温度感从"作者在现场"降到了"过程在现场"。这是
P5-E 在 L4-1 上付的钱，记在这里。

**7. P5-E 新增：风格想要整齐的四个"故事没了"，事实不允许。**
P5-D 用四个同构的段落收掉四个候选，读者得到的是一个整齐的节奏。但四个候选的出局原因并不整齐：批处理
和重复性是被官方与公开 prior art 降级的，0.61 门槛和路由拦截从来就不是关于 Jev 的发现，而是测量台自己
的 policy 走了一遍的必然结果。四个同构的 `第N个故事没了` 会把这两种完全不同的失败压成一种。P5-E 删掉
了这个鼓点，改成四段之后一段结算，并把两类原因分开写。**节奏的整齐在这里被事实换掉了。**

**8. 全篇最重要的叙事装置是一个可能自己长出论断的装置。**
`删故事` 离 `否定了七项发现` 只有一次压缩的距离，而后者是假的 —— 七个候选里没有一个是"被证伪的发现"，
它们全部是**没有通过分诊的候选**。因此它在 claim audit 里被单独列成 C-66 并归入 `B` 类而不是 `A` 类。
P5-E 保住了它作为叙事装置的地位（正文一次、结尾一次），同时把它的断言力压在候选清单的范围内。
**P5-E1 把结尾那一次从两遍压到一遍**，装置的断言力没有变化，但重复的次数少了一次 —— 见 §"Over-stylization
check" 问题三。

**9. P5-E1 新增：风格指标被允许下降，而且真的降了一项。**
工作令 §15 明令禁止为了维持计数而新增任何口语化手段，并写明"风格指标可以下降，人的阅读质量优先"。
本版执行的结果是口语化 33 → 32、单句成段 107 → 106，两项都降。**这是这篇文章第一次出现风格指标下降
而没有任何补偿性新增**，值得记在这里：它说明前面那些数字不是在追求一个下限，而是文本的副产品 ——
文本变准，数字随之变化，哪个方向都可以接受。**如果哪一天这两个数为了回到某个旧值而被重新推高，
那才是这一层真正出事的时候。**

---

## 这一层没有做的事

`STYLE_AUDIT` 回答"有没有太刻意"，而不只是"有没有达到最低数量"。就这个问题而言，本版审计的结论是：
**L1 与 L2-4 是零命中，不是接近通过；L2-2 的各项远超下限，不存在凑数的风险；唯一需要人工判断的地方
是 L1-4 的那一个泛指"模型"，已经在明细里写明。** 反过来，本版审计没有发现任何一处"为了达到数量而
硬塞"的痕迹 —— 这在 32 个口语化条目和 106 个单句成段的规模上是一个真实的结论，不是一句客气话。

**P5-E1 增加的反向检查见上面的 §"Over-stylization check"。** 那一节的结论和这一节是同一条：四个
过密问题里三个从一开始就是否，一个在 P5-E 是"是"、在 P5-E1 被修成"否"，而修的方式是**删掉一句**而不是
补一句。**这一版审计没有任何一个数字是因为想让文章"更像"而变动的。**
