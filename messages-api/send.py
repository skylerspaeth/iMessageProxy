#!/usr/bin/env python3

import argparse
from subprocess import Popen, PIPE

parser = argparse.ArgumentParser(
    prog='./send.py',
    description='Sends iMessages to an argument-specified contact'
)
parser.add_argument('-c', '--contact')
parser.add_argument('-m', '--message')
args = parser.parse_args()

def run_applescript(script, args=[]):
    p = Popen(['osascript', '-'] + args, stdin=PIPE, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    stdout, stderr = p.communicate(script)
    return stdout

def send_message():
    print(f"Sending message {args.message} to: {args.contact}...")
    run_applescript("""
        on run {contact, message}
            tell application "Messages"
                set targetBuddy to contact
                set targetService to id of 1st account whose service type = iMessage
                set textMessage to message
                set theBuddy to participant targetBuddy of account id targetService
                send textMessage to theBuddy
            end tell
        end run
    """, [
        args.contact, args.message
    ])

if __name__ == "__main__":
    send_message()
