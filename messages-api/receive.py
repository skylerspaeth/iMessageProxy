#!/usr/bin/env python3

import sqlite3, time, plistlib, datetime, argparse
from striprtf.striprtf import rtf_to_text
from pathlib import Path

parser = argparse.ArgumentParser(
    prog='./receive.py',
    description='Listens for iMessages from an argument-specified contact'
)
parser.add_argument('-c', '--contact')
args = parser.parse_args()

DB_PATH = f"{Path.home()}/Library/Messages/chat.db"

def get_current_cocoa_timestamp():
    cocoa_epoch = datetime.datetime(2001, 1, 1, 0, 0, 0, 0) # Jan 1, 2001 @ 00:00
    now = datetime.datetime.utcnow()

    # Calculate the difference in seconds and convert to nanoseconds
    nanoseconds_since_cocoa_epoch = int((now - cocoa_epoch).total_seconds() * 1e9)
    return nanoseconds_since_cocoa_epoch

def extract_plain_text(attributed_body):
    try:
        text = attributed_body.split(b"NSString")[1]
        text = text[
            5:
        ]  # stripping some preamble which generally looks like this: b'\x01\x94\x84\x01+'

        # this 129 is b'\x81, python indexes byte strings as ints,
        # this is equivalent to text[0:1] == b'\x81'
        if text[0] == 129:
            length = int.from_bytes(text[1:3], "little")
            text = text[3: length + 3]
        else:
            length = text[0]
            text = text[1: length + 1]
        text = text.decode()
        return text
    except Exception as e:
        print(e)
        sys.exit("ERROR: Can't read a message.")

def fetch_messages(initialTime):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = """
    SELECT message.date, message.text, message.attributedBody, handle.id
    FROM message
    JOIN handle ON message.handle_id = handle.ROWID
    WHERE handle.id = ? AND message.date > ?
    ORDER BY message.date DESC
    """
    cursor.execute(query, (args.contact, initialTime,))
    messages = cursor.fetchall()
    conn.close()
    return messages

def monitor_messages():
    print(f"Listening for messages from: {args.contact}...")
    seen = set()
    initialTime = get_current_cocoa_timestamp()
    previousTimestamp = 0
    while True:
        messages = fetch_messages(initialTime)
        for message in messages:
            if message not in seen:
                # Check if `attributedBody` exists and process it
                if message[0] != previousTimestamp:
                    previousTimestamp = message[0]
                    if message[2]:
                        plain_text = extract_plain_text(message[2])
                        print(f"Received new message: {plain_text}")
                    else:
                        print("Message received but no attributedBody property, ignoring...")
                else:
                    # print("Message with identical timestamp received, ignoring...")

                seen.add(message)
        time.sleep(0.01) # Poll every 10ms

if __name__ == "__main__":
    monitor_messages()
