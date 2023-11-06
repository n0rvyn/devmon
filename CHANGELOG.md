# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [https://norvyn.com](https://norvyn.com).

## [Unreleased]
### [0.0.8] - 2023-11-06
- Add support for OID group (a set of OIDs related by name or value)
- Add support for MongoDB Time Series collection reading and writing

### [0.0.4] - 2023-10-14
#### Fixed
- Fix TypeError for None value of l_voids (line: 480 file: devmon.py)

### [0.0.3] - 2023-10-13
#### Add
- add support for syncing CMDB resource ID to MongoDB

### [0.0.2] - 2023-10-10
#### Add
- add support for Juniper J3400 HA, Fru & Temp stat.
- add support for SNMPD community which has symbol '!'
- add support for OID table reading

#### Changed
- set MongoDB ping command timeout to 2 seconds

#### Need
- fetch port index from every line snmpwalk from sfp OID
- change FAILED to N/A when pm Huawei Storage via SSH failed with connection




[Unreleased]: https://norvyn.com
[3.3]: https://norvyn.com
