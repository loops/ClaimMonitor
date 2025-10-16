#!/usr/bin/env python3

from pydbus import SystemBus
from gi.repository import GLib
import configparser
import shlex
import subprocess
import time
from types import SimpleNamespace

class ClaimMonitor:
    """
<node>
    <interface name='com.eztux.ClaimMonitor'>
        <method name='Switch'>
            <arg type='s' name='input' direction='in'/>
        </method>
    </interface>
</node>
    """
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('/etc/ClaimMonitor.ini')

        self.last_call_time_ns = None
        lockout_seconds = config.getint('monitor', 'lockout_seconds', fallback=2)
        self.lockout_ns = lockout_seconds * 1_000_000_000  # Convert to nanoseconds
        self.debug = config.getboolean('monitor', 'debug')

        self.inputs = {}
        for input in config.sections():
            if input != "monitor":
                data = SimpleNamespace()
                data.switch = shlex.split(config.get(input, 'switch'))
                data.probe = shlex.split(config.get(input, 'probe'))
                data.match = config.get(input, 'match').strip()
                data.error = config.get(input, 'error').strip()
                self.inputs[input] = data

    def should_process(self):
        current_time_ns = time.monotonic_ns()

        if self.last_call_time_ns is not None:
            elapsed_ns = current_time_ns - self.last_call_time_ns
            if elapsed_ns < self.lockout_ns:
                return False  # Too soon, skip processing

        return True

    def Msg(self, out):
        if self.debug:
            current_sec = time.monotonic_ns() / 1000000000
            print(f"{current_sec}: {out}", flush=True)

    def Switch(self, input):
        if not self.should_process():
            self.Msg(f"Ignoring invocation [{input}]")
            return
        self.Msg(f"--Switch invoked [{input}]--")
        if input not in self.inputs:
            self.Msg(f"No such input specified in config!")
            return
        data = self.inputs[input]
        run = subprocess.run(data.probe, capture_output=True, text=True)
        current = run.stdout.strip()
        if current == data.error:
            self.Msg(f"Monitor returned [{current}] error.")
        elif current != data.match:
            self.Msg(f"Monitor returned [{current}] which doesn't match.")
            subprocess.run(data.switch)
            self.last_call_time_ns = time.monotonic_ns()
        else:
            self.Msg(f"Monitor is already on current input.")

bus = SystemBus()
bus.publish("com.eztux.ClaimMonitor", ClaimMonitor())
GLib.MainLoop().run()
