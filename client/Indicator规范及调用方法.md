# **Indicator规范及调用方法**

Indicator，即指示器，是表盘上的功能组件，以一个小图标的形式展示在表盘上方，如下图所示。此功能组件用于：
1）告知用户应用正在后台运行，避免应用在后台长时间停留而用户无感知造成耗电加快的问题（如用户点开地图应用但并未进行导航，App音频播放暂停等）；
2）让用户可以快速跳转回应用界面。

![image.png](https://openfs.oppomobile.com/data/test/openplat/res/202204/18/9bdf0bdc9145c798c4d94947a4d7b2f1.png)

## **什么时候需要indicator**

当应用最小化后仍持续在后台运行，并且不会自动退出后的应用服务（例如定位服务、媒体播放等），可以接入indicator。目前支持的后台服务包括：运动中、导航中及媒体播放等。

## **如何接入indicator**

### **接入方法**

若您的应用想要接入indicator，请通过如下方式接入:
使用原生Notification API发送一个onGoing的通知，表示运行中的任务。并且该通知要符合一些自定义条件，手表才会将其显示为indicator。 该通知管理方式与普通onGoing通知并无二致，需要时发送，不需要时remove。唯一不同之处在于系统会将其显示为indicator，而不是显示在通知栏中。

### **接入条件**

1）onGoing属性为true；
2）category为我们定义好的字符串；
3）携带的extra中“show_heytap_indicator”为true
代码示例如下：

```java
Bundle bundle = new Bundle();
bundle.putBoolean("show_heytap_indicator", true);
Notification.Builder builder = new Notification.Builder 
        (context.getApplicationContext(), "channel");
builder.setOngoing(true)
        .addExtras(bundle)
        .setCategory(category)    
```

### **Category定义**

Category用于区分显示哪种indicator，定义如下：
1）导航-“navigation”, 或官方API中的Notification.CATEGORY_NAVIGATION (added in API level 28)
2）运动-“workout”，或官方API中的Notification.CATEGORY_WORKOUT (added in Android S)
3）媒体播放，通过原生API MediaSessionManager.OnActiveSessionsChangedListener 来监听ActiveSession，具体可参考[官方资料](https://developer.android.com/reference/android/media/session/MediaSession)。