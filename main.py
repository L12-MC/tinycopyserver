import subprocess
import argparse
from api import main
from lib.logger import ANSI

verbose = False
VERSION = "alpha-0.1"
RAINBOWTEXT = f"{ANSI.RED}T{ANSI.YELLOW}i{ANSI.GREEN}n{ANSI.BLUE}y{ANSI.MAGENTA}C{ANSI.CYAN}o{ANSI.RED}p{ANSI.YELLOW}y{ANSI.GREEN}S{ANSI.BLUE}e{ANSI.MAGENTA}r{ANSI.CYAN}v{ANSI.RED}e{ANSI.YELLOW}r{ANSI.RESET}"
COL_L12 = f"{ANSI.BOLD}{ANSI.MAGENTA}L{ANSI.BLUE}1{ANSI.CYAN}2{ANSI.RESET}"
def splash():
    vcol = ANSI.RESET
    if VERSION.startswith("alpha"):
        vcol = ANSI.RED
    elif VERSION.startswith("b"):
        vcol = ANSI.YELLOW
    elif VERSION.startswith("rc"):
        vcol = ANSI.MAGENTA
    MESSAGE = f"""┌───────────────────────────────────────
│
│   {RAINBOWTEXT} {vcol}{VERSION}{ANSI.RESET} {ANSI.DIM}{"(verbose)" if verbose else ''}{ANSI.RESET}
│
│   Server URL: {ANSI.UNDERLINE}{ANSI.rgb(0,0,238)}http://{ip}:{port}{ANSI.RESET}
│
│   Written and {ANSI.DIM}(hopefully){ANSI.RESET} maintained by {COL_L12}
│"""
    print(MESSAGE)

ip = "localhost"
port = 8000

parser = argparse.ArgumentParser()
parser.add_argument("--ip", help="Target IP Address (set to 0.0.0.0 to listen on all interfaces)")
parser.add_argument("--port", help="Target Port (default: 8000)")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
args = parser.parse_args()
if args.ip:
    if args.ip == "0.0.0.0":
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    else:
        ip = args.ip
if args.port:
    port = int(args.port)
if args.verbose:
    verbose = True

splash()

if ip == "localhost":
    main(port=port, verbose=verbose)
else:
    main(host=ip, port=port, verbose=verbose)