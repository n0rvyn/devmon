# DevMon - Devices Monitor with SNMP

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

SNMP(Simple Network Management Protocol)大家都懂，不再缀述。
Python及其它语言也存在许多非常优秀的三方库，比如等等等（只知道pysnmp😂，感兴趣的谷歌下）。
既然现成的车都有了，那为什么还要造这个轮子，说句符合时代特征的话就是，不自己上嘴咋知道这肉好不好吃。
可能还是闲得吧。那么既然写都写了，也就照模照样大概介绍下。  
话说，训过狗的都知道，要想把毛娃教会了，其实首先需要规范的是自己的切入点。
就拿SNMP来说，难点是怎么抓数据，怎么trap吗？
非也，难点是规范SNMP的入口（maybe，也许，possible，就当是），
由此入口编排一套通用的模板，才能方便以后名正言顺地（提问：此处为什么要用土也地？‘地’，‘的’，‘得’怎么用还记得不？）摸鱼。


本仓库包含以下内容：

1. SNMP客户端及事件定义
2. SNMP事件读取与入库（MongoDB）
3. 事件编排及发送日志服务器存档

## To Do
1. 格式化SSH远程命令（行式和列式）的输出
2. 支持SNMP TRAP接收Agent消息投递
3. 规范代码，争取做成Python模块，方便安装

## 内容列表

- [背景](#背景)
- [文件结构](#文件结构)
- [安装](#安装)
- [使用说明](#使用说明)
- [示例](#示例)
- [维护者](#维护者)
- [使用许可](#使用许可)

## 背景

目前市面上的硬件产品，包括存储、主机、交换机、防火墙等，
均支持SNMP协议获取（trap应该算投递？这么表述不会伤害到完美主义者吧？）运行状态，
而作为一个只会巡检的机箱管理员，为了竭尽所能优化工作空间，
自然是要做一些一劳（确实很劳🥱，很徒劳）永逸的挣扎，好腾出时间来解放心灵。

> 新手码农的通病就是，代码少有注释，写完一上传，自己都看不懂。

## 文件结构

├── CHANGELOG.md  
├── devmon  
│   ├── conf  
│   │   └── devmon.yaml  
│   ├── cre_service.sh  
│   ├── devlist  
│   │   └── examples  
│   │       ├── snmp.example.zh.yaml  
│   │       ├── snmp.general.linux.yaml  
│   │       ├── snmp.HillStone.Hxxxx.yaml  
│   │       ├── snmp.Huawei.OceanStor.yaml  
│   │       ├── snmp.Huawei.USG.yaml  
│   │       ├── snmp.IBM.SanSwitch.yaml  
│   │       ├── snmp.IBM.XIV.yaml  
│   │       ├── snmp.Juniper.Jxxxx.yaml  
│   │       └── snmp.TopSec.N4000.yaml  
│   ├── devmon.py  
│   └── src  
│       ├── core  
│       │   ├── cmdb.py  
│       │   ├── encrypt.py  
│       │   ├── __init__.py  
│       │   ├── log.py  
│       │   ├── mongo.py  
│       │   ├── pushmsg.py  
│       │   ├── readfile.py  
│       │   ├── snmp.py  
│       │   └── ssh.py  
│       ├── __init__.py  
│       └── type  
│           ├── case.py  
│           ├── __init__.py  
│           ├── oid.py  
│           ├── snmpagent.py  
│           ├── sshagent.py  
│           └── sshcmd.py  
├── README.md  
└── requirements.txt  

## 安装

### 1. 已测试的Python版本

> Python-3.11	

> 若RHEL7版本需安装Python3.11, 自行谷歌或者参考下一篇文章（如何在RHEL7上升级Python3.11）

### 2. 必要的Python模块  

试着运行`python3 devmon.py`, 提示缺什么装什么即可。通常来讲，要安装以下模块：

```bash
python3 -m pip install PyYAML PyMySQL pymongo
```

### 3. 需安装的Linux组件（以RHEL7为例）
```bash
rpm -ivh mongodb-org-server-x.y.z-el7.x86_64.rpm

yum install -y net-snmp
```

## 使用说明

### 1. 主体配置
> 文件：conf/devmon.conf

### 2. 定义主机及OID列表

> 目录：devlist/a-side, devlist/b-side  # 有效的设备列表  
> 目录：examples  # 已验证的某类设备SNMP定义模板  
> 目录：maintaining  # 对维护中的设备屏蔽事件读取（将设备文件mv到该目录即可）

### 3. 对已定义的SNMP主机及OID推送事件
```bash
python3 devmon.py run  # 读取设备列表的SNMP事件，并入库、存档rsyslog
python3 devmon.py service  # 以定义的间隔时间持续读取
```

### 4. 对已定义的SNMP主机及OID巡检
```bash
python3 devmon.py pm  # 读到有效设备OID值，并以label进行分类
```

命令输出：
```raw
$ python3 devmon.py pm
=================================================================================================
----------------------------------------  172.16.10.250  ----------------------------------------
Memory Size............................................................................... PASSED
System Name............................................................................... PASSED
Network Interface......................................................................... FAILED
MemoryFreePercent......................................................................... PASSED
SWAPAvailablePercent...................................................................... PASSED
Disk I/O Load 15(min) Avg Lvl1............................................................ PASSED
Disk I/O Load 15(min) Avg Lvl3............................................................ PASSED
CPU Usage................................................................................. PASSED
标签Network Interface                   当前值down(2)    阈值区up(1)     设备br0                 
标签Network Interface                   当前值down(2)    阈值区up(1)     设备virbr0              
=================================================================================================
----------------------------------------    localhost    ----------------------------------------
Storage Used Percent...................................................................... FAILED
Network Interface......................................................................... FAILED
Memory Size............................................................................... PASSED
SystemName................................................................................ PASSED
标签Network Interface                   当前值down(2)    阈值区up(1)     设备VHC128              
标签Network Interface                   当前值down(2)    阈值区up(1)     设备XHC0                
标签Network Interface                   当前值down(2)    阈值区up(1)     设备XHC1                
标签Network Interface                   当前值down(2)    阈值区up(1)     设备XHC20               
标签Network Interface                   当前值down(2)    阈值区up(1)     设备ap1                 
标签Network Interface                   当前值down(2)    阈值区up(1)     设备gif0                
标签Network Interface                   当前值down(2)    阈值区up(1)     设备stf0                
标签Storage Used Percent                当前值84.75      限制区80-100    设备/                   
标签Storage Used Percent                当前值84.75      限制区80-100    设备/System/Volumes/Data
标签Storage Used Percent                当前值84.75      限制区80-100    设备/System/Volumes/Preboot
标签Storage Used Percent                当前值84.75      限制区80-100    设备/System/Volumes/Update
标签Storage Used Percent                当前值84.75      限制区80-100    设备/System/Volumes/VM  
标签Storage Used Percent                当前值91.60      限制区80-100    设备/Library/Developer/CoreSimulator/Volumes/watchOS_20T253
标签Storage Used Percent                当前值98.00      限制区80-100    设备/dev                

```

## SNMP入口定义规范样本

```yaml
---
# 设备IP，SNMP Daemon接口地址，必选项
address: SomeAddress
# 设备物理区域， 如：DCA，DataCenterA...，必选项
region: SomeRegion
# 设备业务区域，如Dev, Prod...， 必选项
area: SomeArea
# 设备在CMDB中录入IP，用于关联CMDB中资源ID，必选项
addr_in_cmdb: SomeAddr
# 手动指定资源ID，如无此字段，则尝试在MongoDB(需先同步) 对应表中查找，可选项，数量少建议手动查找指定。
rid: 'THis is resource ID'
# SNMP客户端配置
snmp:
  # SNMP版本，2c或者3，必选项
  version: '2c'
  # SNMP团体名，如v3则不需要，v2c时必选
  community: 'public'
  # SNMP v3协议用户名，v3协议必选项
  username: 'user1'
  # SNMP MIB库，部分设备必选
  mib: 'ANY-MIB'
  # 博科系光纤交换机上下文（虚拟光交）ID，配置了虚拟光交的必选
  context: 128
  # snmpwalk读取OID超时时间，可选
  timeout: 2
  # snmpwalk读取OID失败后尝试次数，可选
  retries: 1
  # OID关联配置
  OIDs:
  # 以单个OID定义，id, id_range, table三必选一
  - id: 'SNMPv2-MIB::sysName.0'
    # OID标签，用于巡检展示分类（建议字符不宜过长），必选项
    label: System Name
    # OID解释，用于拼凑告警内容，必选项
    explanation: '主机名'
    # OID参考值，等于或包含OID读取值，则视为正常，否则触发告警，与watermark二必选一
    reference: 'monitor'
  # 以OID范围定义
  - id_range:
      # OID开始值，如果不以.1(为例)结尾，则默认起始索引为1，以id_range定义必选项
      start: 'ifOperStatus.1'
      # OID范围内的总数量，或以 'end' 关键字为终止ID，与'end'二必选一
      count: 31  # the number of the OID range
      # end: 'ifOperStatus.3'
    label: 'NetworkInterface'
    explanation: '网卡状态'
    # OID名称或者描述需从其它OID读取的，则定义'related_symbol'，索引自动参考当前OID
    # 注意：不以索引号结尾！！！
    # 根据需要配置，可选。
    related_symbol: 'IF-MIB::ifDescr'
    reference: 'up(1)'  # a reference value which been considered as normal stat
  # 列表定义OID，OID为列表入口(table entry)，三必选一
  - table: 'hrStorageUsed'
    # 需读取当前索引号的OID列表入口，可选项
    table_index: 'hrStorageIndex'
    label: 'Storage Used Percent'
    explanation: '存储设备使用率'
    # 用于拼凑告警内容，可选，有默认值。
    alert: '严重异常，请管理员务必关注！'
    # 需排除读取的索引号，可选。
    exclude_index: '35, 36, 44, 73'
    # 同上，读取OID实际名称或者描述，可选。
    related_symbol: 'hrStorageDescr'
    # 取值需计算，例如存储百分比，可选。
    arithmetic: '%'
    # 算术另一元的OID列表入口，'arithmetic', 'arith_symbol', 'arith_pos'三者在则同在，不在则都不在
    arith_symbol: 'hrStorageSize'
    # 额外取值的OID处于算术符号的位置（1或者2），1在前，2在后
    arith_pos: 2
    # OID结果需比对阈值（或者限制值）范围，与参考值二必选一。
    watermark:
      low: -1
      high: 80
      # 限制类型开关；
      # True则该水位为限制区间：取值在low与high之间则告警，之外则正常；
      # False则该水位为阈值区间，取值在low与high之间则正常，反之则告警；
      # 可选值
      # restricted: False


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
