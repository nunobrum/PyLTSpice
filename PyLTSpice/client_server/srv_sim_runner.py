#!/usr/bin/env python
# coding=utf-8

# -------------------------------------------------------------------------------
#    ____        _   _____ ____        _
#   |  _ \ _   _| | |_   _/ ___| _ __ (_) ___ ___
#   | |_) | | | | |   | | \___ \| '_ \| |/ __/ _ \
#   |  __/| |_| | |___| |  ___) | |_) | | (_|  __/
#   |_|    \__, |_____|_| |____/| .__/|_|\___\___|
#          |___/                |_|
#
# Name:        srv_sim_runner.py
# Purpose:     Manager of the simulation sim_tasks on the server side
#
# Author:      Nuno Brum (nuno.brum@gmail.com)
#
# Created:     23-02-2023
# Licence:     refer to the LICENSE file
# -------------------------------------------------------------------------------
import threading
import time
from typing import Any, Callable, Union
from pathlib import Path
import zipfile

from PyLTSpice.sim.sim_runner import SimRunner
from PyLTSpice.sim.spice_editor import SpiceEditor


def zip_files(raw_filename: Path, log_filename:Path):
    zip_filename = raw_filename.with_suffix('.zip')
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(raw_filename)
        zip_file.write(log_filename)
    return zip_filename


class ServerSimRunner(threading.Thread):
    """This class maintains updated status of the SimRunner.
    It was decided not to make SimRunner a super class and rather make it manipulate directly the structures of
    SimRunner. The rationale for this, was to avoid confusions between the run() on the Thread class and the
    run on the SimRunner class.
    Making a class derive from two different classes needs to be handled carefully.

    In consequence of the rationale above, many of the functions that were handled by the SimRunner are overriden
    by this class.
    """

    def __init__(self, parallel_sims: int = 4, timeout=None, verbose=True, output_folder: str = None, simulator=None):
        super().__init__(name="SimManager")
        self.runner = SimRunner(parallel_sims, timeout, verbose, output_folder, simulator)
        self.completed_tasks = []
        self._stop = False

    def run(self) -> None:
        """This function makes a direct manipulation of the structures of SimRunner. This option is """
        while True:
            i = 0
            while i < len(self.runner.sim_tasks):
                task = self.runner.sim_tasks[i]
                if task.is_alive():
                    i += 1
                else:
                    zip_filename = task.callback_return
                    self.completed_tasks.append({
                        'runno': task.runno,
                        'retcode': task.retcode,
                        'raw': task.raw_file,
                        'log': task.log_file,
                        'zipfile': zip_filename,
                        'start': task.start_time,
                        'stop': task.stop_time,
                    })
                    print(task, "is finished")
                    del self.runner.sim_tasks[i]
                    print(self.completed_tasks[-1])
                    print(len(self.completed_tasks))

            time.sleep(0.2)
            if self._stop is True:
                break
        self.runner.wait_completion()
        self.runner.file_cleanup()

    def add_simulation(self, netlist: Union[str, Path, SpiceEditor], *, timeout: float = 600) -> int:
        """"""
        print("starting ", netlist)
        task = self.runner.run(netlist, wait_resource=True, timeout=timeout, callback=zip_files)
        if task is None:
            print("Failed to start task ", netlist)
            return -1
        else:
            print("Started task ", netlist, " with job_id", task.runno)
            return task.runno

    def _erase_files_and_info(self, pos):
        task = self.completed_tasks[pos]
        for filename in ('log', 'raw', 'zipfile'):
            f = task[filename]
            if f.exists():
                f.unlink()
        del self.completed_tasks[pos]

    def erase_files_of_runno(self, runno):
        """Will delete all files related with a completed task. Will also delete information on the completed_tasks
        attribute."""
        for i, task_info in enumerate(self.completed_tasks):
            if task_info['runno'] == runno:
                self._erase_files_and_info(i)
                break

    def cleanup_completed(self):
        while len(self.completed_tasks):
            self._erase_files_and_info(0)

    def stop(self):
        print("stopping...ServerSimRunner")
        self._stop = True

    def running(self):
        return self._stop is False