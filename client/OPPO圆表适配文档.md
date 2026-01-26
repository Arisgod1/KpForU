# OPPO圆表适配文档

## 一、简介

### 1.1 背景说明

OPPO将推出圆形智能手表产品，仍为安卓系统。为了方便适配，本文提供适配指导，包括不同形状设备兼容、UI布局指南、开发指导等，用于引导开发者和设计师将自己的应用适配到圆形设备上，并保证良好的使用体验。

### 1.2 设备基本情况

屏幕比例：为1:1的圆形设备
安卓版本：Android R（安卓11)
网络条件：支持独立连接网络（包括Wi-Fi和移动网络），以及蓝牙网络
硬件条件：支持Mic，三轴加速度传感器/陀螺仪传感器/地磁传感器/气压传感器/光学心率传感器/环境光传感器等，可直接通过安卓原生接口进行调用

### 1.3 与方表的核心差异

1.屏幕尺寸
2.交互规范

## 二、设备兼容

**1.要求应用使用同一APK对不同尺寸的设备进行兼容**
2.通过values资源进行区分

| 设备                           | values资源区分条件 | values资源获取优先级   | drawable资源区分条件   | drawable资源获取优先级                 | layout资源区分条件 | layout资源获取优先级   |
| :----------------------------- | :----------------- | :--------------------- | :--------------------- | :------------------------------------- | :----------------- | :--------------------- |
|                                | values（默认）     |                        | drawable-xhdpi（默认） |                                        | layout（默认）     |                        |
| 方表（以oppo watch 3 pro为例） | values-h248dp      | values-h248dp > values | drawable-h248dp-xhdpi  | drawable-h248dp-xhdpi > drawable-xhdpi | layout-h248dp      | layout-h248dp > layout |
| 圆表                           | values-round       | values-round > values  | drawable-round-xhdpi   | drawable-round-xhdpi > drawable-xhdpi  | layout-round       | layout-round > layout  |

3.APK代码逻辑区分方圆

```plain
boolean isRound = context.getResources().getConfiguration().isScreenRound ();
if (isRound) {
    //TODO 圆表逻辑
} else {
    //TODO 方表表逻辑
}
```

## 三、设计规范

### 3.1 原则

#### 1.在设计时要考虑到扩展性

将外边距定义为百分比，而不是绝对值，以便外边距可以在圆形屏幕上按比例缩放。场景及页面示例如下：
![image.png](https://openfs.oppomobile.com/open/res/202307/03/a0c219e2a4635846ff5d38f5d8a15f1e.png)

#### 2.字体大小

文本框和字高随字体大小变化，间距不变，并且会根据布局将屏幕上的其他元素上推或下推，示例如下：
![image.png](https://openfs.oppomobile.com/open/res/202307/03/914c34f75041b6fa83b04e482d720b5a.png)

### 3.2 设计规范及控件

为了提高设计和开发效率，OPPO提供设计规范及控件、控件包（.arr），可联系运营获取

### 3.3 与方表的设计差异

1.时间和一级标题居中显示
2.设计以居中为主，列表、列表说明文本、长文本除外
3.Button按钮，涉及确认操作的提示内容时，建议优先使用圆形按钮替代“确认”、“取消”等胶囊按钮；复杂的操作内容仍建议使用胶囊按钮，使用文本说明操作

### 3.4 核心场景展示

![image.png](https://openfs.oppomobile.com/open/res/202307/03/76050aaeb557a6f9d90253e751ff63ca.png)

## 四、开发指导

#### 4.1 启动右滑功能

手表由于屏幕过小，无法很好地支持功能键返回或手势返回，因此实现右滑返回能提高手表应用的交互体验，也是应用必须遵循的规则之一。可以在主题中配置如下：

```plain
<item name="android:windowSwipeToDismiss">true</item> 
```

#### 4.2 配置版本兼容

手表应用需要在manifest配置如下：

```plain
<uses-feature android:name="android.hardware.type.watch"/> 
```

#### 4.3 Android R适配

由于手表系统是Android R，涉及权限调整，应用可参考适配文档进行排查。

更多手表开发信息，可参考[OPPO Watch 应用合作介绍](https://open.oppomobile.com/documentation/page/info?id=11282)

更多应用开发信息，可参考安卓公开开发文档