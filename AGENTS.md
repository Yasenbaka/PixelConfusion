# 提交信息规范

> 本文件是提交信息规范的唯一维护文件；`AGENT.md` 仅为索引，不重复维护规则。

所有提交必须使用以下格式。

## 标题

```text
<英文type>(<英文scope>): <中文title>
```

- `type`：英文，例如 `feat`、`fix`、`docs`、`chore`、`refactor`、`test`。
- `scope`：英文小写，例如 `ui`、`core`、`license`、`agent`。
- `title`：中文，简明说明本次提交。

## 描述

标题后空一行，工作细则按以下格式逐条书写：

```text
1、工作细则内容；
2、工作细则内容；
3、工作细则内容；
```

每条工作细则必须另起一行，使用中文序号、顿号和分号，不要在行首添加 Markdown 列表符号。

## 示例

```text
docs(license): 添加 MIT 许可证

1、新增 MIT 许可证文件并注明版权人；
2、在 README 中补充原创代码的许可证说明；
3、保留 gilbert2d 的 BSD-2-Clause 第三方许可声明；
```
