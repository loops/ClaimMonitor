#!/usr/bin/env python3

from pydbus import SystemBus
from gi.repository import GLib
import configparser
import shlex
import subprocess
import time

class ClaimMonitor:
    """
<node>
    <interface name='com.eztux.ClaimMonitor'>
        <method name='Switch'/>
    </interface>
</node>
    """
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('/etc/ClaimMonitor.ini')
        switch = config.get('monitor', 'switch')
        self.switch = shlex.split(switch)
        probe = config.get('monitor', 'probe')
        self.probe = shlex.split(probe)
        self.match = config.get('monitor', 'match').strip()
        self.debug = config.getboolean('monitor', 'debug')
    def Msg(self, out):
        if self.debug:
            current_sec = time.monotonic_ns() / 1000000000
            print(f"{current_sec}: {out}", flush=True)

    def Switch(self):
        run = subprocess.run(self.probe, capture_output=True, text=True)
        current = run.stdout.strip()
        if current != self.match:
            self.Msg(f"Monitor returned [{current}] which doesn't match.")
            subprocess.run(self.switch)
        else:
            self.Msg(f"Monitor is already on current input.")

bus = SystemBus()
bus.publish("com.eztux.ClaimMonitor", ClaimMonitor())
GLib.MainLoop().run()



