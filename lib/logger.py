import keyboard
import sys

class ANSI:
    # Reset
    RESET = "\033[0m"

    # Text Colors
    BLACK   = "\033[30m"
    RED     = "\033[31m"
    GREEN   = "\033[32m"
    YELLOW  = "\033[33m"
    BLUE    = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN    = "\033[36m"
    WHITE   = "\033[37m"

    # Bright Text Colors
    BRIGHT_BLACK   = "\033[90m"
    BRIGHT_RED     = "\033[91m"
    BRIGHT_GREEN   = "\033[92m"
    BRIGHT_YELLOW  = "\033[93m"
    BRIGHT_BLUE    = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN    = "\033[96m"
    BRIGHT_WHITE   = "\033[97m"

    # Background Colors
    BG_BLACK   = "\033[40m"
    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"
    BG_WHITE   = "\033[47m"

    # Bright Background Colors
    BG_BRIGHT_BLACK   = "\033[100m"
    BG_BRIGHT_RED     = "\033[101m"
    BG_BRIGHT_GREEN   = "\033[102m"
    BG_BRIGHT_YELLOW  = "\033[103m"
    BG_BRIGHT_BLUE    = "\033[104m"
    BG_BRIGHT_MAGENTA = "\033[105m"
    BG_BRIGHT_CYAN    = "\033[106m"
    BG_BRIGHT_WHITE   = "\033[107m"

    # Formatting
    BOLD      = "\033[1m"
    DIM       = "\033[2m"
    ITALIC    = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK     = "\033[5m"
    BLINK2    = "\033[6m"  # Rapid blink (rarely supported)
    REVERSE   = "\033[7m"  # Swap fg/bg colors
    HIDDEN    = "\033[8m"  # Invisible text
    STRIKE    = "\033[9m"

    # Reset Individual Formatting
    RESET_BOLD      = "\033[22m"
    RESET_DIM       = "\033[22m"
    RESET_ITALIC    = "\033[23m"
    RESET_UNDERLINE = "\033[24m"
    RESET_BLINK     = "\033[25m"
    RESET_REVERSE   = "\033[27m"
    RESET_HIDDEN    = "\033[28m"
    RESET_STRIKE    = "\033[29m"
    RESET_COLOR     = "\033[39m"  # Reset fg to default
    RESET_BG        = "\033[49m"  # Reset bg to default

    # Cursor Movement
    CURSOR_UP    = "\033[A"
    CURSOR_DOWN  = "\033[B"
    CURSOR_RIGHT = "\033[C"
    CURSOR_LEFT  = "\033[D"

    # Erase
    ERASE_LINE       = "\033[2K"
    ERASE_TO_END     = "\033[0K"
    ERASE_TO_START   = "\033[1K"
    ERASE_SCREEN     = "\033[2J"
    CLEAR_LINE     = "\033[2K"
    SAVE_CURSOR    = "\033[s"   # save absolute cursor position
    RESTORE_CURSOR = "\033[u"   # jump back to saved position
    HIDE_CURSOR    = "\033[?25l"
    SHOW_CURSOR    = "\033[?25h"

    # 256-color and RGB helpers
    @staticmethod
    def color256(n: int) -> str:
        """Foreground 256-color. n = 0–255"""
        return f"\033[38;5;{n}m"

    @staticmethod
    def bg_color256(n: int) -> str:
        """Background 256-color. n = 0–255"""
        return f"\033[48;5;{n}m"

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """Foreground true color (24-bit)"""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        """Background true color (24-bit)"""
        return f"\033[48;2;{r};{g};{b}m"

def _write(*parts: str):
    sys.stdout.write("".join(parts))
    sys.stdout.flush()
 
 
def _print_block(lines: list[str]):
    """Print a block of lines and keep the cursor at the end."""
    for line in lines:
        sys.stdout.write(f"\r{ANSI.CLEAR_LINE}{line}\n")
    sys.stdout.flush()

def _redraw_block(lines: list[str]):
    """Move cursor up, then overwrite the block."""
    # Move cursor up by the number of lines in the block
    # \033[{N}A moves the cursor up N lines
    _write(f"\033[{len(lines)}A") 
    for line in lines:
        _write(f"\r{ANSI.CLEAR_LINE}{line}\n")
    sys.stdout.flush()

class log:
    def info(p: str):
        print(f"{ANSI.BRIGHT_GREEN}INFO{ANSI.RESET}:     {p}{ANSI.RESET}")
    def error(p: str, c: int = None):
        if not c:
            print(f"{ANSI.RED}ERROR{ANSI.RESET}:    {p}{ANSI.RESET}")
        else:
            print(f"{ANSI.RED}ERROR{ANSI.RESET}:    {p} {ANSI.DIM}CODE:     {ANSI.RED}{c}{ANSI.RESET}")
    def success(p: str):
        print(f"{ANSI.BRIGHT_GREEN}{ANSI.BOLD}SUCCESS{ANSI.RESET}:  {p}{ANSI.RESET}")

class inp:
    def text(p: str, default: str = ""):
        o = list(default) # Use a list for easier insertion/deletion
        idx = len(o)      # Current cursor position
        _write(ANSI.HIDE_CURSOR)
        def render():
            # Use a local copy or temporary logic so we don't mess up the actual string 'o'
            # If index is at the end, we highlight a space, otherwise we highlight the char at idx
            char_at_cursor = o[idx] if idx < len(o) else " "
            
            # Text before the cursor
            before = "".join(o[:idx])
            # The highlighted character
            cursor = f"{ANSI.BG_WHITE}{ANSI.BLACK}{char_at_cursor}{ANSI.RESET}"
            # Text after the cursor
            after = "".join(o[idx + 1:]) if idx < len(o) else ""
            
            print(f"│   {p}{ANSI.DIM} ❱ {ANSI.RESET}{before}{cursor}{after}\033[K", end="\r")


        render()

        while True:
            event = keyboard.read_event(suppress=True)
            if event.event_type != keyboard.KEY_DOWN:
                continue

            if event.name == "enter":
                # Remove visual cursor for the final print
                print(f"│   {p}{ANSI.DIM} ❱ {ANSI.RESET}{''.join(o)}\033[K", end="\n")
                break
            
            elif event.name == "left":
                idx = max(0, idx - 1)
                
            elif event.name == "right":
                idx = min(len(o), idx + 1)

            elif event.name == "backspace":
                if keyboard.is_pressed("ctrl"):
                    o = o[idx:] # Clears everything before cursor
                    idx = 0
                elif idx > 0:
                    o.pop(idx - 1)
                    idx -= 1
            
            elif event.name == "delete":
                if idx < len(o):
                    o.pop(idx)

            elif event.name in ["ctrl", "shift", "esc", "caps lock", "up", "down"]:
                continue

            elif event.name == "space":
                o.insert(idx, " ")
                idx += 1
                
            elif event.name == "tab":
                for _ in range(4):
                    o.insert(idx, " ")
                    idx += 1
            
            else:
                # Avoid capturing long names like 'f1', 'menu', etc.
                if len(event.name) == 1:
                    o.insert(idx, event.name)
                    idx += 1
            
            render()

        print("│")
        _write(ANSI.SHOW_CURSOR)
        return "".join(o)

    def integer(prompt: str, default: int = 0, step: int = 1) -> int:
        val = default
    
        def _line() -> str:
            color = ANSI.CYAN if val > 0 else ANSI.RED if val < 0 else ANSI.RESET
            return (
                f"│   {prompt} "
                f"{ANSI.DIM}⬆︎⬇︎{ANSI.RESET}  "
                f"{color}{ANSI.BOLD}{val}{ANSI.RESET}"
            )
    
        _write(ANSI.HIDE_CURSOR)
        _print_block([_line()])
    
        try:
            while True:
                event = keyboard.read_event(suppress=True)
                if event.event_type != keyboard.KEY_DOWN:
                    continue
    
                if event.name == "enter":
                    break
                elif event.name == "up":
                    val += step
                elif event.name == "down":
                    val -= step
                else:
                    continue
    
                _redraw_block([_line()])
        finally:
            _write(ANSI.SHOW_CURSOR)
        print("│")
        return val
        val = default
    
        def _line() -> str:
            color = ANSI.CYAN if val > 0 else ANSI.RED if val < 0 else ANSI.RESET
            return (
                f"│   {prompt} "
                f"{ANSI.DIM}⬆︎⬇︎{ANSI.RESET}  "
                f"{color}{ANSI.BOLD}{val}{ANSI.RESET}"
            )
    
        lines = [_line()]
        _write(lines[0] + "\n")
    
        while True:
            event = keyboard.read_event(suppress=True)
            if event.event_type != keyboard.KEY_DOWN:
                continue
    
            if event.name == "enter":
                break
            elif event.name == "up":
                val += step
            elif event.name == "down":
                val -= step
            else:
                continue
    
            new_lines = [_line()]
            _redraw_lines(lines, new_lines)
            lines = new_lines
    
        return val
    def select(prompt: str, options: list[str], default: int = 0) -> str:
        idx = default
        n   = len(options)
    
        def _lines() -> list[str]:
            out = [f"│   {prompt}"]
            for i, opt in enumerate(options):
                if i == idx:
                    out.append(
                        f"│     {ANSI.BOLD}{ANSI.CYAN}▶  {opt}{ANSI.RESET}"
                    )
                else:
                    out.append(
                        f"│     {ANSI.DIM}   {opt}{ANSI.RESET}"
                    )
            return out
    
        _write(ANSI.HIDE_CURSOR)
        _print_block(_lines())
    
        try:
            while True:
                event = keyboard.read_event(suppress=True)
                if event.event_type != keyboard.KEY_DOWN:
                    continue
    
                if event.name == "enter":
                    break
                elif event.name == "up":
                    idx = (idx - 1) % n
                elif event.name == "down":
                    idx = (idx + 1) % n
                else:
                    continue
    
                _redraw_block(_lines())
        finally:
            _write(ANSI.SHOW_CURSOR)
        print("│")
        return options[idx]
    def color(prompt: str, default: tuple[int, int, int] = (128, 128, 128)) -> tuple[int, int, int]:
        r, g, b   = default
        channel   = 0           # 0 = R, 1 = G, 2 = B
        BAR_WIDTH = 20
        LABELS    = ["R", "G", "B"]
        COLORS    = [ANSI.RED, ANSI.GREEN, ANSI.BLUE]
    
        def _clamp(v: int) -> int:
            return max(0, min(255, v))
    
        def _bar(val: int) -> str:
            filled = round(val * BAR_WIDTH / 255)
            return "█" * filled + "░" * (BAR_WIDTH - filled)
    
        def _swatch() -> str:
            # True-color background block
            return f"\033[48;2;{r};{g};{b}m   \033[0m"
    
        def _lines() -> list[str]:
            vals = [r, g, b]
            out  = [f"│   {prompt}  {_swatch()}  {ANSI.DIM}⬅︎ ⬆︎⬇︎ ➡︎{ANSI.RESET}"]
            for i, (label, col, val) in enumerate(zip(LABELS, COLORS, vals)):
                active  = i == channel
                marker  = f"{ANSI.BOLD}◀ ▶{ANSI.RESET}" if active else "    "
                hi      = ANSI.BOLD if active else ANSI.DIM
                out.append(
                    f"│     {hi}{col}{label}{ANSI.RESET}  "
                    f"{col if active else ANSI.DIM}{_bar(val)}{ANSI.RESET}  "
                    f"{hi}{val:3d}{ANSI.RESET}  {marker}"
                )
            return out
    
        _write(ANSI.HIDE_CURSOR)
        _print_block(_lines())
    
        try:
            while True:
                event = keyboard.read_event(suppress=True)
                if event.event_type != keyboard.KEY_DOWN:
                    continue
    
                name = event.name
                if name == "enter":
                    break
                elif name == "up":
                    channel = (channel - 1) % 3
                elif name == "down":
                    channel = (channel + 1) % 3
                elif name == "right":
                    if channel == 0: r = _clamp(r + 1)
                    elif channel == 1: g = _clamp(g + 1)
                    else:              b = _clamp(b + 1)
                elif name == "left":
                    if channel == 0: r = _clamp(r - 1)
                    elif channel == 1: g = _clamp(g - 1)
                    else:              b = _clamp(b - 1)
                else:
                    continue
    
                _redraw_block(_lines())
        finally:
            _write(ANSI.SHOW_CURSOR)
        print("│")
        return (r, g, b)

def setup():
    VERSION = "alpha-0.1"
    RAINBOWTEXT = f"{ANSI.RED}T{ANSI.YELLOW}i{ANSI.GREEN}n{ANSI.BLUE}y{ANSI.MAGENTA}C{ANSI.CYAN}o{ANSI.RED}p{ANSI.YELLOW}y{ANSI.GREEN}S{ANSI.BLUE}e{ANSI.MAGENTA}r{ANSI.CYAN}v{ANSI.RED}e{ANSI.YELLOW}r{ANSI.RESET}"
    COL_L12 = f"{ANSI.BOLD}{ANSI.MAGENTA}L{ANSI.BLUE}1{ANSI.CYAN}2{ANSI.RESET}"
    vcol = ANSI.RESET
    if VERSION.startswith("alpha"):
        vcol = ANSI.RED
    elif VERSION.startswith("b"):
        vcol = ANSI.YELLOW
    elif VERSION.startswith("rc"):
        vcol = ANSI.MAGENTA
    MESSAGE = f"""┌───────────────────────────────────────
│
│   {RAINBOWTEXT} {vcol}{VERSION}{ANSI.RESET}
│
│   Written and {ANSI.DIM}(hopefully){ANSI.RESET} maintained by {COL_L12}
│
│   {ANSI.BOLD}Setup:{ANSI.RESET}
│"""
    print(MESSAGE)
    name = inp.text("Server name", "TinyCopyServer")
    accent = inp.color("Accent color", (44, 118, 244))
    ip = inp.text(f"Hostname {ANSI.DIM}(set to 0.0.0.0 to listen on all interfaces){ANSI.RESET}", "localhost")
    port = inp.integer("Port", 8000)
    print("└───────────────────────────────────────")
    return (name, accent, ip, port)

setup()