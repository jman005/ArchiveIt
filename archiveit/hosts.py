import requests
from requests.exceptions import RequestException
import ftplib

from io import BytesIO
import time
import logging
logger = logging.getLogger("archiveit.host")

class HostException(Exception):
    pass


class Host():
    def __init__(self):
        pass

    def upload(self, file: bytes, name=None):
        '''
        Uploads data to the hosting provider, returns a URL.
        :param file: The data to send, as bytes.
        :param name: The name of the file (optional)
        :return: A string, the URL.
        '''
        raise NotImplementedError()

class ZeroXZero(Host):
    def __init__(self):
        super(ZeroXZero).__init__()

    def upload(self, file, name=None):
        data = {'file': file}
        try:
            r = requests.post("https://0x0.st", files=data)
        except RequestException:
            logger.error("Could not connect to host 0x0")
            raise HostException("Could not connect to host")
        if str(r) != "<Response [200]>":
            logger.error("Host 0x0 refused to upload data")
            raise HostException("Host refused request")

        return r.text

class Local_Storage(Host):
    def __init__(self):
        super(Host).__init__()

    def upload(self, file, name=None):
        try:
            with open("config/local.txt") as f:
                data = f.read()
                dirc = data.split("\n")[0]
        except FileNotFoundError:
            logger.critical("The 'local file' host requires a configuration file 'local.txt'."
                            "See readme for more information.")
            raise FileNotFoundError("Host config file not found")

        if name is None:
            name = str(int(time.time()))

        with open(dirc + "/" + name, "wb") as f:
            f.write(file)

        return dirc + "/" + name

class FTP(Host):
    def __init__(self):
        super(Host).__init__()

    def upload(self, file, name=None):
        try:
            with open("config/ftp.txt") as f:
                data = f.read()
                server = data.split("\n")[0]
                username = data.split("\n")[1]
                password = data.split("\n")[2]
                path = data.split("\n")[3]
        except FileNotFoundError:
            logger.critical("The 'FTP' host requires a configuration file 'ftp.txt'."
                            "See readme for more information.")
            raise FileNotFoundError("Host config file not found")
        pass

        session = ftplib.FTP(server)
        session.login(username, password)

        # https://stackoverflow.com/a/32481928
        try:
            session.mkd(path)

        except ftplib.error_perm as e:
            if not e.args[0].startswith('550'):
                logger.error("Host FTP refused to upload data")
                raise HostException("Could not create directory in FTP")
        session.cwd(path)

        data = BytesIO(file)

        if not name:
            name = str(int(time.time()))

        session.storbinary("STOR %s" % name, data)
        session.close()

        return server + "/" + path + "/" + name

hosts = {"0x0": ZeroXZero, "local": Local_Storage, "ftp": FTP}
