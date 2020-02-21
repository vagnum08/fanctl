# fanctl

Automatically generate a config for `fancontrol` based on a yml config and current hardware.

# Background

`fancontrol` from `lm-sensors` requires reconfiguration if the hwmon paths have been changed.
This usually happens either after a kernel update, a change in hardware, or depends on the 
order that kernel modules are loaded.

`fanctl` can be used to solve this issue by using a generic config ommiting the hwmon paths.
When `fanctl` is executed it tries to map the current hardware monitoring devices to the ones
declared in `/etc/fanctl/config.yml`.

After the mapping is complete the new configuration is written to `/etc/fancontrol`.

A systemD service is included, and if it is enabled it will regenerate FC config (if there are changes)
and exit. The service is run before `fancontrol.service` thus the config will always be up-to-date.

```bash
$ fanctl -h

usage: fanctl [-h] [-c fanctl config file] [-f fancontrol config file] [-v]

Fancontrol helper. Generates a configuration for fancontrol based on a fanctl
config and automatic mapping to current hardware.

optional arguments:
  -h, --help            show this help message and exit
  -c fanctl config file
                        Load custom config file
  -f fancontrol config file
                        Write to file instead of /etc/fancontrol. If file is
                        '-' the config is written to stdout.
  -v                    Increase verbosity (can be used multiple times)


```


