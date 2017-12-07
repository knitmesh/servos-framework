### 配置settings
    
#### 加载顺序

配置信息一般是放在 settings.ini 文件中的，目前有以下几个级别的 settings.ini 信息:

```python
default_settings.ini            #框架缺省的配置
services/
    service/settings.ini        #服务缺省的配置
    settings.ini                #项目配置
    local_settings.ini          #项目的本地配置
```
配置的加载顺序是从上到下的。对于service下的 settings.ini 文件，
它会按照 services 在 INSTALLED_SERVICES 中的定义顺序来处理。

#### 变量合并与替换
配置文件有先后加载顺序，后加载的项一旦发现有重名的情况，会进行以下特殊的处理:

1. 如果值为list, dict, set，则进行合并处理，即对于list，执行extend()，
   对于dict执行update，同时如果dict的值为dict或list，则会进行递归合并处理。
2. 如果是其它的值，则进行替換，即后面定义的值覆盖前面定义的值
3. 如果写法为:

    ```
    name <= value
    ```

则不管value是什么都将进行替換。


## 基本格式

settings.ini的写法是类ini格式，但是和标准的ini有所区别:


基本写法是:
    ```
    [section]
    name = value
    ```

section --
    节的名字，它应该是一个合法的标识符，即开始为字母或 `_` ，后续可
    以是字母或 `_` 或数字。大小写敏感。

name --
    key，不应包含 '='，可以不是标识符。name不能与Ini初始化时传入的env中的key重名，如果有会报错。

value --
    值，并且是符合python语法的，因此你可以写list, dict, tuple, 三重字符串和
    其它的标准的python的类型。可以在符合python语法的情况下占多行。也可以是简单
    的表达式。


1. 不支持多级，只支持两级处理
2. 注释写法是第一列为 `'#'`
3. 可以在文件头定义 `#coding=utf-8` 来声明此文件的编码，以便可以使用 `u'中文'` 这样的内容。


settings中的value只能定义基本的 Python 数据结构和表达式，因为它们将使用 eval 来执行，所以不能随意写代码，也不能导入其它的模块。

## 配置项引用

在定义 value ，我们可以直接引入前面已经定义好的配置项，有两种类型：

1. section内部引用，即引用的配置项是在同一节中当前配置项之前定义的其它的项，如：

    ```
    [DEFAULT]
    a = 'http://abc.com'
    b = a + '/index'
    ```
    
    一个section内部引用，直接在 value 部分写对应的配置项名称即可。但是要注意，因为 key 并不要求一定是标识符，所以，如果 key 的定义不是标识符，则直接引用的话，可能会因为 eval 执行时出错。这样就要使用第二种方法。
    
2. 跨section引用。它需要在配置项前面添加所在的 section 的名称，如：

    ```
    [DEFAULT]
    a = 'http://abc.com'
    [OTHER]
    b = DEFAULT.a + '/index'
    c = DEFAULT['a'] + '/index'
    d = OTHER.b + '/test'
    ```
    
    上面示例中， `b` 引用了 `DEFAULT` 中的配置项。 `c` 是采用dict下标的写法，适用于 key 不是标识符的情况。 `d` 则是以添加 section 名字的方式来实现section内部引用。

## 字符串引用扩展

引用方式一般是为了解决某个值在多个配置项中重复出现，而采用的减化手段。一般可以使用表达式的方法进行值的加工。如果是字符串，还可以直接在字符串中定义如 `{{expr}}` 这样的格式串来引用配置项的值。如：

```
[DEFAULT]
a = 'http://abc.com'
b = '{{DEFAULT.a}}/index'
```

在 ``{{}}`` 内的值会自动被替換为相应的配置项的值。这样有时写起来比表达式可能更方便。

## 环境变量的引用扩展

有时需要在配置中引入一些环境变量，如很多云环境都是把数据库等的参数放在环境变量中。
因此，如果你需要在配置文件中引入这些变量，可以使用：

```
a = '${MYSQL_HOST}:${MYSQL_PORT}'
a = $MYSQL_PORT
```


## settings的使用

settings在读取后会生成一个对象，要先获得这个对象再使用它。在需要使用settings的代码中通过导入来使用settings对象。
    
```
from servos import settings
```

有了settings对象，我们就可以调用它的方法和属性来引用配置文件中的各个值了。settings对象，你可以理解为一个二级的字典或二级的对象树。
如果key或section名都是标识符，通常情况下使用 `.` 的属性引用方式就可以了，不然可以象字典一样使用下标或 `get()` 等方法来使用。
常见的使用方式有:

1. `settings[section][key]` 以字典的形式来处理
1. `settings.get_var('section/key', default=None)` 这种形式可以写一个查找的路径的形式
1. `settings.section` 或 `settings.section.key` 以 `.` 的形式来引用section和key，不过要求section和key是标识符，且不能是保留字。
1. `for k, v in settings.section.items()` 可以把settings.section当成一个字典来使用，因此字典的许多方法都可以使用，如 in, has 之类的。

## 关于Lazy的处理说明

Lazy的处理是与配置项的引用有关。考虑以下场景：

* 某个service定义了一串配置项，如：

    ```
    [PARA]
    domain = 'http://localhost:8000'
    login_url = domain + '/login'
    ```
* 然后当部署到某个环境中时，用户希望在local_settings.ini中覆盖上面的domain的值
    为实际的地址。
    
这时会有这样的问题：在解析service的settings.ini文件时，domain的值已经解析出来了，
因此在处理 login_url 时，它的值也就固定下来了。等 local_settings.ini 再覆盖domain，
login_url 已经不会再重新计算了。

所以为了解决因为多个settings.ini按顺序导入，但是变量提前计算的问题，引入了Lazy的处理方式。
即，在读取多个settings.ini时，并不计算配置项的值，只是放到这个配置项对应的数组中，等全部读取完毕，
由框架主动调用settings的freeze()方法开始对所有未计算的值进行求值。通过这样的方法就延迟了求值的时间，
保证了最终想到的结果。

## 重要配置参数说明

以下按不同的节(section)来区分


### GLOBAL


```
[GLOBAL]
INSTALLED_SERVICES = [
    'message_collector',
    'cache_manager',
]
```

INSTALLED_SERVICES 为要加载的服务列表。框架会根据此配置加载启动指定服务。

### LOG

详情参见 [日志处理说明](log.md) 。


### FUNCTIONS

用于定义公共的一些函数，例如:


```
[FUNCTIONS]
encode = 'codec_plugin.encode'
```

在此定义之后，可以使用如下方式引用:


```
from servos import functions
functions.encode(message)
```


### BINDS

用于绑定某个信号的配置，例如:


```
[BINDS]
cache_manager.notify_dispatch = 'notify_dispatch', 'cache_manager.add_messages'
```

在配置中，每个绑定的函数应有一个名字，在最简单的情况下，可以省略名字，函数名就与绑定名相同。

BINDS有三种定义形式:


```python
function = topic                      #最简单情况，函数名与绑定名相同，topic是对应的信号
bind_name = topic, function           #给出信号和函数路径
bind_name = topic, function, {kwargs} #给出信号，函数路径和参数(字典形式)
```

其中function中是函数路径，比如 `servicename.model.function_name` ，
利用这种形式，框架可以根据 `servicename.model` 来导入函数。

上面的 `bind_name` 没有特别的作用，只是要求唯一，一方面利用它可以实现：
一个函数可以同时处理多个 topic 的情况，只要定义不同的 `bind_name` 即可。另一方面，
可以起到替換的作用，如果某个绑定不想再继续使用或替换为其它的配置，
可以写一个同名的`bind_name` 让后面的替換前面的。

