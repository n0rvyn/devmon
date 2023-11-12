#!/bin/bash
#
#
platform="$1"

if [ "$platform" != "6" ] -a [ "$platform" != '7' ]; then
  echo "Following the script a RHEL release ID. '6' or '7', choose one."
  exit 1
fi

if ! grep 'devmon' /etc/passwd &>/dev/null || ! grep 'devmon' /etc/group &>/dev/null; then
  echo "User & group 'devmon' should be created first."
  exit 1
fi

PyPATH='/home/scripts/venv/bin/python3'
ToolPATH='/home/scripts/40-Python/devmon-0.0.3/devmon/devmon.py'

function exist() {
  if ls $1 >/dev/null 2>&1; then
    return 0
  else
    return 1
  fi
}

if ! exist $PyPATH; then
  echo "Python path not exist."
  exit 1
fi

if ! exist $ToolPATH; then
  echo "DevMon path not exist."
  exit 1
fi

if [ "$platform" == '7' ]; then

# for RHEL7
cat > /etc/systemd/system/devmon.service << EOF
[Unit]
Description=Devices Hardware Monitor Console
DefaultDependencies=no
After=sysinit.target local-fs.target network.target

[Service]
User=devmon
Group=devmon
Type=simple
ExecStart=$PyPATH $ToolPATH service
ExecStop=/bin/kill -HUP \$MAINPID
KillMode=process
Restart=on-failure
RestartSec=300s

[Install]
WantedBy=multi-user.target
EOF

else

# for Rhel6
cat > /etc/init.d/devmon << EOF
#!/bin/bash
#
# DevMon     Devices Hardware Monitor Console
#
# chkconfig: 2345 55 25
#
# processname: devmon

### BEGIN INIT INFO
# Provides:       devmon
# Required-Start: $local_fs $network $syslog
# Required-Stop:
# Default-Start:  2 3 4 5
# Default-Stop:   0 1 6
# Short-Description: Devices Hardware Monitor Console
# Description:       Monitor for Devices' SNMP
#
### END INIT INFO

# source function ENV
export SHELL=/bin/bash

RETVAL=0
prog="devmon"

# Some variable to make the script more readable
PyPATH="$PyPATH"
ToolPATH="$ToolPATH"

start() {
  echo -n \$"Starting \$prog: "
  \$PyPATH \$ToolPATH &
  RETVAL=\$?
  [ \$RETVAL == '0' ] && echo "success" || echo "failed"
}

stop() {
  echo -n \$"Stop \$prog: "
  ps -ef | grep "\$PyPATH \$ToolPATH" | grep -v grep | awk '{print "kill -9 "\$2}' | sh &&  echo "success" || echo "failed"
  RETVAL=\$?
}

case "\$1" in
        start)
                start
                ;;
        stop)
                stop
                ;;
        restart)
                stop
                start
                ;;
        status)
                ps -ef | grep "\$PyPATH \$ToolPATH" | grep -v grep
                RETVAL=\$?
                ;;
        *)
                echo \$"Usage: \$0 {start|stop|restart}"
                RETVAL=2
esac
exit $RETVAL
EOF

chmod +x /etc/init.d/devmon

fi

exit 0