import alacrity.mq.tasks as tasks
from alacrity.config.db import userupload_db
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
            help='league = workflow for league matches\n' +
                 'user = workflow for user-uploaded replays\n' +
                 'league_list = update league list\n' +
                 'parse = parse downloaded replays in /tmp/dota2replays')

    args = parser.parse_args()
    if args.mode == 'league':
        tasks.league_match_workflow.delay()
    elif args.mode == 'user':
        tasks.user_replay_workflow.delay()
    elif args.mode == 'league_list':
        tasks.update_leagues.delay()
    elif args.mode == 'parse':
        print 'parsing replay files in {}'.format(tempfile.tempdir)
        if os.path.exists(tempfile.tempdir):
            for root, dirs, files in os.walk(tempfile.tempdir):
                for fname in endswith(files, '.dem'):
                    path = os.path.join(root, fname)
                    print 'queuing match from {}'.format(path)
                    # TODO: change notif_key propagation or look it up here
                    chain( \
                        tasks.parse_replay.subtask(((path, None)), {'force': True}), \
                        tasks.delete_replay.s() \
                    ).apply_async()
    else:
        print 'invalid mode {}: must be league, user, league_list, or parse'.format(args.mode)


if __name__ == '__main__':
    main()
