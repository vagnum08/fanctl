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
# Usage

Normally, you won't need to run `fanctl` manually. When the service is enable it will work automatically on every boot.

However to check the settings are correct you can run:

```bash
fanctl -f - -vv
```

This will display the generated fancontrol config along with debugging information.


# Installation

The project uses Meson as its build system.
As such it requires the `meson`  and `ninja` packages to be installed.
Additionally since the package uses a yaml configuration, `python3` and `python-yaml` are also required. 

To install `fanctl` run the following:

```bash

meson build --prefix=/usr --buildtype=release -Dsystemddir=/usr/lib/systemd
sudo ninja -Cbuild install

```
**Note**: _The option `systemddir` must point to the systemD directrory on the system. Usually is on `/usr/lib/systemd`._

To use the service without reboot the systemd daemon must be reloaded, i.e. `systemctl daemon-reload`

If you want `fanctl` to be executed at boot enable the service.
```bash
systemctl enable fanctl.service

```


To uninstall fanctl execute `sudo ninja -Cbuild uninstall` from the project directory.

