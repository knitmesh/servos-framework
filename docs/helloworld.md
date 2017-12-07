# Hello, World

## 准备

安装python-servos


## 创建新的项目

在安装完毕后，会提供一个命令行工具 servos, 它可以执行一些命令。

进入你的工作目录，然后执行:


```
servos makeproject project-demo
```

执行成功后，在 project-demo 目录下会是这样的:


```
├── services
│   ├── __init__.py
│   ├── local_settings.ini
│   └── settings.ini
├── manage.py
└── setup.py
```


## 创建Hello服务

然后让我们创建一个Hello的服务:


```
cd project-demo
servos makeservice Hello
```

在执行成功后，你会在services/Hello下看到:


```
├── __init__.py
├── requirements.txt
├── service.py
└── settings.ini
```


## 编写服务代码

打开 Hello/service.py，你会看到:


```python
# -*- coding: utf-8 -*-
from servos import ServiceBase, entry, settings
logger = logging.getLogger(__name__)


@entry()
class DemoService(ServiceBase):
    _service_name = 'demoservice'

    def start(self):
        logger.info('starting %s service' % self._service_name)
        super(DemoService, self).start()
        self.tg.add_thread(self._do_loop, 'demo_thread')
        logger.info('%s service started' % self._service_name)

    def _do_loop(self, name, *args, **kwargs):
        while True:
            logger.info('%s print in thread loop', name)
            threading.time.sleep(10)
        logger.info('%s exit loop', name)

    def stop(self):
        logger.info('stoping %s service' % self._service_name)
        super(DemoService, self).stop()
        logger.info('%s service stoped' % self._service_name)

```

该demo服务会使用线程池中的线程循环打印信息。



## 启动

在命令行下执行:


```
servos runserver --settings settings.ini
```

这样就启动了所有服务。

也可以使用 `manage.py` 作为启动文件来进行调试，在IDE的 Parameters 配置处输入将要使用的命令行, 如： 

```
runserver --settings settings.ini
```
