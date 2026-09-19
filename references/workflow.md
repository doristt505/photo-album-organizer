# 执行与恢复

Python 3.10+，无第三方依赖。脚本执行助手视觉审核后的计划，不自动识别场景或判断审美。

计划 JSON：`{"groups":[{"id":"scene-01","keeper":"trip/b.jpg","files":["trip/a.jpg","trip/b.jpg"],"reason":"主体清楚，构图干净"}]}`。

所有文件路径相对源目录。每个输入照片恰好归入一个组，单张照片也建组。输出必须为源目录之外的全新目录。执行前检查计划覆盖范围和可用磁盘空间。

```text
python scripts/album.py apply --source SOURCE --plan PLAN.json --output NEW_OUTPUT
python scripts/album.py restore --album OUTPUT --file trip/a.jpg --output NEW_RESTORE
```

输出 `highlights/`、`memories/`、`manifest.jsonl`。恢复复制到全新目录，仓内版本保留。没有删除功能。中断时保留输出及日志，另选新目录重试；不自动清理失败输出。修改已有整理时需另行根据现存状态做可逆调整并备份清单，不覆盖现有导出。
