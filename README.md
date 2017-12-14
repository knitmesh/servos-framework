
# Servos Framework: *The process level Concurrent Toolkit* 
[![Python 2.7](https://img.shields.io/badge/python-2.7-yellow.svg)](https://www.python.org/) [![License](https://img.shields.io/badge/license-GPLv2-red.svg)](https://raw.githubusercontent.com/Xyntax/POC-T/master/doc/LICENSE.txt) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/1413552d34bc4a4aa84539db1780eb56)](https://www.codacy.com/app/xyntax/POC-T?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=Xyntax/POC-T&amp;utm_campaign=Badge_Grade) 

## 框架说明

### 服务的组织
采用分散开发统一管理。以服务为单位进行开发。每个服务可以单独启动，也可以多个服务同时启动，通过配置文件进行管理指定哪些服务生效，部署方式灵活。

特点
---
* 框架代码结构简单易用，易于修改。新手、老鸟皆可把控。

* 采用gevent实现并发操作，与scrapy的twisted相比，代码更容易理解。

* 完全模块化的设计，强大的可扩展性。

* 支持多线程/Gevent两种并发模式

* 支持分布式

### 扩展性
- plugin扩展。框架已经预设了一些调用点，方便对各个环节进行修改。可以针对这些调用点编写相应的处理，当框架启动时会自动进行采集，当程序运行到调用点位置时，自动调用对应的插件函数。
- middleware 中间件扩展。与`web framework`类似，这里是对服务接口调用进行扩展。
- injection 注入式扩展。可向框架注入 functions, global_objects 等。

## 新增服务流程
- 增加服务包。
- 从基类继承，并使用 `entry` 装饰器标记。
- 编码服务逻辑。
- 配置文件中增加要启动的服务。

用户手册
----

* [快速开始](https://github.com/knitmesh/servos-framework/blob/master/docs/helloworld.md)
* [日志处理说明](https://github.com/knitmesh/servos-framework/blob/master/docs/log.md)
* [命令行命令说明](https://github.com/knitmesh/servos-framework/blob/master/docs/manage.md)
* [配置文件说明](https://github.com/knitmesh/servos-framework/blob/master/docs/settings.md)

依赖
---
* Python 2.7
* pip


### 安装

- 安装服务框架。新构建的服务依赖 **servos-framework** 框架，先 ```pip install servos-framework```。
- 安装服务依赖。运行命令 ```servos install```，该命令会自动安装各服务在自己目录下 requirements.txt 定义的依赖包，具体参数可以运行 ```servos help``` 命令查看。
- 启动服务。运行 ```servos runserver --settings cache_settings.ini```。
- 调试服务。使用 **manage.py** 作为启动文件，在IDE的 Parameters 配置处输入将要使用的命令行, 如： ```runserver --settings cache_settings.ini```。

### 部署安装

- 执行`./setenv.sh`会自动创建virtualenv虚拟环境。
- 执行`source .virtualenvs/services/bin/activate`切换到虚拟环境。
- 启动服务。
    1. cache服务：运行 ```servos runserver --settings cache_settings.ini```。
    2. websocket服务：运行 ```servos runserver --settings wss_settings.ini```。

### Docker
构建base镜像
```bash
# 初始化外部依赖
python2 docker/prepare.py -v VERSION --pip-server 192.168.103.137:8000 --yum-repo http://192.168.103.137:8001
docker build . -f docker/base/Dockerfile -t service_base:VERSION
```

构建功能镜像（以cache为例）
```bash
cd docker/cache/
docker build . -t service-cache:VERSION
```

运行服务（以cache为例）
```bash
docker run --rm --network host \
    -v /etc/portal/cache_settings.ini:/etc/portal/cache_settings.ini \
    --name service-wss \
    t2cloud-service-wss:VERSION
```
