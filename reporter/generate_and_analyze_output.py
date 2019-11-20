import argparse
import sys

from slackclient import SlackClient

from janalyze.runtestbed import runtestbed
from test_common.database import database
from test_common.util import Util


class Reporter:
    HTML_ERROR_TEMPLATE = '\n'.join([
        '<!DOCTYPE html>',
        '',
        '<html lang="en">',
        '',
        '  <head>',
        '      <meta charset="utf-8">',
        '      <title>Test {test_id} error</title>',
        '  </head>',
        '',
        '  <body>',
        '    {body}',
        '  </body>',
        '',
        '</html>',
    ])
    DB_KEYSPACE = 'testtier'
    REPORT_HTML = 'raw/result/output/simoutput.html'
    REPORT_URL_TEMPLATE = 'https://gitlab.trinity.cc/test/reporter/-/jobs/{job}/artifacts/' + REPORT_HTML
    SLACK_CHANNEL = 'CCW3B94GZ'
    SLACK_TOKEN = 'xoxp-10351633397-10359027170-438668796707-d20df1d259fd699fc08989342c15bdc4'
    TESTBED_LIMIT = 0

    def __init__(self, test_id, job_id, pipeline_id, project_id, output_file, analyze):
        self.test_id = test_id
        self.job_id = job_id
        self.pipeline_id = pipeline_id
        self.project_id = project_id
        self.output_path = output_file
        self.analyze = analyze

    def run(self):
        try:
            testoutput_filename = self.generate_test_output_json_file()
            if self.analyze:
                self.analyze_and_report(testoutput_filename)
                self.update_portal()

        except Exception as err:
            self._error('Unexpected error: {}'.format(err))

    def update_portal(self):
        db = database(self.DB_KEYSPACE)
        if not db.connect():
           self._error('Could not connect to Database!')
        
        rows = db.query('perf_results', self.test_id)
        if not rows:
            self._error('No perf results Data Found!')

        for row in rows:
            test_key = row.test_key

        results = dict()
        results['report_pipeline'] = self.pipeline_id
        results['report_project_id'] = self.project_id
        results['report_job_id'] = self.job_id
        results['report_html'] = self.REPORT_HTML

        resp = Util.update_status(test_key, 'success', 'reporter', 'testbed', results)

    def generate_test_output_json_file(self):
        db = database(self.DB_KEYSPACE)
        if not db.connect():
            self._error('Could not connect to Database!')

        data = db.QueryToJson('usagestats', self.test_id)
        if not data:
            self._error('No Usage stat Data Found!')

        print('Test output json: {0}'.format(data))
        testoutput_filename = 'testoutput.json'
        with open(testoutput_filename, 'w') as fd:
            fd.write(data)

        return testoutput_filename

    def analyze_and_report(self, testoutput_filename):
        runtestbed(testoutput_filename, self.output_path, self.TESTBED_LIMIT)
        self._slack_notification()

    def _slack_notification(self):
        report_url = self.REPORT_URL_TEMPLATE.format(job=self.job_id)
        message = 'Testbed Report: Test {}\n{}'.format(self.test_id, report_url)
        try:
            sc = SlackClient(self.SLACK_TOKEN)
            sc.api_call('chat.postMessage', channel=self.SLACK_CHANNEL, text=message)
        except Exception as e:
            print('Failed to send to slack: {}'.format(e))

    def _error(self, error_msg):
        """
        Generate html error, send slack notification and terminate execution with non zero exit code.
        """
        html = self.HTML_ERROR_TEMPLATE.format(test_id=self.test_id, body=error_msg)
        with open(self.output_path, 'w') as fd:
            fd.write(html)
        self._slack_notification()
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('test_id')
    parser.add_argument('job_id')
    parser.add_argument("pipeline_id")
    parser.add_argument("project_id")
    parser.add_argument('output_file')
    parser.add_argument('--no-analyze', action='store_true', help='Do not analyze. Only generate testoutput file.')
    args = parser.parse_args()
    print('Running job_id {jid} for test_id: {tid} with output_path: {out}'.format(tid=args.test_id, out=args.output_file, jid=args.job_id))

    reported = Reporter(args.test_id, args.job_id, args.pipeline_id, args.project_id, args.output_file, not args.no_analyze)
    reported.run()


if __name__ == '__main__':
    main()

