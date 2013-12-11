import alacrity.mq.tasks as tasks
from celery import chain
import argparse
import tempfile
import os

if not tempfile.gettempdir().endswith('dota2replays'):
    tempfile.tempdir = os.path.join(tempfile.gettempdir(), 'dota2replays')

def endswith(array, ending):
    for x in array:
        if x.endswith(ending):
            yield x

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode',
            help='all = run whole match workflow' +
                 'league = update league list' +
                 'parse = parse downloaded replays in /tmp/dota2replays')

    args = parser.parse_args()
    if args.mode == 'all':
        tasks.workflow.delay()
    elif args.mode == 'league':
        tasks.update_leagues.delay()
    elif args.mode == 'parse':
        print 'parsing replay files in {}'.format(tempfile.tempdir)
        if os.path.exists(tempfile.tempdir):
            for root, dirs, files in os.walk(tempfile.tempdir):
                for fname in endswith(files, '.dem'):
                    path = os.path.join(root, fname)
                    print 'queuing match from {}'.format(path)
                    chain( \
                        tasks.parse_replay.subtask((path,), {'force': True}), \
                        tasks.delete_replay.s() \
                    ).apply_async()
    else:
        print 'invalid mode {}: must be all, league, or parse'.format(args.mode)


if __name__ == '__main__':
    main()
