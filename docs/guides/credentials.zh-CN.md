# 凭据

[English](credentials.md) | **简体中文**

本仓库在其真实运行期间使用过一个真实的 TypeSafe API key。本页描述这个 key 是如何被解析的，以及 ——
更有用的部分 —— 这套方案**不**能给你买到什么。

> **请先读这一段：** 本文档与 [CLAUDE.md](../../CLAUDE.md) 中的规则，是**一个合作的 agent 会遵守的
> 约定。它们不是安全边界。** 一个有文件访问权限的 agent 或程序可以读取 `.secrets/typesafe.env`。
> 说不是这样，就是在对一份真实凭据作虚假陈述。真正存在的边界见 [SECURITY.md](../../SECURITY.md)。

---

## 1. 解析顺序

Key 只从两个地方读取，按此顺序，别无其他：

1. 环境变量 **`TYPESAFE_API_KEY`**，当其值非空白时；
2. **`<repo>/.secrets/typesafe.env`**，一个被 gitignore 的本地文件；
3. 两者都没有 —— 此时每一个需要 API 的命令都会在花掉任何东西之前停止。

环境变量优先，因此轮换的或一次性的 key 可以为某一个终端设置而不必改动文件。**当环境变量中存在值时，
文件完全不会被读取** —— 一个损坏的文件无法拖垮一个已被显式配置好的会话。

加载器 **fail closed**。来源缺失、为空、格式错误、重复或不可读，都会在请求发出**之前**终止运行，而不是
带着一个猜测继续。

## 2. 命令会告诉你关于 key 的什么

任何命令都不会打印 key 本身、它的长度、前缀、后缀，或它的哈希。每个接触凭据的命令只报告以下之一：

```text
TYPESAFE_API_KEY: missing
TYPESAFE_API_KEY: exists (source=environment)
TYPESAFE_API_KEY: exists (source=local-secret-file)
TYPESAFE_API_KEY: unusable (malformed | duplicate-key | unreadable)
```

不存在任何为展示而返回 key 的代码路径，也没有任何状态字符串携带派生出的标识符。这是刻意的：一个没有打印
路径的设计，才使「绝不泄露」成为事实，而不是一个愿景。

## 3. 为单次会话设置 key

不把它留在 shell 历史里：

```powershell
$secureKey = Read-Host "Paste TypeSafe API key" -AsSecureString
$env:TYPESAFE_API_KEY = [System.Net.NetworkCredential]::new("", $secureKey).Password
Remove-Variable secureKey
```

## 4. 持久化本地文件

会话变量在终端关闭时消失。为了避免重复粘贴 key，把它放进 `.secrets/typesafe.env` —— 在工作目录之内，
在版本控制之外。

格式是一行，没有引号，没有 shell 语法：

```text
# Local credentials for this machine. Never commit this file.

TYPESAFE_API_KEY=<your-key>
```

空行与 `#` 注释会被忽略；值是 `=` 之后的内容并去除首尾空白。**文件中的任何内容都不会被展开、替换或
执行** —— `$(...)`、`${VAR}`、反引号和引号都是普通字符，也不存在行内注释语法（行尾的 `# comment`
会成为值的一部分）。两行 `TYPESAFE_API_KEY`、一个意料之外的名称、或一行不是赋值的内容，都是**错误而
非静默选择**，加载器会停止。空值意味着*缺失*。

`.secrets.example/typesafe.env` 是被提交的模板，其中只有一个显然的占位符
（`YOUR_TYPESAFE_API_KEY_HERE`）。`.secrets/` 不会：

```console
$ git check-ignore -v .secrets/typesafe.env
.gitignore:28:.secrets/    .secrets/typesafe.env
```

出于同样的原因，`git add --dry-run .secrets/typesafe.env` 会被拒绝，而
`git add --dry-run .secrets.example/typesafe.env` 会成功 —— 那个模板本来就是用来提交的。

---

## 5. 这套方案给你买到了什么，没买到什么

它把 key 挡在**版本控制之外、diff 之外、聊天记录之外**。它仍然是一个磁盘上的明文文件。对此要头脑清醒：

- 它适用于**你自己控制的机器上的个人实验仓库** —— 不适用于共享主机，也不适合作为生产级密钥管理的范本。
- 它**以你的身份运行的任何东西**都可读，也可被监视该目录的备份、索引与云同步工具读取 —— 如果仓库位于
  同步文件夹内，则包括 OneDrive、Dropbox 和 Windows Search。
- 该文件的默认 Windows ACL 从父目录继承：`Administrators`、`SYSTEM`、`Authenticated Users` 和
  `BUILTIN\Users`（读）。在单用户机器上，这大致就是「你，以及任何以管理员身份运行的东西」，但它**不是**
  每用户锁，第二个本地账户可以读这个文件。本仓库不管理该 ACL。收紧它是可选的，如果你要这么做，请对**该
  文件**操作 —— 不要对仓库目录操作，也不要以丢掉 `SYSTEM` 或你自己账户的方式操作。
- **有文件访问权限的 agent 可以读它。** [CLAUDE.md](../../CLAUDE.md) 要求 agent 不要这么做，而这条
  指令是约定，不是机制。

### 四条真正是机制的边界

上面的规则是约定。下面这些不是，而且当你改动这里的任何东西时，要保证继续成立的就是它们：

| 边界 | 它是什么 |
|---|---|
| **`.gitignore`** | `.secrets/`、`*.env`、`*.secret`、`*.secrets`。key 不可能被意外提交，而 `git check-ignore` 才是**证明**它的检查 —— 不是文档里的一句注释。 |
| **Fail closed** | 来源缺失、为空、格式错误、重复或不可读，都会在请求发出之前终止运行。 |
| **无打印路径** | 加载器没有任何为展示而返回 key 的函数；状态字符串不携带派生标识符；`scrub_secrets` 覆盖引用了响应的错误文本。 |
| **操作系统权限** | 文件的 ACL —— 本仓库**不**管理它。见上面的注意。 |

这四条中任何一条被削弱，上面的约定就不再足够。把对其中任何一条的改动视为安全变更。

---

## 6. 如果你怀疑 key 已泄露

被提交、被粘贴、被同步、被截图，或被打印进日志 —— 补救办法是一样的：

1. **首先在 TypeSafe Console 中吊销该 key 并签发新的。先做这一步。** 事后重写历史并不能撤销一次泄露；
   泄露的凭据从泄露那一刻起就已经失陷，唯一有帮助的事情是让它停止工作。
2. **然后**清理：更新 `.secrets/typesafe.env` 或会话变量，并检查这次暴露是否到达了日志、CI 记录或同步
   文件夹。
3. **再然后，如果它进入过某次提交**，考虑清理历史 —— 但只能在吊销之后，并且只能是有意为之。重写已发布
   的历史是有破坏性的，也不能替代第 1 步。

> **运行实验时绝不启用 `TYPESAFE_LOG_LEVEL=debug`。** SDK 会脱敏密钥 *header*，但明确**不**脱敏请求或
> 响应 *body*，因此 debug 日志会把你完整的 `state` 和每一个答案都打印出来。本项目中的任何东西都不会
> 启用它。

如何报告本仓库中的安全问题，见 [SECURITY.md](../../SECURITY.md)。
