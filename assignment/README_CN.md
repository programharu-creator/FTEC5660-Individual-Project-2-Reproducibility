# FTEC5660：LiTS + DeepSeek 复现作业

当前阶段：已完成 9 组正式实验、报告和演示材料。结果见 [RESULTS_CN.md](deliverables/RESULTS_CN.md)。GitHub 推送和 Zoom 录像链接仍待完成。

## 实验内容

复现 LiTS 仓库中的 MATH500 数学推理 MCTS 流程。在同一个 DeepSeek 模型、同一组题目和固定搜索参数下，将最大搜索步数设为 5、10、15，比较正确率、实际搜索深度、API 调用次数、token 用量和耗时。

论文参考为 [LiTS v2](https://arxiv.org/html/2603.00631v2) 的表 6。论文的 ReST MCTS 是 Llama3-8B 和其评分模型设置下的 100 题实验；本作业首先开展 API 版、小样本复现。模型、评分模型、题数和部分运行设置有差别，不能声称严格重现论文的 37%。

详细固定参数见 [experiment_plan.json](experiment_plan.json)。论文、仓库工作流、我们测量的结果必须在报告中分开写清楚。

## 按步骤操作

在项目根目录打开 PowerShell，无须激活环境：

1. 环境和数据检查（不需要 API key）：

   `.\.venv\Scripts\python.exe -m assignment.study preflight`

2. 将 DeepSeek API key 填入项目根目录 `.env` 的 `DEEPSEEK_API_KEY=` 后面。该文件已被 Git 忽略，不要写进报告或提交到 GitHub。不要把 key 放进命令行参数。

3. 查看试跑设置（不会调用模型）：

   `.\.venv\Scripts\python.exe -m assignment.study plan --phase smoke`

4. 最小连通性和流程试跑（1 题，需要 key，会产生 API 费用）：

   `.\.venv\Scripts\python.exe -m assignment.study run --phase smoke`

5. 小规模试验（同一组前 5 题，先查看耗时和用量）：

   `.\.venv\Scripts\python.exe -m assignment.study run --phase pilot --max-steps 10 --seed 11`

6. 再决定正式实验规模。正式计划为 30 题 × 3 个步数设置 × 3 次重复。每个组合单独运行，例如：

   `.\.venv\Scripts\python.exe -m assignment.study run --phase formal --max-steps 10 --seed 11`

所有真实运行在唯一的新目录中保存配置、执行日志、API 用量和完整搜索产物。程序拒绝覆盖已有结果。失败或被调用次数上限中断的运行要保留并标为不完整，不能当成完整实验计入准确率。

## 环境和复现

上游提交：`25e94d862cb4514c22d9a80a635e392461769df7`。

Windows 独立 Python 3.12.12。这里只安装数学 API 路径依赖，使用源码模块运行；不启用本地 GPU 模型、数据库、地理工具或记忆后端。依赖的精确版本保存在 `requirements-api.lock.txt`。

在另一台机器重建：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r assignment/requirements-api.lock.txt
.\.venv\Scripts\python.exe -m assignment.prepare_data
.\.venv\Scripts\python.exe -m assignment.study preflight
```

可复查的适配改动：
- 删除 `lits/config.py` 中未使用的 torch 导入，使 API 路径不依赖 GPU 软件栈。
- 按 DeepSeek 官方格式发送 thinking 开关；所有实验关闭模型内部 thinking。
- 用本地固定版本数据替代上游未固定版本的在线数据加载。任务名称和作者数值检查器保持一致。
- 显式启用深度上限；不同组仅改变 max_steps。Python/NumPy seed 用于本地随机过程，不保证远端模型逐次一致。

最大步数限制的是树上单条推理路径长度。总调用次数还取决于分支、搜索迭代、评分和终止检查。API 评估中的答案整理/投票也会调用模型，其用量与搜索分别记录。

## 提交物

- 不超过 10 页的报告：使用 `REPORT_OUTLINE.md`。
- GitHub 仓库：包括清楚的安装、运行步骤、实验脚本、变更 commits 和脱敏结果。
- 不超过 15 分钟的 Zoom 演示录像链接：按 `PRESENTATION_OUTLINE.md` 准备。

当前本地 Git 分支用于保留改动，尚未创建或推送个人 GitHub 仓库。

DeepSeek stable tool API: strict is omitted on the normal endpoint (beta-only feature); upstream local tool-result validation is retained. See https://api-docs.deepseek.com/guides/tool_calls/ .

Cost reporting: use api_calls.jsonl token totals and the provider billing dashboard. Ignore upstream automatic dollar estimates unless their assumed prices are replaced with the dated DeepSeek prices, including cache tiers. No monetary estimate has been measured or reported by this setup.

## Restore saved evidence without API calls

Run python assignment/reporting/restore_evidence.py, then install assignment/reporting/requirements-report.txt and run python assignment/reporting/build_deliverables.py. The existing environment has no pip; use uv pip, or create a fresh venv with standard python -m venv. Report generation requires no key and no model inference.

Recorded decoding is role-specific. The plan model top_p is a default, while existing binary-scoring calls also use 0.95. Exact request values are in api_calls.jsonl.

Push the existing local Git history to a new personal repository to preserve the stepwise commits. The ZIP contains source and evidence, not the .git directory or private .env.
