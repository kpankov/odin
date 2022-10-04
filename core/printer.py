
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


def fatal(str_fatal):
    print(bcolors.BOLD + bcolors.FAIL + "FATAL:" + bcolors.ENDC, bcolors.FAIL + str_fatal + bcolors.ENDC)
    exit(1)


def error(str_error):
    print(bcolors.BOLD + bcolors.FAIL + "ERROR:" + bcolors.ENDC, bcolors.FAIL + str_error + bcolors.ENDC)


def warning(str_warning):
    print(bcolors.BOLD + bcolors.WARNING + "WARNING:", str_warning, bcolors.ENDC)


def info(str_info):
    print("INFO: " + str_info)


def debug(self, str_debug):
    print(bcolors.OKBLUE + "DEBUG: " + str_debug + bcolors.ENDC)


def red(string):
    print(bcolors.FAIL + string + bcolors.ENDC)


def boldred(string):
    print(bcolors.BOLD + bcolors.FAIL + string + bcolors.ENDC)


def cmd(string):
    print(bcolors.BOLD + bcolors.OKBLUE + string + bcolors.ENDC)


def green(string):
    print(bcolors.BOLD + bcolors.OKGREEN + string + bcolors.ENDC)
