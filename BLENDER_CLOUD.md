# Blender 云端运行

本仓库已经配置 `Blender Cloud` GitHub Actions 工作流。它用于游戏资产的自动构建和验证，不是可以远程拖动鼠标的 Blender 桌面。

## 不用在电脑上安装 Blender

进入 [Blender Cloud 任务页面](https://github.com/tangmuyou/lulu-game/actions/workflows/blender-cloud.yml)。

- 修改 `main` 分支中的 `tools/blender/` 脚本会自动触发。
- 也可以点击 **Run workflow → Run workflow** 手动运行。
- 点击一次具体运行记录，绿色表示成功；失败时请查看日志，不要把失败的任务当作成品。
- 在运行记录下方的 **Artifacts** 下载 `blender-cloud-test-数字`。

## 当前会生成什么

目前是一个带圆角、木纹贴图和绿色绑带的小木箱，用来检查云端是否真正工作，并非噜噜村的正式美术成品。

```text
model/
  cloud_test_crate.glb       # 内嵌贴图的 GLB 模型
  cloud_test_crate.blend     # Blender 工程，贴图已打包
textures/
  wood_basecolor.png
preview/
  front.png
  right.png
  back.png
  left.png
logs/
  blender.log
validation.json
```

预览为四个环绕视角、512×512 的透明 PNG，由 **导出的 GLB 重新导入 Blender 后** 使用 Cycles CPU 渲染。

脚本校验 GLB 文件头、非空网格、内嵌贴图、Blender 重新导入及必要输出。它不会谎报 Godot 实机测试；`validation.json` 中的 `godot_runtime_tested` 为 `false`。

## 已配置的运行方式

- 官方 Blender 4.5.14 Linux 安装包，下载后核对官方 SHA-256 清单。
- GitHub 标准 `ubuntu-24.04` 云端 CPU runner，不使用付费 GPU 或大型 runner。
- 只有仓库为公开状态时才运行；改为私有后此工作流会跳过，避免自动产生私有仓库用量。
- 单次任务最长 15 分钟，没有定时任务，也没有常驻服务器。
- 下载产物保留 7 天。重要文件请另行保存。
- 工作流只需要读取代码的权限，不需要你提交云服务密码或 API 密钥。

GitHub 官方说明：公开仓库使用标准 GitHub-hosted runner 的 Actions 用量免费。参见 [GitHub Actions 计费](https://docs.github.com/en/billing/concepts/product-billing/github-actions)。不要将这里的配置理解为所有 GitHub、存储服务或云服务器都免费。

## 隐私与素材

这个仓库当前是公开仓库，里面的代码和上传的文件可能被其他人看到。不要提交账号密码、API 密钥、私人文件或尚未允许公开的商业素材。此次测试脚本从零生成测试木箱，没有上传你以往的模型包。

## 以后如何调整

当前脚本位于 `tools/blender/smoke_test.py`，云端配置位于 `.github/workflows/blender-cloud.yml`。后续可以修改或新增建模脚本，按同样流程生成模型、材质和预览；具体资产仍需要单独制作和验收。
