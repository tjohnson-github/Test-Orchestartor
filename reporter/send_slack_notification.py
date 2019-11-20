# Todo Implement
#
# This file needs to send a notification of the test output to slack
# (possibly needs to use an intermediate format)

import argparse
from slackclient import SlackClient


def slack_notification(test_id, url):
    # TODO: refactor this later
    SLACK_TOKEN = 'xoxp-10351633397-10359027170-438668796707-d20df1d259fd699fc08989342c15bdc4'
    SLACK_CHANNEL = 'CCW3B94GZ'
    try:
        message = 'Testbed Report: Test {}\n{}'.format(test_id, url)
        sc = SlackClient(SLACK_TOKEN)
        sc.api_call("chat.postMessage", channel=SLACK_CHANNEL, text=message)
    except Exception as e:
        print("Failed to send to slack: " + str(e))


parser = argparse.ArgumentParser()
parser.add_argument("test_id")
parser.add_argument("job_id")
args = parser.parse_args()

test_id = args.test_id
job_id = args.job_id
url = 'https://gitlab.trinity.cc/test/reporter/-/jobs/{job}/artifacts/raw/result/output/simoutput.html'.format(job=job_id)

# Send the report URL to slack
slack_notification(test_id, url)
