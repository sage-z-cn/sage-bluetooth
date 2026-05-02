# Sage Bluetooth - 开发计划

## 总体概述

基于设计文档，将开发工作划分为 **7 个阶段**，按照依赖关系自底向上推进：先搭建基础设施和数据模型，再实现蓝牙核心逻辑，然后构建 UI 层，最后进行集成联调和打包部署。每个阶段末尾列出验证标准，确保阶段性成果可测试。

---

## 阶段 0：项目初始化与环境搭建

### 目标
搭建项目骨架、安装依赖、确认运行环境。

### 任务清单

| # | 任务 | 产出 | 优先级 |
|---|------|------|--------|
| 0.1 | 按设计文档的目录结构创建项目骨架（所有目录和 `__init__.py`） | 完整目录结构 | P0 |
| 0.2 | 创建 `requirements.txt`（PyQt5>=5.15, bleak>=3.0.1, qasync>=0.27） | 依赖文件 | P0 |
| 0.3 | 创建 `requirements-dev.txt`（pytest, pytest-qt, pytest-asyncio, pyinstaller） | 开发依赖 | P0 |
| 0.4 | 初始化 git 仓库，添加 `.gitignore` | 版本控制 | P0 |
| 0.5 | 创建 `src/config.py`，定义全局常量（窗口尺寸、扫描超时、路径等） | 全局配置 | P0 |
| 0.6 | 创建 `src/utils/logger.py`，按 [06-deployment.md](06-deployment.md) 第 5 节配置日志 | 日志模块 | P1 |
| 0.7 | 验证 Windows 环境：Python 3.10+、bleak 导入正常、蓝牙适配器可用 | 环境确认 | P0 |

### 验证标准
- `pip install -r requirements.txt` 成功
- `python -c "from bleak import BleakScanner"` 无报错
- `python src/main.py` 能启动一个空窗口并正常退出

---

## 阶段 1：数据模型层 (`models/`)

### 目标
实现所有数据模型和枚举定义，作为后续核心逻辑的基础。

### 任务清单

| # | 任务 | 对应设计文档章节 | 优先级 |
|---|------|-----------------|--------|
| 1.1 | 实现枚举：`ConnectionState`、`ScanState`、`DeviceType` | [04-data-models.md 第 9 节](04-data-models.md) | P0 |
| 1.2 | 实现 `BLEDeviceModel`（dataclass，frozen，`from_bleak` 工厂方法） | [04-data-models.md 第 2 节](04-data-models.md) | P0 |
| 1.3 | 实现 `DeviceInfoModel`（GATT 读取结果模型） | [04-data-models.md 第 3 节](04-data-models.md) | P0 |
| 1.4 | 实现 `GattServiceModel`、`GattCharacteristicModel` | [04-data-models.md 第 4-5 节](04-data-models.md) | P0 |
| 1.5 | 实现 `AppState`（运行时全局状态，含设备字典） | [04-data-models.md 第 6 节](04-data-models.md) | P0 |
| 1.6 | 实现 `AppConfig`（可持久化配置，JSON 读写） | [04-data-models.md 第 7 节](04-data-models.md) | P1 |
| 1.7 | 实现 `utils/uuid_constants.py`（GATT 服务/特征 UUID 常量） | [03-bluetooth-core.md 第 7.2 节](03-bluetooth-core.md) | P0 |

### 验证标准
- 所有模型可正常实例化、序列化/反序列化
- `BLEDeviceModel.from_bleak()` 可正确转换（可用 mock 数据测试）
- `AppConfig.save()` / `AppConfig.load()` 配置持久化正常

---

## 阶段 2：设备类型识别模块 (`utils/`)

### 目标
实现设备类型识别引擎，支持 Appearance 映射、Service UUID 辅助、名称关键词兜底。

### 任务清单

| # | 任务 | 对应设计文档章节 | 优先级 |
|---|------|-----------------|--------|
| 2.1 | 实现 `APPEARANCE_MAP` 完整映射表（约 100+ 条目） | [05-device-type-recognition.md 第 2.1 节](05-device-type-recognition.md) | P0 |
| 2.2 | 实现 `resolve_device_type(appearance)` 函数（精确匹配 + 范围匹配） | [05-device-type-recognition.md 第 2.2 节](05-device-type-recognition.md) | P0 |
| 2.3 | 实现 `SERVICE_TYPE_MAP` 映射表 | [05-device-type-recognition.md 第 3.1 节](05-device-type-recognition.md) | P0 |
| 2.4 | 实现 `NAME_KEYWORDS` 映射表及 `resolve_by_name()` | [05-device-type-recognition.md 第 6 节](05-device-type-recognition.md) | P1 |
| 2.5 | 实现综合识别函数 `resolve_device_type_comprehensive()` | [05-device-type-recognition.md 第 3.2 节](05-device-type-recognition.md) | P0 |
| 2.6 | 准备设备类型图标资源（40x40 PNG，至少覆盖 16 种类型） | [05-device-type-recognition.md 第 4-5 节](05-device-type-recognition.md) | P1 |

### 验证标准
- 单元测试覆盖主要 Appearance 值（0x0080 → HEADPHONE, 0x0015 → KEYBOARD 等）
- Service UUID 辅助识别逻辑正确
- 未知设备返回 `DeviceType.UNKNOWN`
- 图标资源文件存在且命名正确

---

## 阶段 3：蓝牙核心层 (`core/`)

### 目标
实现所有 BLE 交互逻辑，封装为 `BluetoothManager` 门面类，向上层提供 Qt 信号接口。

### 任务清单

| # | 任务 | 对应设计文档章节 | 优先级 |
|---|------|-----------------|--------|
| **3A: asyncio 与 Qt 整合** | | |
| 3.1 | 在 `main.py` 中集成 `qasync` 事件循环（Qt + asyncio 双循环） | [03-bluetooth-core.md 第 9 节](03-bluetooth-core.md) | P0 |
| 3.2 | 实现异步任务管理器（`_run_async` 方法，防止任务被 GC） | [03-bluetooth-core.md 第 9.2 节](03-bluetooth-core.md) | P0 |
| **3B: 蓝牙适配器控制** | | |
| 3.3 | 实现 `AdapterController`（PowerShell PnP 命令方案） | [03-bluetooth-core.md 第 4 节](03-bluetooth-core.md) | P0 |
| 3.4 | 实现管理员权限检测（`ctypes.windll.shell32.IsUserAnAdmin()`） | [03-bluetooth-core.md 第 4.4 节](03-bluetooth-core.md) | P0 |
| 3.5 | 实现蓝牙开关操作（`turn_on` / `turn_off` + 错误提示） | [03-bluetooth-core.md 第 4.2 节](03-bluetooth-core.md) | P0 |
| **3C: 设备扫描器** | | |
| 3.6 | 实现 `DeviceScanner`（`BleakScanner` + 回调） | [03-bluetooth-core.md 第 5 节](03-bluetooth-core.md) | P0 |
| 3.7 | 实现设备去重策略（地址去重 + 信息合并） | [03-bluetooth-core.md 第 5.4 节](03-bluetooth-core.md) | P0 |
| 3.8 | 实现扫描超时控制和 `stop_scan` | [03-bluetooth-core.md 第 5.2 节](03-bluetooth-core.md) | P0 |
| **3D: 设备连接器** | | |
| 3.9 | 实现 `DeviceConnector`（连接 / 断开 / 配对） | [03-bluetooth-core.md 第 6 节](03-bluetooth-core.md) | P0 |
| 3.10 | 实现单连接模式（连接新设备时自动断开旧设备） | [03-bluetooth-core.md 第 6.3 节](03-bluetooth-core.md) | P0 |
| 3.11 | 实现连接超时处理和重连机制（最多 3 次重试） | [03-bluetooth-core.md 第 8 节](03-bluetooth-core.md) | P1 |
| **3E: GATT 读取器** | | |
| 3.12 | 实现 `GattReader`（读取 GAP/DIS/BAS 服务特征） | [03-bluetooth-core.md 第 7 节](03-bluetooth-core.md) | P0 |
| 3.13 | 实现电量监控（Notify 优先，降级为 60 秒轮询） | [03-bluetooth-core.md 第 7.4 节](03-bluetooth-core.md) | P1 |
| **3F: 门面类** | | |
| 3.14 | 实现 `BluetoothManager` 单例（协调所有子模块，统一信号定义） | [03-bluetooth-core.md 第 3 节](03-bluetooth-core.md) | P0 |
| 3.15 | 实现错误处理策略（异常分类 → 友好 UI 提示） | [03-bluetooth-core.md 第 8 节](03-bluetooth-core.md) | P0 |

### 实现顺序建议

```
3.1 (qasync集成) → 3.2 (任务管理) → 3.3-3.5 (适配器控制)
    → 3.6-3.8 (扫描器) → 3.9-3.11 (连接器) → 3.12-3.13 (GATT)
    → 3.14-3.15 (门面类 + 错误处理)
```

### 验证标准
- 蓝牙适配器开关操作成功（需管理员权限环境）
- 扫描 10 秒能发现附近 BLE 设备，列表实时更新
- 能连接目标设备，读取到设备名称、厂商、电量等信息
- 断开连接后状态正确回退
- 非管理员运行时给出友好提示

---

## 阶段 4：UI 表示层 (`ui/`)

### 目标
构建完整的用户界面，包括系统托盘、主窗口、设备列表、详情面板等。

### 任务清单

| # | 任务 | 对应设计文档章节 | 优先级 |
|---|------|-----------------|--------|
| **4A: 样式与资源** | | |
| 4.1 | 编写 `styles.py`（QSS 样式，深色标题栏、浅色内容区） | [02-ui-design.md 第 4 节](02-ui-design.md) | P0 |
| 4.2 | 准备托盘图标资源（`bluetooth_on.ico`、`bluetooth_off.ico`、`app.ico`） | [02-ui-design.md 第 2.1 节](02-ui-design.md) | P0 |
| 4.3 | 创建资源路径工具函数 `get_resource_path()` | [06-deployment.md 第 2.3 节](06-deployment.md) | P0 |
| **4B: 系统托盘** | | |
| 4.4 | 实现 `TrayIcon`（`QSystemTrayIcon` 封装） | [02-ui-design.md 第 2 节](02-ui-design.md) | P0 |
| 4.5 | 实现托盘图标状态切换（蓝牙开/关/扫描中） | [02-ui-design.md 第 2.1 节](02-ui-design.md) | P0 |
| 4.6 | 实现右键上下文菜单（显示窗口、蓝牙开关、刷新、退出） | [02-ui-design.md 第 2.3 节](02-ui-design.md) | P0 |
| 4.7 | 实现左键单击切换窗口显示/隐藏 | [02-ui-design.md 第 2.2 节](02-ui-design.md) | P0 |
| **4C: 自定义标题栏** | | |
| 4.8 | 实现 `TitleBar`（无边框窗口的自定义标题栏） | [02-ui-design.md 第 4.1 节](02-ui-design.md) | P0 |
| 4.9 | 实现蓝牙状态指示灯（绿/红/黄三色） | [02-ui-design.md 第 4.1 节](02-ui-design.md) | P0 |
| 4.10 | 实现窗口拖拽移动 | [02-ui-design.md 第 4.1 节](02-ui-design.md) | P0 |
| **4D: 控制面板** | | |
| 4.11 | 实现 `ControlPanel`（蓝牙 Toggle Switch + 刷新按钮） | [02-ui-design.md 第 4.2 节](02-ui-design.md) | P0 |
| 4.12 | 实现 Toggle Switch 样式动画（滑动开关） | [02-ui-design.md 第 4.2 节](02-ui-design.md) | P0 |
| 4.13 | 实现刷新按钮的加载动画（旋转 spinner） | [02-ui-design.md 第 4.2 节](02-ui-design.md) | P0 |
| **4E: 设备列表** | | |
| 4.14 | 实现 `DeviceListWidget`（基于 `QListWidget` + 自定义项） | [02-ui-design.md 第 4.3 节](02-ui-design.md) | P0 |
| 4.15 | 实现设备列表项（图标 + 名称 + 地址 + 电量 + 操作按钮） | [02-ui-design.md 第 4.3 节](02-ui-design.md) | P0 |
| 4.16 | 实现操作按钮动态切换（配对/连接/断开/删除，按状态显示） | [02-ui-design.md 第 5.4 节](02-ui-design.md) | P0 |
| 4.17 | 实现删除确认对话框（弹窗确认） | [02-ui-design.md 第 5.5 节](02-ui-design.md) | P1 |
| 4.18 | 实现空状态和扫描中状态 UI | [02-ui-design.md 第 4.3 节](02-ui-design.md) | P0 |
| **4F: 设备详情面板** | | |
| 4.19 | 实现 `DeviceDetailWidget`（可折叠详情面板） | [02-ui-design.md 第 4.4 节](02-ui-design.md) | P0 |
| 4.20 | 实现滑入/滑出动画（高度过渡） | [02-ui-design.md 第 4.4 节](02-ui-design.md) | P1 |
| 4.21 | 实现详情字段展示（名称、地址、类型、厂商、电量、信号强度条等） | [02-ui-design.md 第 4.4 节](02-ui-design.md) | P0 |
| 4.22 | 实现信号强度条（10 格，RSSI 映射） | [02-ui-design.md 第 4.4 节](02-ui-design.md) | P1 |
| **4G: 主窗口** | | |
| 4.23 | 实现 `MainWindow`（400x600 固定尺寸，无边框） | [02-ui-design.md 第 3 节](02-ui-design.md) | P0 |
| 4.24 | 实现窗口位置计算（屏幕右下角，任务栏上方） | [02-ui-design.md 第 5.1 节](02-ui-design.md) | P0 |
| 4.25 | 实现失去焦点自动隐藏（`WindowDeactivate` 事件过滤） | [02-ui-design.md 第 5.2 节](02-ui-design.md) | P0 |
| 4.26 | 组装各子组件，完成布局（标题栏 + 控制面板 + 列表 + 详情） | [02-ui-design.md 第 3.2 节](02-ui-design.md) | P0 |

### 实现顺序建议

```
4.1-4.3 (样式资源) → 4.8-4.10 (标题栏) → 4.11-4.13 (控制面板)
    → 4.14-4.18 (设备列表) → 4.19-4.22 (详情面板)
    → 4.23-4.26 (主窗口组装) → 4.4-4.7 (系统托盘)
```

### 验证标准
- 窗口尺寸 400x600，固定不可调整
- 托盘图标显示正确，左键弹出/隐藏窗口
- 蓝牙开关 Toggle 可操作，状态灯颜色正确
- 设备列表项展示完整，操作按钮按状态正确切换
- 选中设备后详情面板滑入展示
- 失去焦点后窗口自动隐藏

---

## 阶段 5：业务层集成与信号连接 (`app.py`)

### 目标
将 UI 层与蓝牙核心层通过 Qt 信号/槽连接，实现完整的业务流程。

### 任务清单

| # | 任务 | 对应设计文档章节 | 优先级 |
|---|------|-----------------|--------|
| 5.1 | 实现 `App` 主控制器（`app.py`），初始化所有模块并注册信号 | [01-overview.md 第 2 节](01-overview.md) | P0 |
| 5.2 | 连接蓝牙开关信号：Toggle → `BluetoothManager.turn_on/off` → 托盘/标题栏状态更新 | [01-overview.md 第 5 节](01-overview.md) | P0 |
| 5.3 | 连接扫描流程：刷新按钮 → `start_scan` → 设备列表实时更新 | [01-overview.md 第 5.2 节](01-overview.md) | P0 |
| 5.4 | 连接设备操作：配对/连接/断开/删除按钮 → `BluetoothManager` 对应方法 | [02-ui-design.md 第 5.4 节](02-ui-design.md) | P0 |
| 5.5 | 连接设备信息读取：连接成功 → `read_device_info` → 更新详情面板 | [01-overview.md 第 5.3 节](01-overview.md) | P0 |
| 5.6 | 实现电量实时更新（信号驱动 UI 刷新） | [03-bluetooth-core.md 第 7.4 节](03-bluetooth-core.md) | P1 |
| 5.7 | 实现错误统一处理：`error_occurred` 信号 → UI 提示/Toast | [03-bluetooth-core.md 第 8 节](03-bluetooth-core.md) | P0 |
| 5.8 | 实现扫描时详情面板自动收起 | [02-ui-design.md 第 5.3 节](02-ui-design.md) | P1 |
| 5.9 | 实现蓝牙关闭时详情面板自动收起 | [02-ui-design.md 第 4.4 节](02-ui-design.md) | P1 |

### 验证标准
- 端到端流程通畅：开启蓝牙 → 扫描 → 选择设备 → 连接 → 查看详情 → 断开
- 所有状态切换有即时 UI 反馈
- 错误场景（蓝牙关闭、连接超时等）有友好提示

---

## 阶段 6：后台服务 (`services/`)

### 目标
实现后台监控服务，提升用户体验。

### 任务清单

| # | 任务 | 对应设计文档章节 | 优先级 |
|---|------|-----------------|--------|
| 6.1 | 实现 `ConnectionMonitor`（连接状态异常检测与自动重连） | [03-bluetooth-core.md 第 8.2 节](03-bluetooth-core.md) | P1 |
| 6.2 | 实现 `BatteryMonitor`（电量轮询，Notify 降级为 60 秒定时读取） | [03-bluetooth-core.md 第 7.4 节](03-bluetooth-core.md) | P1 |
| 6.3 | 实现扫描结果限制（最近 50 个设备，防止内存无限增长） | [03-bluetooth-core.md 第 10 节](03-bluetooth-core.md) | P2 |

### 验证标准
- 连接意外断开时 UI 状态正确回退
- 电量变化在 UI 上实时反映（Notify 或轮询）

---

## 阶段 7：打包、部署与测试

### 目标
完成应用打包、安装程序制作，以及全面测试。

### 任务清单

| # | 任务 | 对应设计文档章节 | 优先级 |
|---|------|-----------------|--------|
| 7.1 | 编写 `build.py`（PyInstaller 配置，单文件模式） | [06-deployment.md 第 2 节](06-deployment.md) | P0 |
| 7.2 | 处理资源文件路径兼容（`sys._MEIPASS`） | [06-deployment.md 第 2.3 节](06-deployment.md) | P0 |
| 7.3 | 打包测试：确认 exe 可独立运行 | [06-deployment.md 第 2 节](06-deployment.md) | P0 |
| 7.4 | 编写 Inno Setup 安装脚本 | [06-deployment.md 第 3 节](06-deployment.md) | P1 |
| 7.5 | 实现安装程序（创建快捷方式、开机自启选项） | [06-deployment.md 第 3.2 节](06-deployment.md) | P1 |
| 7.6 | 编写单元测试（设备类型识别、数据模型） | [06-deployment.md 第 8 节](06-deployment.md) | P1 |
| 7.7 | 集成测试（蓝牙扫描、连接的真实环境测试） | [06-deployment.md 第 8.2 节](06-deployment.md) | P0 |
| 7.8 | UI 测试（窗口尺寸、组件渲染） | [06-deployment.md 第 8.3 节](06-deployment.md) | P1 |
| 7.9 | 按发布检查清单逐项验收 | [06-deployment.md 第 9 节](06-deployment.md) | P0 |

### 验证标准
- PyInstaller 打包成功，exe 在干净 Windows 环境可运行
- 安装程序正常工作（安装、卸载、快捷方式）
- 发布检查清单全部通过

---

## 开发优先级总览

```
阶段 0 (项目初始化)        ██████████  P0
阶段 1 (数据模型)          ██████████  P0
阶段 2 (设备类型识别)      ██████████  P0 (P1 为名称关键词兜底)
阶段 3 (蓝牙核心)          ██████████  P0
阶段 4 (UI 表示层)         ██████████  P0 (P1 为动画/删除确认)
阶段 5 (业务层集成)        ██████████  P0
阶段 6 (后台服务)          ██████░░░░  P1
阶段 7 (打包部署测试)      ██████████  P0
```

---

## 关键技术风险与应对

| 风险 | 阶段 | 影响 | 应对方案 |
|-----|------|------|---------|
| qasync 与 PyQt5 事件循环兼容 | 阶段 0/3 | 阻塞开发 | 尽早验证，备选方案为线程桥接 |
| Bleak WinRT 后端不稳定 | 阶段 3 | 连接失败率高 | 实现重连机制，详细日志记录 |
| PowerShell PnP 命令需管理员权限 | 阶段 3 | 非管理员环境无法开关蓝牙 | 运行时检测权限，提供引导提示 |
| 蓝牙设备种类繁多，识别不完全准确 | 阶段 2 | UI 显示错误类型图标 | 多级兜底策略（Appearance → Service UUID → 名称关键词） |
| PyInstaller 打包体积过大 | 阶段 7 | 分发体验差 | 排除不必要模块，考虑 UPX 压缩 |

---

## 建议开发周期

| 阶段 | 建议天数 | 前置依赖 |
|------|---------|---------|
| 阶段 0 | 0.5 天 | 无 |
| 阶段 1 | 1 天 | 阶段 0 |
| 阶段 2 | 1 天 | 阶段 1 |
| 阶段 3 | 3 天 | 阶段 0（qasync 验证后可与阶段 1 并行） |
| 阶段 4 | 3 天 | 阶段 0（UI 可与核心层并行开发，使用 mock 数据） |
| 阶段 5 | 2 天 | 阶段 3 + 阶段 4 |
| 阶段 6 | 1 天 | 阶段 5 |
| 阶段 7 | 1 天 | 阶段 5 |

> **总计约 10-12 个工作日**，阶段 1/2 与阶段 3/4 可部分并行开发。
