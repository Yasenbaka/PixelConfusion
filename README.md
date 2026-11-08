# PixelConfusion

本地图片混淆与复原桌面工具，所有处理都在本机完成。

在此文件夹打开终端，运行：

```powershell
python main.py
```

程序会打开本地窗口。选图和处理均在电脑上完成。入口为 `main.py`，业务代码按职责拆在 `pixelconfusion/`：

```text
pixelconfusion/
├── app.py              # 窗口、状态与交互控制
├── core/               # Gilbert / Arnold 算法、变换器、图片读写
├── ui/
│   ├── theme.py        # 配色与字体
│   ├── drawing.py      # 圆角绘制原语
│   ├── images.py       # 图标、品牌图与预览图生成
│   ├── text.py         # 文本与省略工具
│   ├── widgets/        # 自绘基础控件
│   └── views/          # 顶栏、来源卡、参数卡、操作区、预览区
├── parameters.py       # 侧栏参数校验
└── tasks.py            # 后台任务与事件队列
```

图标资源在 `assets/icons/`，测试在 `tests/`。

## 快速测试

1. 点击左栏“使用内置测试图”，得到一张普通几何图案。
2. 选择算法和次数，点击“混淆图片”。
3. 点击右侧底部“用作输入”，保持相同参数，再点击“复原图片”。
4. 右侧预览恢复后，点击“保存 PNG”导出图片。

每次处理都从左侧输入图片开始。想连续处理上一轮结果时，先点击“用作输入”。

## 算法和参数

| 模式 | 支持的尺寸 | 复原需要的参数 |
| --- | --- | --- |
| Gilbert（广义希尔伯特曲线） | 任意正整数宽高 | 相同次数和偏移量；偏移量留空采用默认值 |
| Arnold（标准猫映射） | 正方形 | 相同次数、a、b，默认 a=1、b=1 |

Gilbert 使用广义希尔伯特曲线遍历像素，默认每次循环移动 `floor(((sqrt(5)-1)/2) × 宽 × 高 + 0.5)` 个像素。旧工具的取整方式可能不同，可手动填写偏移量。

Arnold 的前向坐标变换为：

```text
x' = (x + a*y) mod N
y' = (b*x + (a*b+1)*y) mod N
```

算法、次数或参数不匹配时，结果仍可能是混淆图；此工具不自动猜测密码或未知参数。

预览会缩小显示，实际处理保留原始宽高和 RGBA 像素。保存为 PNG。支持常见的单帧 8 位图片；不处理动画、多页图片或高位深图片。经过缩放、裁剪或有损压缩的混淆图，可能无法精确复原。

## 依赖

当前环境已安装所需依赖。在其他 Python 环境使用时，先运行：

```powershell
python -m pip install -r requirements.txt
```

需要 Python 3.10 或更新版本，以及 Tkinter（Windows 官方 Python 安装程序通常包含）。

## 验证

```powershell
python -m unittest -v
```

测试仅使用程序生成的像素，覆盖坐标映射、长方形和细长图片、透明通道、文件保存、两种算法的逐字节往返一致性，以及侧栏参数校验。

Gilbert 递归划分改编自 [Jakub Červený 的 gilbert2d](https://github.com/jakubcerveny/gilbert)。授权见 `THIRD_PARTY_NOTICES.txt`。

## 许可证

本项目原创代码采用 MIT License，见 `LICENSE`。改编自 gilbert2d 的部分仍为 BSD-2-Clause，见 `THIRD_PARTY_NOTICES.txt`；MIT 许可不改变该部分的原始许可。
