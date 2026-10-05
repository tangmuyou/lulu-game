# Blender 技能安装

安装范围：本 GitHub 仓库与 GitHub Actions 云端任务。不是给 ChatGPT 账号全局安装插件，也不是修改你的电脑。

## 安装的精简组合

| 组件 | 固定版本 | 用途 |
| --- | --- | --- |
| majidmanzarpour/blender-game-skills | f0ef29385a03de139957e6f700b801cdc00b7e29 | 参考图建模流程、网格验证、导出回读等脚本 |
| MartinRapcan/blender-claude-skill | 964cfe73bb1d15ff5b1603c625ecf067fb8d11bc | 无界面 Blender 脚本规范和基础函数 |
| Khronos glTF-Validator | 2.0.0-dev.3.10 | GLB 格式与数据检查（上游发布版本名包含 dev） |

两套技能采用 Git 子模块固定到完整提交号，保留各自 MIT 许可证。Khronos 工具通过其官方 npm 包安装，使用 Apache-2.0 许可证；禁用 npm 安装脚本。每次任务都会检查技能提交号和校验器版本，不自动追踪上游 main。

Blender 保持 4.5.14，继续使用标准 Ubuntu CPU runner；没有增加付费 GPU、密钥、远程桌面或定时任务。公开仓库限制、15 分钟超时、产物保留 7 天的设置不变。

## 已接入的检查

- 原来的真实木箱建模、GLB 导出和四角度预览保持不变。
- 检查技能文件存在、提交号正确、许可证存在，编译检查技能 Python 文件。
- 实际调用可靠脚本技能中的清场、包围盒、相机和场景报告函数。
- 实际调用游戏技能中的网格校验器；额外禁止空网格集合假通过。
- 故意制作负缩放测试副本，确认校验器会拒绝。
- 对上游 roundtrip.py 做单点内存适配，以 CPU Cycles 替代 Workbench；不修改上游文件。
- Khronos 检查真实 GLB，同时确认被故意破坏文件头的内存副本会被拒绝。
- 检查生成的 PNG 不是全透明或空白。

`AGENTS.md` 与 `.agents/skills/lulu-blender-cloud/SKILL.md` 是后续制作入口。上游技能路径也链接在 `.agents/skills/`，在新克隆的工作区需先初始化 Git 子模块，云端任务会自动完成。

## 报告与技能包

运行 `Blender Cloud` 后，下载任务产物中的：

- `skills_installation.json`：安装版本与文件检查。
- `skills_qa.json`：脚本与 CPU 兼容性实测结果。
- `qa/mesh_validation.json`：真实模型网格检查。
- `qa/roundtrip/`：导出回读报告和真实 CPU 预览。
- `gltf_validation.json`、`gltf_validation_summary.json`：Khronos 检查。
- `expected_*` 报告：故意错误样本被拦截的证据，不是正式资产失败。
- `installed_blender_skills.zip`：两套上游技能的完整文件与许可证。

只有实际任务成功及相应报告通过，才能声称安装已验证。安装和测试木箱通过不证明所有上游功能、正式资产美术质量、参考图还原度、绑定、烘焙、动画或提速比例；尚未做 Godot 实机测试。

Capybala 的 Blender 5.1 函数库、MCP 桌面服务，以及带非商业限制的工具未纳入本次精简安装。
