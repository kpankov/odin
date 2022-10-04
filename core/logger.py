
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Logger:
    DBG_NONE = 0
    DBG_ALL = 10

    def __init__(self, debug_level=DBG_NONE):
        self._silent_mode = False
        self._debug_level = debug_level

    def set_silent_mode(self, on_off):
        self._silent_mode = on_off

    @staticmethod
    def fatal(str_fatal):
        print(bcolors.BOLD + bcolors.FAIL + "FATAL:" + bcolors.ENDC, bcolors.FAIL + str_fatal + bcolors.ENDC)
        exit(1)

    @staticmethod
    def error(str_error):
        print(bcolors.BOLD + bcolors.FAIL + "ERROR:" + bcolors.ENDC, bcolors.FAIL + str_error + bcolors.ENDC)

    @staticmethod
    def warning(str_warning):
        print(bcolors.BOLD + bcolors.WARNING + "WARNING:", str_warning, bcolors.ENDC)

    @staticmethod
    def info(str_info):
        print("INFO: " + str_info)

    def debug(self, str_debug):
        if self._debug_level > 0:
            print(bcolors.OKBLUE + "DEBUG: " + str_debug + bcolors.ENDC)

    @staticmethod
    def red(string):
        print(bcolors.FAIL + string + bcolors.ENDC)

    @staticmethod
    def boldred(string):
        print(bcolors.BOLD + bcolors.FAIL + string + bcolors.ENDC)

    @staticmethod
    def cmd(string):
        print(bcolors.BOLD + bcolors.OKBLUE + string + bcolors.ENDC)

    @staticmethod
    def green(string):
        print(bcolors.BOLD + bcolors.OKGREEN + string + bcolors.ENDC)

    def bypass(self, string, **options): # TODO: make sure that it's right way
        if not self._silent_mode:
            print(string, *options)
