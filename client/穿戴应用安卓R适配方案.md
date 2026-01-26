# 穿戴应用安卓R适配方案

## 概述

本文档针对Android 8升级到Android 11做了一个主要行动项的梳理，列在文档中作为各应用的适配行动指导。

内容主要梳理自官方文档：

### Android 9

1、 [行为变更：所有应用](https://developer.android.com/about/versions/pie/android-9.0-changes-all)
2、[行为变更：以 API 级别 28 及更高级别为目标的应用](https://developer.android.com/about/versions/pie/android-9.0-changes-28)

### Android 10

1、[行为变更：所有应用](https://developer.android.com/about/versions/10/behavior-changes-all)
2、[重大隐私权变更](https://developer.android.com/about/versions/10/privacy)

### Android 11

1、[行为变更：所有应用](https://developer.android.com/about/versions/11/behavior-changes-all)
2、[重大隐私权变更
](https://developer.android.com/about/versions/11/privacy)

梳理出来的都是对于应用影响可能较大的变更项，建议所有应用进行一遍排查。并且每个应用处理的方式可能不一样，**所以这里没有统一的处理方法**。

另外可能每个应用会有自己的特有问题，建议模块负责人可以去看看官方文档，是否有未列出的点需要处理。

## 适配项

### 页面右滑退出适配

支持右滑退出的页面，需要将主题“android:windowSwipeToDismiss”设为true
styles.xml：

```plain
<style name="AppTheme" parent="Theme.AppCompat.NoActionBar">
    <item name="android:windowSwipeToDismiss">true</item>
</style>
```

AndroidManifest.xml：所有界面都支持右滑退出

```plain
<application
    android:icon="@drawable/ic_launcher"
    android:label="@string/app_name"
    android:theme="@style/AppTheme">
```

如果是特定Activtiy需要支持右滑退出，可针对单个activity配置

```plain
<activity
    android:name=".MainActivity"
    android:theme="@style/AppTheme">
```

### 设备标识符限制

参考路径：https://developer.android.com/about/versions/10/privacy/changes#non-resettable-device-ids

从 Android 10 开始，应用必须具有 READ_PRIVILEGED_PHONE_STATE 特许权限才能访问设备的不可重置标识符（包含 IMEI 和序列号）。
![image.png](https://openfs.oppomobile.com/open/res/202307/03/dd1b24b8104362677bd8afdf101ea00e.png)

**适配行动项：**排查是否使用到上述函数，是否可以去掉，如需确实需要，可查看谷歌提供的适配方案，也可使用移动安全联盟提供的统一SDK，由于一二代表未支持统一SDK，如果使用统一SDK需要兼容一二代表（一二代表可直接获取设备标识符，可先通过原生接口获取设备标识符，如果获取不到再通过统一SDK获取）

http://msa-alliance.cn/col.jsp?id=120

### 隐私权变更

参考路径：https://developer.android.com/about/versions/pie/android-9.0-changes-all#privacy-changes-all

隐私权变更，包括后台对传感器的访问受限、限制访问通话记录、限制访问电话号码、限制访问 Wi-Fi 位置和连接信息

**适配行动项：**排查应用中是否有这些行为，测试是否功能异常。

### 非SDK接口限制

参考路径：https://developer.android.com/guide/app-compatibility/restrictions-non-sdk-interfaces

对使用非 SDK 接口的限制，从 Android 9（API 级别 28）开始，Android 平台对应用能使用的非 SDK 接口实施了限制。只要应用引用非 SDK 接口或尝试使用反射或 JNI 来获取其句柄，这些限制就适用。

可能的限制方式如下。
![image.png](https://openfs.oppomobile.com/open/res/202307/03/649f280c99a5c5b3165d6e61c96183c0.png)

**适配行动项：**排查应用中调用的非SDK开放接口，测试是否功能异常。更详细的限制接口表可以在上面的链接中下载到。

### 后台启动应用

参考路径：https://developer.android.com/about/versions/pie/android-9.0-changes-all#fant-required

在 Android 9 中，您不能从非 Activity 环境中启动 Activity，除非您传递 Intent 标志 FLAG_ACTIVITY_NEW_TASK。 如果您尝试在不传递此标志的情况下启动 Activity，则该 Activity 不会启动，系统会在日志中输出一则消息。

**适配行动项：**检查非activity情况下的startActivity，是否添加了该标志位

### 前台服务

参考路径：https://developer.android.com/about/versions/pie/android-9.0-changes-28#fg-svc

如果应用以 Android 9 或更高版本为目标平台并使用前台服务，则必须请求 FOREGROUND_SERVICE 权限。这是[普通权限](https://developer.android.com/guide/topics/permissions/normal-permissions)，因此，系统会自动为请求权限的应用授予此权限。

**适配行动项：**应用排查前台服务是否有该权限

### Build.SERIAL

参考路径：https://developer.android.com/about/versions/pie/android-9.0-changes-28#build-serial-deprecation

在 Android 9 中，Build.SERIAL 始终设为 “UNKNOWN”，以保护用户隐私。

**适配行动项：**检查应用中是否使用Build.SERIAL

### 外部存储访问权限范围限定为应用文件和媒体

参考路径：https://developer.android.com/about/versions/10/privacy/changes#scoped-storage

默认情况下，对于以 Android 10 及更高版本为目标平台的应用，其[访问权限范围限定为外部存储](https://developer.android.com/training/data-storage/files/external-scoped)，即分区存储。

**适配行动项：**检查应用的存储行为，查看是否受影响需要适配

### 后台访问位置

参考路径：https://developer.android.com/about/versions/10/privacy/changes#app-access-device-location

为了让用户更好地控制应用对位置信息的访问权限， Android 10 引入了 ACCESS_BACKGROUND_LOCATION 权限

**适配行动项：**有后台访问位置信息的应用，需要申请该权限。判断标准见参考链接。

### selinux

android R打开selinux之后可能会导致一些功能异常。

**适配行动项：**适配行动项：应用全功能自检，如果发生一些意料外的崩溃或异常，可以看log里是否打印avc关键字的log，这种一般是selinux导致。
