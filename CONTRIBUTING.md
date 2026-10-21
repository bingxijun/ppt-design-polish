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

Publishing a matching `v<package.json version>` release triggers `release-package`, which builds a reproducible portable skill ZIP and SHA-256 file and uploads them as release assets. For a local build, run `python3 scripts/package_release.py --output-dir /absolute/fresh-directory`.

发布与 `package.json` 版本相符的 `v<版本号>` release 后，自动构建可复现的安装 ZIP 和 SHA-256 文件并上传。也可使用上方命令本地构建，输出目录中应没有已有的发布文件。

Maintainers can also publish by committing `docs/releases/<package version>.md` to `main`, beginning with `# v<version> <title>`. This is an intentional publication trigger: the workflow reruns tests and example checks, creates a release at that exact commit, and attaches the ZIP and checksum. An already-published version is skipped. Editing other files alone does not publish a release. The workflow uses the repository's existing Actions token, without a personal token or browser login. See the [GitHub CLI release command](https://cli.github.com/manual/gh_release_create).

维护者也可将 `docs/releases/<package 版本>.md` 提交到 `main`，首行为 `# v<版本> <标题>`。这是明确的发布触发操作：工作流重新运行测试及示例检查，在该提交创建 release 并附上安装包与校验文件；已发布版本会跳过。单独修改其他文件不会发布。流程使用仓库已有的 Actions 令牌，无需个人令牌或浏览器登录。

Use issues or pull requests for feedback. Source files, fonts, images, and examples must be yours to share. Contributions are offered under the project's MIT license, with existing third-party licenses preserved.

欢迎通过 issue 或 PR 反馈。请确认有权分享所提交的源文件、字体、图片和示例；贡献采用项目 MIT 许可，已有第三方许可继续保留。
