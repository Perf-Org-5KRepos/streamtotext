import argparse
import asyncio

import pyaudio

from streamtotext import audio
from streamtotext import transcriber

async def timeout(ts, secs):
    await asyncio.sleep(secs)
    print('Timeout reached')
    await ts.stop()


async def handle_events(ts):
    while not ts.running:
        await asyncio.sleep(.1)

    async for ev in ts.events:
        print(ev)
    print('No more events')


def cmd_transcribe(args):
    mic = audio.Microphone(rate=44100)
    squelched = audio.SquelchedSource(mic)

    loop = asyncio.get_event_loop()

    print('Detecting squelch level.')
    level = loop.run_until_complete(
        squelched.detect_squelch_level(detect_time=4)
    )
    print('Done. Level is %f' % level)

    ts = transcriber.WatsonTranscriber()

    tasks = [
        asyncio.ensure_future(ts.transcribe(squelched)),
        asyncio.ensure_future(handle_events(ts)),
        asyncio.ensure_future(timeout(ts, 2))
    ]
    res = loop.run_until_complete(asyncio.gather(*tasks))


def cmd_list_devices(args):
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        print(p.get_device_info_by_index(i).get('name'))


def cmd_device_info(args):
    p = pyaudio.PyAudio()
    print(p.get_device_info_by_index(args.device_index))


def main():
    parser = argparse.ArgumentParser(description='Speech to text utility.')
    subparsers = parser.add_subparsers(help='command')

    parser_transcribe = subparsers.add_parser(
        'transcribe', help='Transcribe an audio source.'
    )
    parser_transcribe.add_argument('transcriber',
                                   choices=['watson'],
                                   help='Transcription service')
    parser_transcribe.set_defaults(func=cmd_transcribe)

    parser_list_devices = subparsers.add_parser(
        'list-devices', help='List local audio devices')
    parser_list_devices.set_defaults(func=cmd_list_devices)

    parser_device_info = subparsers.add_parser(
        'device-info', help='Get info about a device',
    )
    parser_device_info.add_argument('device_index', type=int,
                                    help='Numbered device index')
    parser_device_info.set_defaults(func=cmd_device_info)

    args = parser.parse_args()
    args.func(args)
