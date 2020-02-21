#!@PYTHON@

# fanctl.py
#
# Copyright 2020 Evangelos Rigas
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import argparse
from pathlib import Path
import yaml
import logging

CONF = "/etc/fanctl/config.yml"
FCCONF = Path("/etc/fancontrol")
HWP = Path("/sys/class/hwmon")
VERBO = [logging.WARN, logging.INFO, logging.DEBUG]

log = logging.getLogger("fanctl")


def get_devpath(path):
    """Get the device path of the HWMON entry

    Args:
      path (pathlib.Path): The /sys/class/hwmon/hwmon? path

    Returns:
      (pathlib.Path): The /sys/device/ path of the hwmon

    """
    p = "/".join(path.resolve().parts[2:-2])
    return Path(p)


def _generate_devname(devices):
    """Generate DEVNAME config entry

    Args:
      devices (dict): The fanctl config dict

    Returns:
      (str): The DEVNAME entry

    """
    devname = "DEVNAME="
    for name, settings in devices.items():
        hwmon = settings["hwmon"]["id"]
        devname += f"{hwmon}={name} "
    return devname


def _generate_devpath(devices):
    """Generate DEVPATH config entry

    Args:
      devices (dict): The fanctl config dict

    Returns:
      (str): The DEVPATH entry

    """
    devpath = "DEVPATH="
    for name, settings in devices.items():
        hwmon = settings["hwmon"]["id"]
        path = settings["hwmon"]["devpath"]
        devpath += f"{hwmon}={path} "
    return devpath


def _generate_fctemps(devices):
    """Generate FCTEMPS config entry

    Args:
      devices (dict): The fanctl config dict

    Returns:
      (str): The FCTEMPS entry

    """
    fctemps = "FCTEMPS="
    for name, settings in devices.items():
        hwmon = settings["hwmon"]["id"]
        pwm = settings["pwm"]
        temp = settings["temp"]
        fctemps += f"{hwmon}/pwm{pwm}={hwmon}/temp{temp}_input "
    return fctemps


def _generate_fcfans(devices):
    """Generate FCFANS config entry

    Args:
      devices (dict): The fanctl config dict

    Returns:
      (str): The FCFANS entry

    """
    fcfans = "FCFANS="
    for name, settings in devices.items():
        hwmon = settings["hwmon"]["id"]
        pwm = settings["pwm"]
        fan = settings["fan"]
        fcfans += f"{hwmon}/pwm{pwm}={hwmon}/fan{fan}_input "
    return fcfans


def _generate_temp_limits(devices):
    """Generate MINTEMP/MAXTEMP config entries

    Args:
      devices (dict): The fanctl config dict

    Returns:
      (str): The MINTEMP/MAXTEMP entries

    """
    mintemp = "MINTEMP="
    maxtemp = "MAXTEMP="

    for name, settings in devices.items():
        hwmon = settings["hwmon"]["id"]
        pwm = settings["pwm"]
        lim = settings["limits"]["temp"]
        mintemp += f"{hwmon}/pwm{pwm}={lim[0]} "
        maxtemp += f"{hwmon}/pwm{pwm}={lim[1]} "
    return mintemp + "\n" + maxtemp


def _generate_start_limits(devices):
    """Generate MINSTART/MINSTOP config entries

    Args:
      devices (dict): The fanctl config dict

    Returns:
      (str): The FCTEMPS entries

    """
    minstart = "MINSTART="
    maxstop = "MINSTOP="

    for name, settings in devices.items():
        hwmon = settings["hwmon"]["id"]
        pwm = settings["pwm"]
        lim = settings["limits"]["st"]
        minstart += f"{hwmon}/pwm{pwm}={lim[0]} "
        maxstop += f"{hwmon}/pwm{pwm}={lim[1]} "
    return minstart + "\n" + maxstop


def _generate_pwm_limits(devices):
    """Generate MINPWM/MAXPWM config entries

    Args:
      devices (dict): The fanctl config dict

    Returns:
      (str): The MINPWM/MAXPWM entries

    """
    minpwm = "MINPWM="
    maxpwm = "MAXPWM="

    for name, settings in devices.items():
        hwmon = settings["hwmon"]["id"]
        pwm = settings["pwm"]
        lim = settings["limits"]["pwm"]
        minpwm += f"{hwmon}/pwm{pwm}={lim[0]} "
        maxpwm += f"{hwmon}/pwm{pwm}={lim[1]} "
    return minpwm + "\n" + maxpwm


def hwmon_detect():
    """Find the hwmon devices and their paths

    Returns:
      (dict): A dict containing the hwmon device and its sysfs path

    """
    log.debug("Scanning for HWMON devices")

    paths = {}
    for p in sorted(HWP.iterdir()):
        np = p.joinpath("name")
        if np.exists():
            driver = np.read_text().strip()
            abs_path = p.resolve()
            log.debug(f"Found {p.name} with driver: {driver} in {abs_path}")
            paths.update({driver: {"devpath": get_devpath(p), "hwmon": p.name}})

    return paths


def validate_config(config_dict):
    """Validate fanctl config file

    Args:
      config_dict (dict): fanctl config dict

    """
    for device, settings in config_dict["devices"].items():
        for setting in ["pwm", "temp", "fan", "limits"]:
            if setting not in settings:
                return False
        for lim in ["st", "temp", "pwm"]:
            if lim not in settings["limits"]:
                return False
            if len(settings["limits"][lim]) < 2:
                return False
    return True


def _parse_config(config_file):
    """Parse fanctl config file

    Args:
      config_file (pathlib.Path): The path of the fanctl config file

    Returns:
      (dict): A dict with the fanctl config

    """
    conf = Path(config_file)
    if conf.exists():
        conf = yaml.safe_load(conf.open())
        if not validate_config(conf):
            raise Exception("Aborting. Configuration is invalid.")
        return conf["devices"]
    else:
        raise FileNotFoundError(config_file)


def find_hwmon_file(path, hwmon, hwmon_type, mon_id):
    """Check that a tmp/pwm/fan file exists in hwmon path

    Args:
      path (pathlib.Path): sysfs device path
      hwmon (str): hwmon entry (e.g. hwmon1)
      hwmon_type (str): One of temp, pwm, and fan
      mon_id (int): file number (e.g. 1 for temp1_input)

    Returns:
      (bool): True if exists, False otherwise

    """
    hwmon_path = Path("/sys").joinpath(path, "hwmon", hwmon)
    hwmon_files = list(hwmon_path.glob(f"{hwmon_type}{mon_id}_*"))
    if hwmon_files:
        return True
    else:
        return False


def assert_hwmon_file(dev, hwmon_type, hwmon_id):
    """Check that a tmp/pwm/fan file exists in hwmon path

    Args:
      dev (dict): device config
      hwmon_type (str): One of temp, pwm, and fan
      mon_id (int): file number (e.g. 1 for temp1_input)

    Returns:
      (bool): True if exists, False otherwise
    
    """

    return find_hwmon_file(dev["devpath"], dev["hwmon"], hwmon_type, hwmon_id)


def generate_mapping(config):
    if config is None:
        config = CONF  # Use default config file
    try:
        conf = _parse_config(config)
    except FileNotFoundError as e:
        log.error(f"Failed to read fanctl config file: {config}.")
        exit(1)

    paths = hwmon_detect()
    config = {}
    # TODO: Have a hash/label for each entry
    # It will allow multiple definitions for the same driver
    # but different hardware
    for device, settings in conf.items():
        if device in paths:
            log.info(
                f"Path for {device} exists on the system. Proceeding with mapping."
            )
            for hwmon_type in ["pwm", "fan", "temp"]:
                dev = paths[device]
                hwmon_id = settings[hwmon_type]
                # Assert that the sensors exist in the hwmon path
                if not assert_hwmon_file(dev, hwmon_type, hwmon_id):
                    log.error(
                        f'HWMON file for {device}-->{dev["hwmon"]}/{hwmon_type}{hwmon_id} is missing.'
                    )
                    raise FileNotFoundError()

            # Update the config with the current paths since files exists
            settings.update({"hwmon": {"devpath": dev["devpath"], "id": dev["hwmon"]}})
            config.update({device: settings})

    return config


def config_invalid(config_dict):
    """Check if hardware has been changed invalidating the config
    
    Args:
      config_dict (dict): fanctl config dict
    Returns:
      (bool): True if config is invalid, else False

    """
    if not FCCONF.exists():
        return True

    for line in FCCONF.read_text().splitlines():
        if line.startswith("DEVNAME"):
            # {k: v for v, k in [dev.split("=") for dev in l.strip("DEVNAME=").split()]}
            devs = line.strip("DEVNAME=").split()
            for dev in devs:
                mon, name = dev.split("=")
                if config_dict[name]["hwmon"]["id"] != mon:
                    return True
            return False


def generate_fc_config(config, outfile=sys.stdout):
    """ Generate fancontrol config

    Args:
      config (dict): fanctl config dict
      outfile: The file stream to write the config

    """
    log.info("Generating fancontrol config...")
    print(_generate_devpath(config), file=outfile)
    print(_generate_devname(config), file=outfile)
    print(_generate_fctemps(config), file=outfile)
    print(_generate_fcfans(config), file=outfile)
    print(_generate_temp_limits(config), file=outfile)
    print(_generate_start_limits(config), file=outfile)
    print(_generate_pwm_limits(config), file=outfile)
    if not (outfile.name == sys.stdout.name):
        log.info(f"Config was written to {outfile.name}")


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Fancontrol helper.\n Generates a configuration for fancontrol based on a fanctl config and automatic mapping to current hardware.",
        prog="fanctl",
    )
    parser.add_argument(
        "-c", type=str, metavar="fanctl config file", help="Load custom config file"
    )
    parser.add_argument(
        "-f",
        type=str,
        metavar="fancontrol config file",
        help="Write to file instead of /etc/fancontrol. If file is '-' the config is written to stdout.",
    )
    parser.add_argument(
        "-v",
        action="count",
        default=0,
        help="Increase verbosity (can be used multiple times)",
    )
    args = parser.parse_args()

    args.v = min(args.v, 2)  # max level (DEBUG)

    loglevel = VERBO[args.v]
    logging.basicConfig(level=loglevel)

    #  Generate a map between the config and the current hardware.
    try:
        config = generate_mapping(args.c)
    except Exception as e:
        log.exception("Failed to read fanctl config.")
        exit(-1)

    # If FCCONF points to the right hwmon skip generation.
    if not config_invalid(config) and not args.f:
        log.info("Configuration is valid. Skipping regeneration.")
        exit(0)

    # Write the fancontrol config to a file or stdout
    try:
        if args.f:
            if args.f == "-":
                conf_out = sys.stdout
            else:
                conf_out = Path(args.f).open("w")
        else:
            conf_out = Path("/etc/fancontrol").open("w")
        generate_fc_config(config, conf_out)
        exit(0)
    except IOError as e:
        log.error(e)
        if e.errno == 13:
            print(f"You don't have permissions to change {e.filename}")
        exit(1)
