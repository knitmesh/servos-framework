# 日志处理说明

## 日志配置

目前框架在default_settings.ini中已经有如下配置:


```
[LOG]
#level, filename, filemode, datefmt, format can be used in logging.basicConfig
level = 'info'
format = "[%(levelname)s %(name)s %(asctime)-15s %(filename)s,%(lineno)d] %(message)s"

[LOG.Loggers]
ROOT={'handlers':['Full']}

[LOG.Handlers]
Full = {'format':'format_full','class':'logging.handlers.RotatingFileHandler','args':('default.log','w',10000000,15)}
Simple = {'format':'format_simple'}
Package = {'format':'format_package'}

#defines all log fomatters
[LOG.Formatters] 
format_full = "[%(levelname)s %(name)s %(asctime)-15s %(filename)s,%(lineno)d] %(message)s"
format_simple = "[%(levelname)s] %(message)s"
format_package = "[%(levelname)s %(name)s] %(message)s"
```

日志可以分为：全局配置、root logger配置、其它logger配置。同时为了配置上可以复用，
handler和formatter可以单独配置，这样在logger中配置时只要引用相当的名字就可以了。

### basicConfig

[LOG]中定义的是全局配置，它对应于使用logging.basicConfig()的方式。因此你可以在[LOG]中定义如下参数:


level --
    日志级别，如：'info', 'debug', 'error', 'warn', 'notset'('noset'表示未设置)。缺省是NOTSET。

filename --
    文件名。当你需要将日志记录到文件中时使用。缺省是使用标准输出。

filemode --
    写入文件时的模式。需要先设置filename。缺省为'a'(追加方式)，可以设置为'w'(表
    示写入方式，会覆盖原日志文件)。

datefmt --
    日期格式，按datetime格式串的要求进行配置，缺省为'yyyy-mm-dd hh:mm:ss,ms'。

format --
    日志输出格式串。详见 [Python的日志记录属性](http://docs.python.org/library/logging.html#logrecord-attributes) 。



从logging中定义的日志级别可以看到有：CRITICAL(同FATAL), ERROR, WARNING(同WARN),
INFO, DEBUG, NOTSET。级别的大小是从高向低排的，最高的数值越大。当你设置了某个日志级别，
只有大于等于这个级别的才可以输出。一般来说，在创建logger或handler时，如果没有指定日志级别，
缺省都是NOTSET，所以所有的日志都会输出。


### logger定义

针对不同的logger，可以定义不同的日志配置。所有logger都定义在 `[LOG.Loggers]` 中。
它可以定义logger的level, 还可以定义多个handler，在缺省情况下，当不定义handler时，
会使用logging.StreamHandler类来处理。每个logger的配置形如:

```
[LOG.Loggers]
key = value
```

其中key就是logger的名字，如'servos.console', 'servos.core'等。
如果logger的名字为 'ROOT'，则表示root logger。而root logger就是执行basicConfig()后的日志对象。

value是一个字典，可以使用的参数说明为:

- propagate --
    传播标志。缺省为1，如果不传播，则要设置为0。主要是因为logging中的日志是可以分级的，
    在存在分级的情况下，当前logger处理完一条日志后，如果传播标志为1，则一旦存在父日志对象，
    则会自动调用父日志handler来输出日志。因此，你要根据你的实际配置来决定要如何设置传播。
    否则有可能出现一条日志会被输出多次的情况。

- level --
    logger的日志级别。

- handlers --
    处理句柄，它是一个list。它与另一个参数'format'不能同时使用。而这里处理句柄只是一个名字的引用，
    如:['handler1', 'handler2']。真正的处理句柄将在[LOG.Handlers]中定义。

- format --
    日志输出格式串。不能与handlers连用。如果同时定义了handlers，则此项不生效。
    当定义了format时，由handlers中会自动创建一个缺省的StreamHandler的句柄，
    其格式串为format的值。这里格式串有两种处理方式，一种是它定义为后面[LOG.Formatters]
    的一个名字的引用。另一种就是当在[LOG.Formatters]找不到时，则认为是一个普通的格式串进行处理。


> 因为一个logger可以支持多个handler，而format只定义了某个handler的格式串。
在通常情况下，在定义handler时，同时可以定义它的日志级别和format信息。
所以format的参数在这里，只是用来处理最简单的情况。


### handler的定义

所有的handler都定义在 [LOG.Handlers] 中，形式为:

```
[LOG.Handlers]
key = value
```

其中key为handler的名字。

value为handler要使用的参数，可以为:

- class --
    handler所对应的类对象。缺省为 `logging.StreamHandler` 。注意，这里加上了模块的路径，以便可以方便导入。

- args --
    需要传入handler类进行初始化的位置参数。

- kwargs --
    需要传入handler类进行初始化的名字参数。

- level --
    handler的日志级别。缺省为NOTSET。

- format --
    当前handler使用的日志输出格式。它有两种定义方式，一种是和后面的[LOG.Formatters]
    中的formatter对应，只是一个名字。另一种是当找不到一个名字时，会自动认为是格式串。
    所以简单情况下，可以直接在handler中定义format串，而不是先在[LOG.Formatters]
    中先定义好formatter，然后再引用它的名字。


从上面可以看出，handler和logger都可以定义自已的日志级别。同时root logger用于
定义缺省的日志级别。所你你可以根据需要在不同的对象上实现有区别的日志级别定义。


### formatter的定义

从前面可以看出，在定义logger和handler时都可以直接定义format串，并不一定需要定义
formatter。那么formatter的存在只是为了复用。你可以先定义几种常用的日志格式，
然后在定义logger和handler时引用它，这样会比较简单。只不过要注意，在[LOG]中定义的format
不能是formatter的引用，因为它是要使用basicConfig()来处理的，而它是不接受一个
Formatter对象的。formatter的定义形式为:

```
key = value
```

共中key为formatter的名字。

value为日志的格式串。具体定义参见  [Python的日志记录属性](http://docs.python.org/library/logging.html#logrecord-attributes) 。


## 应用介绍

### 使用

使用简单的日志可以直接使用root logger，方法为:

```
import logging
logging.info()
```

可以直接调用logging模块提供的相关的api进行输出。这是最简单的情况。
也可以主动获得root logger对象，如:


```
import logging
logger = logging.getLogger('')
```

使用某个命名logger对象，如:


```
import logging
logger = logging.getLogger('cache_manager.cache_helper')
```

如果，指定的日志名已经在settings.ini中配置了，则可以直接使用它的配置项。如果没有配置，则全部使用缺省的。

如果你使用了其它的组件，它们需要对日志进行配置，也可以在settings.ini中设置，一样可以生效。


### 使用建议

建议在你的程序中，每次要用到logger对象时，使用logging.getLogger(name)来获得一个logger对象。

