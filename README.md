# PixelConfusion

本地图片混淆与复原桌面工具，所有处理都在本机完成。

在此文件夹打开终端，运行：

```powershell
python main.py
```

程序会打开本地窗口。选图和处理均在电脑上完成。入口为 `main.py`，打包脚本为 `build.py`，业务代码按职责拆在 `pixelconfusion/`：

```text
pixelconfusion/
├── app.py              # 窗口、状态与交互控制
├── batch.py            # 批量结果记录
├── console.py          # 控制台输出编码
├── core/               # Gilbert / Arnold 算法、变换器、图片读写
├── paths.py            # 源码与打包后的资源路径
├── ui/
│   ├── theme.py        # 配色与字体
│   ├── drawing.py      # 圆角绘制原语
│   ├── images.py       # 图标、品牌图与预览图生成
│   ├── text.py         # 文本与省略工具
│   ├── widgets/        # 自绘基础控件（含结果网格与开关）
│   └── views/          # 顶栏、来源条、参数卡、迭代方式、操作区、预览区
├── parameters.py       # 侧栏与批量参数校验
├── tasks.py            # 后台任务与事件队列
└── version.py          # 版本号与版本来源解析
```

图标资源在 `assets/icons/`，品牌标识与软件图标在 `assets/brand/`，测试在 `tests/`。多次迭代的交互与实现约定见 `docs/batch-iteration.md`。

## 快速测试

1. 点击顶部来源条右侧的“使用内置测试图”，得到一张普通几何图案。
2. 选择算法和次数，点击“正向混淆”。
3. 点击右侧底部“用作输入”，保持相同参数，再点击“反向混淆”（即复原）。
4. 右侧预览恢复后，点击“保存 PNG”导出图片。

每次处理都从顶部来源图片开始。想连续处理上一轮结果时，先点击“用作输入”。

## 多次迭代

在左栏“迭代方式”中选择“多次”，输入“等差迭代次数” N（默认 10，上限 50）：

1. 输入框会从第 1 次开始，一次生成 **1…N** 的 N 张结果。
2. 未开启“正反自动混淆”时，点“反向混淆”或“正向混淆”生成该方向的整批结果；左侧保留输入预览，右侧显示结果网格。生成前右侧标题为“结果集”，生成后变为“反向结果集”或“正向结果集”。
3. 本批没有找到想要的结果时，点“迭代方式”卡里的“下一批”，继续生成 **N+1…2N**，并替换上一批。
4. 开启“正反自动混淆”后，底部按钮变为“自动混淆”和“自动下一批混淆”；右侧左框显示反向结果集，右框显示正向结果集，原图只保留在顶部来源条。
5. 点击任意缩略图可打开大图预览，在预览窗里选择“用作输入”或“保存 PNG”。

更改图片、算法、偏移量、a、b、N、迭代方式或自动混淆开关，都会清空当前批量结果并从第 1 批重新开始。结果网格只保留缩略图，打开预览或保存时会按该次迭代值重新生成原尺寸图，以控制大图批量结果的内存占用。

## 算法和参数

| 模式 | 支持的尺寸 | 反向混淆（复原）需要的参数 |
| --- | --- | --- |
| Gilbert（广义希尔伯特曲线） | 任意正整数宽高 | 相同次数和偏移量；偏移量留空采用默认值 |
| Arnold（标准猫映射） | 正方形 | 相同次数、a、b，默认 a=1、b=1 |

正向混淆和反向混淆是同一置换的正、反两个方向：正向混淆沿曲线向前移动像素，反向混淆向回移动，两者互为逆操作。对未混淆的图片点反向混淆，也会得到一张混淆图，这是正常现象。

Gilbert 使用广义希尔伯特曲线遍历像素，默认每次循环移动 `floor(((sqrt(5)-1)/2) × 宽 × 高 + 0.5)` 个像素。旧工具的取整方式可能不同，可手动填写偏移量。

Arnold 的前向坐标变换为：

```text
x' = (x + a*y) mod N
y' = (b*x + (a*b+1)*y) mod N
```

算法、次数或参数不匹配时，结果仍可能是混淆图；对未混淆的图片做反向混淆同样会得到混淆图。此工具不自动判断输入是否已混淆，也不猜测密码或未知参数。

预览会缩小显示，实际处理保留原始宽高和 RGBA 像素。保存为 PNG。支持常见的单帧 8 位图片；不处理动画、多页图片或高位深图片。经过缩放、裁剪或有损压缩的混淆图，可能无法精确复原。

## 依赖

当前环境已安装所需依赖。在其他 Python 环境使用时，先运行：

```powershell
python -m pip install -r requirements.txt
```

需要 Python 3.10 或更新版本，以及 Tkinter（Windows 官方 Python 安装程序通常包含）。

## 版本号

版本号采用 `大更新.中期更新.小更新` 的三段格式，例如 `1.0.0`：大更新调整整体架构或交互方式，中期更新新增功能并保持兼容，小更新修复问题和调整细节。

版本号默认写在 `pixelconfusion/version.py` 的 `VERSION_PARTS` 中，修改版本只需改这一行：

```python
VERSION_PARTS: tuple[int, int, int] = (1, 0, 0)  # (大更新, 中期更新, 小更新)
```

打包时也可以不修改代码，按以下优先级指定版本号：

1. `python build.py --version 1.0.0`：只对本次打包生效；
2. 环境变量 `PIXELCONFUSION_VERSION`；
3. 项目根目录的 `version.json`，内容为 `{"version": "1.0.0"}`；
4. `pixelconfusion/version.py` 中的 `VERSION_PARTS`。

打包脚本会把最终版本号写入可执行文件名、Windows 文件属性、窗口标题和程序内的 `--version` 输出，几处始终一致。运行中版本号显示在窗口标题、顶栏标识下方和使用说明里；在终端也可以用以下命令查看：

```powershell
python main.py --version
```

写回版本号并递增时使用：

```powershell
python build.py --bump patch        # 1.0.0 -> 1.0.1，小更新
python build.py --bump minor        # 1.0.0 -> 1.1.0，中期更新
python build.py --bump major        # 1.0.0 -> 2.0.0，大更新
python build.py --set-version 1.2.0 # 直接指定版本号
```

`--bump` 和 `--set-version` 会把新版本号写回当前的版本来源（存在 `version.json` 时写回它，否则写回 `pixelconfusion/version.py`），随后执行打包。

## 打包

打包为单个可执行程序需要 PyInstaller，先安装开发依赖：

```powershell
python -m pip install -r requirements-dev.txt
```

然后在项目根目录运行：

```powershell
python build.py
```

默认输出 `dist/PixelConfusion-1.0.0.exe`，可执行程序内含版本号，文件属性中的版本、产品名称和窗口标题与实际版本一致。常用参数：

| 参数 | 说明 |
| --- | --- |
| `--version X.Y.Z` | 仅本次打包使用指定版本号 |
| `--bump {major,minor,patch}` | 递增版本号、写回来源后打包 |
| `--set-version X.Y.Z` | 指定版本号、写回来源后打包 |
| `--print-version` | 只打印解析到的版本号 |
| `--onedir` | 输出文件夹而不是单文件 |
| `--console` | 保留控制台窗口，便于排查启动问题 |
| `--output DIR` | 指定输出目录，默认 `dist` |
| `--name NAME` | 可执行程序基名，默认 `PixelConfusion` |
| `--no-version-suffix` | 文件名不附加版本号 |
| `--clean` | 打包前清理缓存与临时目录 |
| `--dry-run` | 只打印版本号和 PyInstaller 命令，不执行打包 |

打包产物是 Windows 可执行文件，首次运行可能被 SmartScreen 提示；这不是程序错误，选择“更多信息 → 仍要运行”即可。

## 验证

```powershell
python -m unittest -v
```

测试仅使用程序生成的像素，覆盖坐标映射、长方形和细长图片、透明通道、文件保存、两种算法的逐字节往返一致性，以及侧栏、批量参数与版本号解析校验。

Gilbert 递归划分改编自 [Jakub Červený 的 gilbert2d](https://github.com/jakubcerveny/gilbert)。授权见 `THIRD_PARTY_NOTICES.txt`。

## 许可证

本项目原创代码采用 MIT License，见 `LICENSE`。改编自 gilbert2d 的部分仍为 BSD-2-Clause，见 `THIRD_PARTY_NOTICES.txt`；MIT 许可不改变该部分的原始许可。
