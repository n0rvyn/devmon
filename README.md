# DevMon - Devices Monitor with SNMP

## Also used for preventive maintenance and performance observability.

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

SNMP(Simple Network Management Protocol)大家都懂，不再缀述。
Python及其它语言也存在许多非常优秀的三方库，比如等等等（只知道pysnmp😂，感兴趣的谷歌下）。
既然现成的车都有了，那为什么还要造这个轮子，说句符合时代特征的话就是，不自己上嘴咋知道这肉好不好吃。
可能还是闲得吧。那么既然写都写了，也就照模照样大概介绍下。  
话说，训过狗的都知道，要想把毛娃教会了，其实首先需要规范的是自己的行为动作。
就拿SNMP来说，难点是怎么抓数据，怎么trap吗？
非也，难点是规范SNMP的入口（maybe，也许，possible，就当是），
由此入口编排一套通用的模板，才能方便以后名正言顺地（提问：此处为什么要用土也地？‘地’，‘的’，‘得’怎么用还记得不？）摸鱼。


本仓库包含以下内容：

1. SNMP客户端及事件定义
2. SNMP事件读取与入库（MongoDB）
3. 事件编排及发送日志服务器存档
[update]
4. SNMP性能数据点定义
5. SNMP巡检项定义

## To Do
1. 格式化SSH远程命令（行式和列式）的输出
2. 支持SNMP TRAP接收Agent消息投递
3. 规范代码，争取做成Python模块，方便安装

## 内容列表

- [背景](#背景)
- [文件结构](#文件结构)
- [安装](#安装)
- [配置说明](#配置说明)
- [使用说明](#使用说明)
- [维护者](#维护者)
- [如何贡献](#如何贡献)
- [使用许可](#使用许可)
- [打包示例](#打包示例)

## 背景

目前市面上的硬件产品，包括存储、主机、交换机、防火墙等，
均支持SNMP协议获取（trap应该算投递？这么表述不会伤害到完美主义者吧？）运行状态，
而作为一个只会巡检的机箱管理员，为了竭尽所能优化工作空间，
自然是要做一些一劳（确实很劳🥱，很徒劳）永逸的挣扎，好腾出时间来解放心灵。

> 新手码农的通病就是，代码少有注释，写完一上传，自己都看不懂。

## 文件结构

```raw
[4.0K]  .
├── [1.0K]  CHANGELOG.md
├── [4.0K]  devmon
│   ├── [4.0K]  conf
│   │   └── [1.8K]  devmon.yaml
│   ├── [2.1K]  cre_service.sh
│   ├── [4.0K]  devlist
│   │   ├── [4.0K]  a-side
│   │   ├── [4.0K]  b-side
│   │   ├── [4.0K]  examples
│   │   │   ├── [1.6K]  HW_OceanStor_RUNNING_STATUS_E.txt
│   │   │   ├── [3.4K]  snmp.Brocade.SanSwitch.yaml
│   │   │   ├── [   0]  snmp.example.GPFS.yaml
│   │   │   ├── [4.9K]  snmp.example.zh.yaml
│   │   │   ├── [6.4K]  snmp.general.linux.yaml
│   │   │   ├── [2.2K]  snmp.HillStone.Hxxxx.yaml
│   │   │   ├── [3.4K]  snmp.Huawei.OceanStor.yaml
│   │   │   ├── [1.7K]  snmp.Huawei.USG.yaml
│   │   │   ├── [1.3K]  snmp.IBM.XIV.yaml
│   │   │   ├── [3.6K]  snmp.Juniper.Jxxxx.yaml
│   │   │   └── [ 865]  snmp.TopSec.N4000.yaml
│   │   └── [4.0K]  maintaining
│   ├── [ 44K]  devmon.py
│   ├── [4.0K]  log
│   ├── [4.0K]  pic
│   │   └── [645K]  grafana_devmon.png
│   └── [4.0K]  src
│       ├── [4.0K]  core
│       │   ├── [1.4K]  cmdb.py
│       │   ├── [3.3K]  cre_case.py
│       │   ├── [1.2K]  cre_point.py
│       │   ├── [1.5K]  encrypt.py
│       │   ├── [ 901]  __init__.py
│       │   ├── [2.8K]  log.py
│       │   ├── [4.0K]  mongo.py
│       │   ├── [1.9K]  pushmsg.py
│       │   ├── [4.0K]  __pycache__
│       │   ├── [7.0K]  read_devlist.py
│       │   ├── [ 18K]  snmp.py
│       │   └── [9.6K]  ssh.py
│       ├── [1.2K]  __init__.py
│       ├── [4.0K]  __pycache__
│       └── [4.0K]  type
│           ├── [1.7K]  case.py
│           ├── [ 112]  event.py
│           ├── [ 737]  __init__.py
│           ├── [2.5K]  oid.py
│           ├── [ 343]  point.py
│           ├── [4.0K]  __pycache__
│           ├── [1.1K]  snmpagent.py
│           ├── [ 322]  sshagent.py
│           └── [ 854]  sshcmd.py
├── [ 34K]  LICENSE
├── [ 14K]  README.md
└── [ 105]  requirements.txt

16 directories, 39 files
```

## 安装

### 1. 已测试的Python版本

> Python-3.11	

> 若RHEL7版本需安装Python3.11, 自行谷歌或者参考下一篇文章（如何在RHEL7上升级Python3.11）

### 2. 必要的Python模块
```bash
python3 -m venv /path/to/your/own/venv
source /path/to/your/own/venv/bin/activate
python3 -m pip install -r requirements.txt
```

### 3. 需安装的Linux组件（以RHEL7为例）
```bash
rpm -ivh mongodb-org-server-x.y.z-el7.x86_64.rpm
yum install -y net-snmp
```

## 配置说明

### 1. 主体配置
> 文件：conf/devmon.conf

### 2. Grafana Linux主机性能数据看板（beta）
> 目录: grafana/

### 3. 定义主机及OID列表

> 目录：devlist/a-side, devlist/b-side  # 有效的设备列表，A/B列区分定义，读取SNMP数据时间隔了指定的时间
> 目录：examples  # 已验证的某类设备（型号）SNMP定义模板
> 目录：maintaining  # 对维护中的设备屏蔽事件读取（将设备文件mv到该目录即可）

## 使用说明
### 1. 对已定义的SNMP主机及OID推送事件（目前仅支持rsyslog）
```bash
python3 devmon.py run  # 读取设备列表的SNMP事件，并入库、存档rsyslog
python3 devmon.py service  # 以定义的间隔时间持续读取
```

### 2. 对已定义的SNMP主机及OID巡检

#### 2.1 巡检全部定义的设备
```bash
python3 devmon.py pm  # 读到有效设备OID值，并以label进行分类
```

#### 2.2 巡检某台设备
```bash
python3 devmon.py pm <DEVICE ADDRESS>
```

### 3. 抓取SNMP可读的设备性能数据（以perf: True定义）
```bash
python3 devmon.py perf
```

命令输出示例：
```bash
(venv) $ python3 devmon.py pm
=================================================================================================
----------------------------------------    localhost    ----------------------------------------
SystemName................................................................................ backup
Memory Size............................................................................. 12136572
MemoryFreePercent......................................................................... PASSED
CPU Idle.................................................................................. FAILED
SWAPAvailablePercent...................................................................... PASSED
Storage Used Percent...................................................................... FAILED
NetworkInterface.......................................................................... FAILED
Disk I/O Load 15(min) Avg................................................................. PASSED
标签CPU Idle                      当前值38               限制区0-60      设备ssCpuIdle
标签NetworkInterface              当前值down             阈值区up(1)     设备enp4s0
标签NetworkInterface              当前值down             阈值区up(1)     设备sit0
标签NetworkInterface              当前值down             阈值区up(1)     设备wlp3s0b1
标签Storage Used Percent          当前值83.89            阈值区-1-80     设备/opt
标签Storage Used Percent          当前值87.84            阈值区-1-80     设备/usr/portage
```

## SNMP入口定义规范样本（部分）

```yaml
---
address: localhost  # the address which been listened to by SNMP Daemon
region: SomeRegion  # The region of device, e.g., DCA, DCB, DataCenterA...
area: SomeArea  # the business area
addr_in_cmdb: SomeAddr  # the address which related with Resource ID in CMDB
rid: 'THis is resource ID'
snmp:
  version: '2c'  # the SNMPD version
  community: 'public'  # the SNMPD community
  timeout: 1  # second(s) to timeout
  retries: 1  # time(s) to retry after failed
  OIDs:
  - id: 'sysName.0'
    label: SystemName
    explanation: '主机名'
    show: True
  - id: 'hrMemorySize.0'
    label: 'Memory Size'
    explanation: '内存大小'
    show: True
```

## 维护者

[@n0rvyn](https://github.com/n0rvyn)

## 如何贡献

非常欢迎你的加入！[提一个 Issue](https://github.com/RichardLitt/standard-readme/issues/new) 或者提交一个 Pull Request。
(即使你会pull，奈何作者搞不了merge😂)

## 使用许可

[MI没有T](LICENSE)
没啥许可，都没搞清楚许可之间啥区别，想抄就抄，不介意。


## 打包示例
> 试着用pyinstaller打包，效果不佳，有大佬忍不住的话可以指点一二。

```bash
pyinstaller devmon.py -F \ 
    -p src/core/log.py \
    -p src/core/mongo.py \
    -p src/core/pushmsg.py \
    -p src/core/readfile.py \
    -p src/core/rid.py \
    -p src/core/snmp.py \
    -p src/core/ssh.py \
    -p src/type/case.py \
    -p src/type/oid.py \
    -p src/type/snmpagent.py \
    -p src/type/sshagent.py \
    -p src -p src/core/ -p src/type/
```
