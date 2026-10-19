# Contributing / 参与贡献

Improvements should solve observable presentation problems. Include the smallest reproducible input, the exported result, and the expected behavior. Remove confidential source material before opening an issue.

改进应对应可观察的演示文稿问题。请提供最小复现输入、导出结果与预期表现；提交 issue 前移除机密材料。

```bash
python3 -m unittest discover -s scripts -p 'test_*.py' -v
npm install
python3 scripts/check_example.py
```

For design changes, render the final PPTX and inspect the affected pages. Unit tests cannot establish visual quality. Keep English and Chinese user-facing documentation aligned, and preserve third-party notices.

设计改动需从最终 PPTX 渲染并检查受影响页面。单元测试不能证明视觉质量。用户说明保持中英对应，保留第三方署名及许可。

Use issues or pull requests for feedback. Source files, fonts, images, and examples must be yours to share. Contributions are offered under the project's MIT license, with existing third-party licenses preserved.

欢迎通过 issue 或 PR 反馈。请确认有权分享所提交的源文件、字体、图片和示例；贡献采用项目 MIT 许可，已有第三方许可继续保留。
