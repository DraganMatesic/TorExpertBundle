"""
+---------------------------------------------------------------------------+
|                                  INFO                                     |
+---------------------------------------------------------------------------+
|TorHandle - class builder, create paths                                    |
|create_tor                                                                 |
|    - creates tor browser if it doesn't exists under same socket           |
|    - option timeout : number of seconds before Error raise                |
|      when Tor can't establish circuit ( if conn is slower)                |
|    - option path: set path where tor.exe is located for Expert Bundle     |
|create_controller - creates new tor controller                             |
|tor_connect - create connection on Tor socket                              |
|new_identity - change Tor identity to get new IP                           |
|shutdown_tor - close Tor safely                                            |
|kill_tor - close Tor if there is no other way to shutdown from some reason |
+---------------------------------------------------------------------------+

"""

from stem.control import Controller
import socks,socket
from time import sleep
from subprocess import Popen,PIPE
import os,psutil,re
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


class TorHandle(object):

    def __init__(self,socks_port,control_port):
        self.CONTROL_PORT = control_port
        self.SOCKS_PORT = socks_port
        self.SocketOriginal = socket.socket

        self.controller = None
        self.torstat = False
        self.p = None

        self.TOR_DIR = r'{0}\TorExpert'.format(ROOT_DIR)
        self.TOR_PATH = r'{0}\TorExpert\Tor\tor.exe'.format(ROOT_DIR)
        self.TORRC_DIR = r'{0}\TorExpert\Config'.format(ROOT_DIR)
        self.TORRC_PATH = r'{0}\TorExpert\Config\torrc{1}.config'.format(ROOT_DIR,socks_port)
        self.DATA_PATH = '{0}\Data\{1}'.format(self.TOR_DIR,self.SOCKS_PORT)
        self.PID_PATH = '{0}\Data\{1}\pid'.format(self.TOR_DIR,self.SOCKS_PORT)

    @staticmethod
    def create_dir(path):
        if not os.path.exists(path):
            os.makedirs(path)

    @staticmethod
    def create_file(path):
        if not os.path.exists(path):
            open(path, 'w').close()

    def make_torrc(self):
        text_file = u'''
        # Where data will be stored?
        DataDirectory {0}\Data\{1}
        
        # Countdown time before exit        
        ShutdownWaitLength 5
        
        # Where to write PID
        PidFile {0}\Data\{1}\pid
        
        # Communication ports
        SocksPort {1}
        ControlPort {2}
        
        # Authentication of Tor
        CookieAuthentication 1
        
        # GeoIP file paths?
        GeoIPFile {0}\Data\Tor\geoip
        GeoIPv6File {0}\Data\Tor\geoip6
        '''.format(self.TOR_DIR,self.SOCKS_PORT,self.CONTROL_PORT).replace('        ',"")

        self.create_dir(self.TORRC_DIR)
        self.create_file(self.TORRC_PATH)
        with open(self.TORRC_PATH,"w") as torrc:
            torrc.write(text_file)

    def create_tor(self,**kvargs):
        start_time = datetime.now()
        timeout = 60
        if kvargs.get('timeout'):
            timeout = kvargs.get('timeout')
        if not self.is_tor_up():

            if kvargs.get('path'):
                self.TOR_PATH = kvargs.get('path')
            self.make_torrc()
            if not os.path.isfile(self.TOR_PATH):
                raise FileNotFoundError ("Declare path of TOR Expert Bundle or place it on path {0}".format(self.TOR_PATH))

            cmd = [self.TOR_PATH,'-f',self.TORRC_PATH]
            self.p = Popen(cmd, stdin = PIPE, stdout = PIPE, stderr = PIPE, shell = False)
            while True:
                event = self.p.stdout.readline()
                print(event)
                diff = datetime.now() - start_time
                if diff.seconds > timeout:
                    self.kill_tor()
                    err = 'Too long to establish tor circuit over {0} seconds'.format(diff.seconds)
                    raise TimeoutError(err)
                if re.search('Bootstrapped 100%',str(event)):
                    break
                if re.search('No route to host', str(event)):
                    self.kill_tor()
                    raise ConnectionError("Check your internet connection")
        else:
            print("Tor is already running")

        self.create_controller()

    def is_tor_up(self):
        if os.path.exists(self.PID_PATH):
            with open(self.PID_PATH) as pidN:
                pid = pidN.read()
                for process in psutil.process_iter():
                    if process.pid == int(pid) and process.name() == 'tor.exe':
                        return True
        return False

    def kill_tor(self):
        with open(self.PID_PATH) as pidN:
            pid = pidN.read()
            for process in psutil.process_iter():
                if process.pid == int(pid) and process.name() == 'tor.exe':
                    process.terminate()
            pidN.close()
        os.remove(self.PID_PATH)

    def create_controller(self):
        self.controller = Controller.from_port(port=self.CONTROL_PORT)

    def tor_connect(self):
        self.controller.connect()
        self.controller.authenticate()
        socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1", self.CONTROL_PORT)
        socket.socket = socks.socksocket

    def clear_socket(self):
        if socket.socket != self.SocketOriginal:
            socket.socket = self.SocketOriginal

    def new_identity(self):
        self.clear_socket()
        controller = self.controller
        new_id_status = controller.is_newnym_available()
        new_id_wait_time = controller.get_newnym_wait()
        print(new_id_status,new_id_wait_time)
        if new_id_status:
            controller.clear_cache()
            controller.signal('NEWNYM')
        else:
            sleep(new_id_wait_time)

    def shutdown_tor(self):
        self.clear_socket()
        controller = self.controller
        controller.signal('SHUTDOWN')