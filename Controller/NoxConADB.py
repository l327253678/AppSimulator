import sys
import os
import time
import re
import random

sys.path.append(os.getcwd())

from Controller.Common import *


class NoxConADB(object):
    '''
    可以使用Timer进行时分同步
    '''
    REBOOT_RECOVERY = 1
    REBOOT_BOOTLOADER = 2

    DEFAULT_TCP_HOST = "localhost"
    DEFAULT_TCP_PORT = 62001  # 5555

    def __init__(self, task_info, mode):
        '''
        mode:
          multi(例：NoxConsole.exe adb -name:nox-1 -command:"version"): > Nox 6.0.0:
          single(例：nox_adb.exe version): VMware + Nox 3.8.1 or  > Nox 6.0.0
        '''
        self.mode = mode
        self._DEBUG = False
        self._stdout = None
        self._stderr = None
        self._devices = None
        self.__target = None
        self._org_path = os.getcwd()
        self._work_path = WORK_PATH
        self._console_binary = CONSOLE_BINARY_PATH
        self._adb_binary = ADB_BINARY_PATH
        self._app_name = task_info['app_name']
        self._redis_key = task_info['redis_key']
        self._docker_name = str(task_info['taskId']) if str(task_info['taskId']).startswith('nox') \
            else 'nox-' + str(task_info['taskId'])
        self._timer_no = task_info['timer_no']
        self._taskId = task_info['taskId']
        self._timer_flg = False

    def _log(self, prefix, msg):
        common_log(self._DEBUG, self._taskId, 'NoxConADB ' + self._docker_name, prefix, msg)

    def _clean(self):
        self._stdout = None
        self._stderr = None

    def _get_phone_number(self):
        num = '186'
        for i in range(8):
            num += str(random.randrange(0, 9))
        return num

    def _luhn_residue(self, digits):
        return sum(sum(divmod(int(d) * (1 + i % 2), 10)) for i, d in enumerate(digits[::-1])) % 10

    def _get_imei(self, N):
        part = ''.join(str(random.randrange(0, 9)) for _ in range(N - 1))
        res = self._luhn_residue('{}{}'.format(part, 0))
        return '{}{}'.format(part, -res % 10)

    def get_docker_name(self):
        ret = self.adb_shell("getprop persist.nox.emulator_name")
        if ret:
            self._docker_name = ret.replace('\r\r\n', '')

        return self._docker_name

    def get_new_phone(self):
        imei = self._get_imei(15)
        phone_number = self._get_phone_number()
        self.adb_shell("setprop persist.nox.modem.imei " + imei)
        # "adb shell setprop persist.nox.modem.imsi 460000000000000"
        self.adb_shell("setprop persist.nox.modem.phonumber " + phone_number)
        # "adb shell setprop persist.nox.modem.serial 89860000000000000000"
        time.sleep(1)
        return True

    def get_android_version(self):
        self._clean()
        time.sleep(20)  # 6.2.37
        self.adb_shell("getprop ro.build.version.release")
        return self._stdout

    def clear_cache(self):
        packages = {
            'miaopai': 'com.yixia.videoeditor',
            'dianping': 'com.dianping.v1',
            'douyin': 'com.ss.android.ugc.aweme',
            'huoshan': 'com.ss.android.ugc.live'
        }
        if self._app_name not in packages.keys():
            return False
        else:
            self.adb_shell("pm clear " + packages[self._app_name])
        return True

    def set_gps(self, latitude, longitude):
        self.adb_shell("setprop persist.nox.gps.latitude {}".format(latitude))
        self.adb_shell("setprop persist.nox.gps.longitude {}".format(longitude))
        return True

    def adb_start_web(self, url):
        # adb shell am start -a android.intent.action.VIEW -d http://testerhome.com
        self.adb_shell("am start -a android.intent.action.VIEW -d " + url)
        return True

    def get_stdout(self):
        return self._stdout

    def get_stderr(self):
        return self._stderr

    def get_new_error(self):
        """
        Was failed the last command?
        """
        if self._stdout is None and self._stderr is not None:
            return True
        return False

    def _make_command(self, cmd):
        # NoxConsole.exe adb -name:nox-22 -command:"version"
        if self.mode == MODE_MULTI:  # multi: Nox >6.1.0
            cmd_str = self._console_binary + ' adb -name:' + self._docker_name + ' -command:"' + cmd + '"'
        else:  # single: Nox 3.8.1
            cmd_str = self._adb_binary + ' ' + cmd
        return cmd_str

    def _set_save_redis_key(self):
        f = open(self._work_path + '\\cmd\\save_redis_key.conf', 'w')
        self._log('<<info>> save_redis_key:', self._redis_key)  # datetime.now().strftime('%H:%M:%S %f')
        f.write(str(self._redis_key))
        f.close()

    def adb_cmd_before(self, cmdline):
        # overwrite NoxConADB adb_cmd_before
        self._set_save_redis_key()
        if self.mode == MODE_MULTI and self._timer_flg and self._timer_no >= 0:
            cycle = 3 * len(TIMER)
            now = datetime.now().second % cycle
            if now > TIMER[self._timer_no]:
                wait_time = cycle + TIMER[self._timer_no] - now
            else:
                wait_time = TIMER[self._timer_no] - now

            tobe = datetime.fromtimestamp(int(datetime.now().timestamp()) + wait_time).strftime("%m-%d %H:%M:%S")
            self._log('<<info>> timer_no:{}'.format(self._timer_no),
                      'will run at {} (sleep {} s)'.format(tobe, wait_time))
            time.sleep(wait_time)
            self._log('<<info>>[adb_cmd] {}\n'.format(datetime.now().strftime('%H:%M:%S %f')), cmdline)
        else:
            self._log('<<info>>[adb_cmd]\n\t', cmdline)

    def adb_cmd(self, cmd):
        self._clean()
        try:
            os.chdir(NOX_BIN_PATH)  # 防止 BignoxVMS 写入.py本地
            cmdline = self._make_command(cmd)
            self.adb_cmd_before(cmdline)
            process = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # process.wait()
            (stdout, stderr) = process.communicate()
            # print('stdout:', stdout.decode('gbk'))
            # print('stderr:', stderr.decode('gbk'))
            self._stdout = stdout.decode('utf8').replace('\r', '').replace('\n', '')
            self._stderr = stderr.decode('utf8').replace('\r', '').replace('\n', '')
        except Exception as e:
            self._log('<<error>> adb_cmd Exception:\n', e)
        finally:
            os.chdir(self._org_path)  # 恢复路径
            # if self._stdout.find('device not exist!') != -1 or \
            #         self._stdout.find('error: no devices/emulators found') != -1:
            #     print(self._stdout)
            #     raise Exception("offline")

        return

    def adb_shell(self, cmd):
        self._clean()
        self.adb_cmd('shell ' + cmd)
        return self._stdout

    def get_adb_version(self):
        ret = None
        self.adb_cmd("version")
        try:
            if self._stdout.find('device not exist') == -1:
                ret = self._stdout
                self._log('<<info>> get_adb_version ok:\n', ret)
        except Exception as e:
            self._log('<<error>> get_adb_version Exception:\n', e)
        return ret

    def wait_for_device(self, timeout=30):
        """
        Block until device is online
        adb wait-for-device
        """
        ver = None
        while timeout > 0:
            ver = self.get_android_version()
            if ver and ver.startswith('4.4.2'):
                self._log('<<info>> wait_for_device', 'ok')
                break
            else:
                self._log('<<info>> wait_for_device', 'timeout: {}s'.format(timeout))
                timeout -= 5
                time.sleep(5)

        return True if ver else False

    def check_path(self):
        if self.get_adb_version() is None:
            return False
        return True

    def start_server(self):
        self._clean()
        self.adb_cmd('start-server')
        return self._stdout

    def kill_server(self):
        """
        Kills ADB server
        adb kill-server
        """
        self._clean()
        self.adb_cmd('kill-server')

    def restart_server(self):
        """
        Restarts ADB server
        """
        self.kill_server()
        return self.start_server()

    def restore_file(self, file_name):
        """
        Restore device contents from the <file> backup archive
        adb restore <file>
        """
        self._clean()
        self.adb_cmd('restore %s' % file_name)
        return self._stdout

    def get_adb_help(self):
        self._clean()
        self.adb_cmd('help')
        return self._stdout

    def get_target_device(self):
        """
        Returns the selected device to work with
        """
        return self.__target

    def get_state(self):
        """
        adb get-state
        设备状态:
            device：设备正常连接
            offline：连接出现异常，设备无响应
            unknown：没有连接设备
        """
        self._clean()
        self.adb_cmd('get-state')
        return self._stdout

    def get_serialno(self):
        """
        Get serialno from target device  port like 62001
        adb get-serialno
        """
        self._clean()
        self.adb_cmd('get-serialno')
        return self._stdout

    def reboot_device(self, mode):
        """
        Reboot the target device
        adb reboot recovery/bootloader
        """
        self._clean()
        if not mode in (self.REBOOT_RECOVERY, self.REBOOT_BOOTLOADER):
            self._stderr = "mode must be REBOOT_RECOVERY/REBOOT_BOOTLOADER"
            return self._stdout

        self.adb_cmd("reboot %s" % "recovery" if mode == self.REBOOT_RECOVERY else "bootloader")
        return self._stdout

    def set_adb_root(self, mode):
        """
        restarts the adbd daemon with root permissions
        adb root
        """
        self._clean()
        self.adb_cmd('root')
        return self._stdout

    def set_system_rw(self):
        """
        Mounts /system as rw
        adb remount
        """
        self._clean()
        self.adb_cmd("remount")
        return self._stdout

    def get_remote_file(self, remote, local):
        """
        Pulls a remote file
        adb pull remote local
        """
        self._clean()
        self.adb_cmd('pull \"%s\" \"%s\"' % (remote, local))
        if "bytes in" in self._stderr:
            self._stdout = self._stderr
            self._stderr = None
        return self._stdout

    def push_to_device(self, local, remote):
        """
        Push a local file
        adb push local remote
        """
        self._clean()
        self.adb_cmd('push \"%s\" \"%s\"' % (local, remote))
        return self._stdout

    def listen_usb(self):
        """
        Restarts the adbd daemon listening on USB
        adb usb
        """
        self._clean()
        self.adb_cmd("usb")
        return self._stdout

    def listen_tcp(self, port=DEFAULT_TCP_PORT):
        """
        Restarts the adbd daemon listening on the specified port
        adb tcpip <port>
        """
        self._clean()
        self.adb_cmd("tcpip %s" % port)
        return self._stdout

    def get_bugreport(self):
        """
        Return all information from the device that should be included in a bug report
        adb bugreport
        """
        self._clean()
        self.adb_cmd("bugreport")
        return self._stdout

    def get_jdwp(self):
        """
        List PIDs of processes hosting a JDWP transport
        adb jdwp
        """
        self._clean()
        self.adb_cmd("jdwp")
        return self._stdout

    def get_logcat(self, lcfilter=""):
        """
        View device log
        adb logcat <filter>
        """
        self._clean()
        self.adb_cmd("logcat %s" % lcfilter)
        return self._stdout

    def run_emulator(self, cmd=""):
        """
        Run emulator console command
        """
        self._clean()
        self.adb_cmd("emu %s" % cmd)
        return self._stdout

    def connect_remote(self, host=DEFAULT_TCP_HOST, port=DEFAULT_TCP_PORT):
        """
        Connect to a device via TCP/IP
        adb connect host:port
        """
        self._clean()
        self.adb_cmd("connect %s:%s" % (host, port))
        return self._stdout

    def disconnect_remote(self, host=DEFAULT_TCP_HOST, port=DEFAULT_TCP_PORT):
        """
        Disconnect from a TCP/IP device
        adb disconnect host:port
        """
        self._clean()
        self.adb_cmd("disconnect %s:%s" % (host, port))
        return self._stdout

    def ppp_over_usb(self, tty=None, params=""):
        """
        Run PPP over USB
        adb ppp <tty> <params>
        """
        self._clean()
        if tty is None:
            return self._stdout

        cmd = "ppp %s" % tty
        if params != "":
            cmd += " %s" % params

        self.adb_cmd(cmd)
        return self._stdout

    def sync_directory(self, directory=""):
        """
        Copy host->device only if changed (-l means list but don't copy)
        adb sync <dir>
        """
        self._clean()
        self.adb_cmd("sync %s" % directory)
        return self._stdout

    def forward_socket(self, local=None, remote=None):
        """
        Forward socket connections
        adb forward <local> <remote>
        """
        self._clean()
        if local is None or remote is None:
            return self._stdout
        self.adb_cmd("forward %s %s" % (local, remote))
        return self._stdout

    def uninstall(self, package=None, keepdata=False):
        """
        Remove this app package from the device
        adb uninstall [-k] package
        """
        self._clean()
        if package is None:
            return self._stdout
        cmd = "uninstall %s" % (package if keepdata is True else "-k %s" % package)
        self.adb_cmd(cmd)
        return self._stdout

    def install(self, fwdlock=False, reinstall=False, sdcard=False, pkgapp=None):
        """
        Push this package file to the device and install it
        adb install [-l] [-r] [-s] <file>
        -l -> forward-lock the app
        -r -> reinstall the app, keeping its data
        -s -> install on sdcard instead of internal storage
        """
        self._clean()
        if pkgapp is None:
            return self._stdout

        cmd = "install "
        if fwdlock is True:
            cmd += "-l "
        if reinstall is True:
            cmd += "-r "
        if sdcard is True:
            cmd += "-s "

        self.adb_cmd("%s %s" % (cmd, pkgapp))
        return self._stdout

    def find_binary(self, name=None):
        """
        Look for a binary file on the device
        """
        self.adb_shell("which %s" % name)

        if self._stdout is None:  # not found
            self._stderr = "'%s' was not found" % name
        elif self._stdout.strip() == "which: not found":  # which binary not available
            self._stdout = None
            self._stderr = "which binary not found"
        else:
            self._stdout = self._stdout.strip()

        return self._stdout

    def get_screen_size(self):
        """
        获取手机屏幕大小
        """
        size_str = self.adb_shell('wm size')
        m = re.search(r'(\d+)x(\d+)', size_str)
        if m:
            return "{height}x{width}".format(height=m.group(2), width=m.group(1))
        return "1920x1080"


if __name__ == "__main__":
    task = {
        'app_name': 'miaopai',
        'docker_name': 'nox-2',
        'timer_no': 2
    }
    me = NoxConADB(task_info=task, mode=MODE_MULTI)
    me._DEBUG = True

    # print(my.get_adb_version())
    # print(my.get_serialno())
    # print(my.adb_shell('input keyevent 4'))
