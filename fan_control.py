#!/usr/bin/python
"""
Config file example:

{
    "temp_on": 75,
    "temp_off": 55
}

"""
import RPi.GPIO as GPIO
import os, sys, time, re, json
from pathlib import Path
import logging

DATA_DIR = Path(os.getenv('FAN_CONTROL_LOG_DIR') or '/var/log').expanduser()
DATA_DIR.mkdir(exist_ok=True, parents=True)
logging.basicConfig(filename=DATA_DIR/'fan_control.log', filemode='a', level=logging.INFO)

PIN = 12
CHECK_TIMEOUT = 3
CONFIG_FILE = Path(os.getenv('FAN_CONTROL_CONFIG_FILE') or '/opt/fan_control.json')


class FanControl:
    def __init__(self):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(PIN, GPIO.OUT, initial=0)
        self.ON = False

    def __call__(self):
        logging.info('Start Monitoring...')
        while True:
            try:
                conf = self.read_config()
                tmp = self.get_temp() 
                if not self.ON and tmp >= conf['temp_on']:
                    self.fan_on()
                else:
                    if self.ON and tmp <= conf['temp_off']:
                        self.fan_off()
            except Exception as e:
                logging.exception('Main cycle error')
            time.sleep(CHECK_TIMEOUT)

    def get_temp(self):
        cmd = 'vcgencmd measure_temp'
        output = os.popen(cmd).read().strip()
        temp = re.search(r"[\d.]+", output).group(0)
        return float(temp)

    def fan_on(self):
        logging.info('FAN ON')
        GPIO.output(PIN, 1)
        self.ON = True

    def fan_off(self):
        logging.info('FAN OFF')
        GPIO.output(PIN, 0)
        self.ON = False

    def read_config(self):
        data = dict(
            temp_on=70,
            temp_off=55
        )
        if CONFIG_FILE.exists():
            try:
                with CONFIG_FILE.open() as f:
                    data = json.load(f)
            except Exception:
                logging.exception('Read config file error')
        return data

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        GPIO.cleanup(PIN)


if __name__ == '__main__':
    ctl = FanControl()
    try:
        ctl()
    except KeyboardInterrupt:
        sys.exit()
