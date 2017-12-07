# 命令行命令说明

## servos

当运行不带参数的servos命令时，会显示一个帮助信息，但是因为命令很多，
所以这个帮助只是列出可用命令的清单，如:


```
Usage: servos [global_options] [subcommand [options] [args]]

Global Options:
  --help                show this help message and exit.
  -v, --verbose         Output the result in verbose mode.
  -s SETTINGS, --settings=SETTINGS
                        Settings file name. Default is "settings.ini".
  -y, --yes             Automatic yes to prompt.
  -L LOCAL_SETTINGS, --local_settings=LOCAL_SETTINGS
                        Local settings file name. Default is
                        "local_settings.ini".
  -d SERVICES_DIR, --dir=SERVICES_DIR
                        Your services directory, default is "services".
  --pythonpath=PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/myproject".
  --version             show program's version number and exit.

Type 'servos help <subcommand>' for help on a specific subcommand.

Available subcommands:
  find
  install
  makecmd
  makeproject
  makeservice
  runserver
```

在servos中，有一些是全局性的命令，有一些是由某个service提供的命令。因此当你在一个
project目录下运行servos命令时，它会根据当前project所安装的servos来显示一个完整的命令清单。
上面的示例只显示了在没有任何service时的全局命令。

如果想看单个命令的帮助信息，可以执行:


```
#> servos help runserver
Usage: servos runserver [options] 

Start a new development server.

Options:
  -b, --background  If run in background. Default is False.
```

### 常用全局选项说明

除了命令，servos还提供了全局可用的参数，它与单个命令自已的参数不同，它是对所有命令都可以使用的参数。

### runserver

启动开发服务器:


```
Usage: servos runserver [options] 

Start a new development server.

Options:
  -b, --background  If run in background. Default is False.  
```

示例：

```
servos runserver #启动服务
```


### makeproject

生成一个project框架，它将自动按给定的名字生成一个project目录，同时包含有初始子目录和文件。


```
Usage: servos makeproject projectname
```

示例：

```
servos makeproject project
```

创建project项目目录。


### makeservice

生成一个service框架，它将自动按给定的名字生成一个service目录，同时包含有初始子目录和文件。


```
Usage: servos makeservice servicename
```

示例：

```
servos makeservice Hello
```

创建Hello服务。如果当前目前下有services目录，则将在services目录下创建一个Hello的目录，
并带有初始的文件和结构。如果当前目前下没有services目录，则直接创建Hello的目录。


### makecmd

向指定的service或当前目录下生成一个commands.py模板。

```
Usage: servos makecmd [servicename, ...]
```

示例：

```
servos makecmd Hello
```

### find

查找对象，目前仅支持查找配置项。


```
Usage: servos find -o option
```


示例：

```
servos find -o GLOBAL/DEFAULT_ENCODING
```

### install

```
Usage: servos install [servicename,...]
```

执行在项目目录下或service目录下的requirements.txt。如果不指定servicename，则是扫描整个项
目，如果指定servicename，则只扫描指定service下的requirements.txt。
