import argparse

def args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="0", help="Video Device number e.g. 0, use v4l2-ctl --list-devices")
    parser.add_argument("--fps", type=int, default=30, help="Frame Rate e.g. 30")
    parser.add_argument("--flip", action='store_true', help="Mirror video")
    parser.add_argument("--width", type=int, default = 800)
    parser.add_argument("--height", type=int, default = 600)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fullscreen", help="Fullscreen (Native 800*480)",action="store_true")
    group.add_argument("--waterfall", help="Enable Waterfall (Windowed only)",action="store_true")
    args = parser.parse_args()
    return args
