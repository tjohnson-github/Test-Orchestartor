#!/usr/bin/env python3

import json
import logging
import os
import uuid

from cassandra.cluster import Cluster
from cassandra.policies import RoundRobinPolicy

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


class database:
    def __init__(self, database):
        try:
            self.dbHost = os.environ['DATABASE_HOST'].split(',')
            logger.info("Database Host " + str(self.dbHost))
            self.database = database
        except Exception as e:
            logger.error("Error: {0}".format(e))
            pass

    def __del__(self):
        logger.error('Removing database object')

    def connect(self):
        ret = False
        try:
            logger.info("Database Host connecting" + str(self.dbHost))

            db_cluster = Cluster(self.dbHost, load_balancing_policy=RoundRobinPolicy())
            self.db_session = db_cluster.connect(keyspace=self.database)
            self.db_session.default_timeout = 5.0
            ret = True
        except Exception as e:
            logger.error("Error: {0}".format(e))

        return ret

    def create(self, table):
        try:
            rows = self.queryTableExist(table)
            if not rows:
                logger.info('create table {0}'.format(table))
        except Exception as e:
            logger.error("Error: {0}".format(e))

    def insert(self, table, data):
        try:
            logger.info('Insert Records into {0}'.format(table))
            stmt = self.db_session.prepare('INSERT INTO {0} JSON ?;'.format(table))
            data = json.dumps(data)
            self.db_session.execute(stmt, [data])
        except Exception as e:
            logger.error("Error: {0}".format(e))

    def update(self, table, data):
        try:
            logger.info('Update Table {0}'.format(table))
            stmt = self.db_session.prepare('INSERT INTO {0} JSON ? DEFAULT UNSET;'.format(table))
            data = json.dumps(data)
            self.db_session.execute(stmt, [data])
        except Exception as e:
            logger.error("Error: {0}".format(e))

    def query(self, table, test_id):
        rows = None

        try:
            logger.info("query {0}".format(test_id))
            if not isinstance(test_id, uuid.UUID):
                id = uuid.UUID(test_id)
            else:
                id = test_id

            query = "SELECT * FROM {0} WHERE test_id=%s allow filtering".format(table)
            future = self.db_session.execute_async(query, [id])
            rows = future.result()
        except Exception as e:
            logger.error("Error: {0}".format(e))

        return rows

    def queryKey(self, table, key, value):
        rows = None
        try:
            query = "SELECT * FROM {0} WHERE {1}=%s allow filtering".format(table, key)
            future = self.db_session.execute_async(query, [value])
            rows = future.result()
        except Exception as e:
            logger.error("Error: {0}".format(e))

        return rows

    def queryTableExist(self, table):
        try:
            query = "SELECT table_name FROM system_schema.tables WHERE keyspace_name=%s and table_name=%s allow filtering"
            future = self.db_session.execute_async(query, [self.database, table])
            rows = future.result()
        except Exception as e:
            logger.error("Error: {0}".format(e))

        return rows

    def AddResults(self, test_id, test_name, num_clients, tier, ip_gateway, gateway_version, client_version, protocol, test_mode, encryption, test_key):
        try:
            result = dict()
            result['test_id'] = str(test_id)
            result['gateway_version'] = gateway_version
            result['client_version'] = client_version
            result['ip_gateway'] = ip_gateway
            result['tier'] = tier
            result['protocol'] = protocol
            result['num_clients'] = num_clients
            result['test_name'] = test_name
            result['test_key'] = test_key
            # result['test_mode']=test_mode
            # result['encryption']=encryption
            self.insert('perf_results', result)
        except Exception as e:
            logger.error("Error: {0}".format(e))

    def UpdateResults(self, test_id, test_mode, reason):
        try:
            clientSuccess = 0
            duration = 60
            result = dict()
            mbpsStats = []
            error_text = reason
            numClients = 0

            rows = self.query('perf2', test_id)
            logger.info("update ")
            for row in rows:
                clientSuccess += 1
                duration = row.duration
                numClients = row.num_clients
                error_text += ' Err:{0} {1}'.format(row.error_no, row.error_text)
                if test_mode == 'download':
                    mbpsStats.append(float(row.sent_mbps))
                else:
                    mbpsStats.append(float(row.rcvd_mbps))

            # add perf summary in summary table
            if mbpsStats:
                result['result'] = 'Success'
                result['test_id'] = str(test_id)
                result['failed_rate'] = int((len(mbpsStats)/2)/numClients * 100)
                result['avg_mbps'] = sum(mbpsStats)/len(mbpsStats)
                result['max_mbps'] = max(mbpsStats)
                result['min_mbps'] = min(mbpsStats)
                result['error_text'] = 'Test Completed'
                result['duration'] = duration
            else:
                result['test_id'] = str(test_id)
                result['result'] = 'Failed'
                result['error_text'] = error_text

            logger.info("update {0}".format(result))
            self.update('perf_results', result)

            return result
        except Exception as e:
            logger.error("Error: {0}".format(e))

    def UpdateGatewayStats(self, test_id, cpu, cpu_free, mem, mem_free, packetsPerSec):
        result = dict()

        result['test_id'] = str(test_id)
        result['gateway_cpu_utilization'] = cpu
        result['gateway_cpu_free'] = cpu_free
        result['gateway_memory'] = mem
        result['gateway_memory_free'] = mem_free
        result['packetsPerSec'] = packetsPerSec
        self.update('perf_results', result)

    def QueryToJson(self, table, test_id):
        try:
            endpoints = dict()
            outDict = dict()
            data = dict()
            events = []
            hostinfo = dict()
            testName = "test-cell"
            duration = "60"

            outDict["test-id"] = test_id

            rows = self.query(table, test_id)
            for row in rows:
                data = dict()

                if row.session_id:
                    data["session"] = row.session_id

                    perfRows = self.queryKey('perf2', 'session_key', row.session_id)
                    for prow in perfRows:
                        # set topology
                        hostinfo = dict()
                        hostinfo["name"] = row.name
                        hostinfo["instance-type"] = "t2.micro"
                        endpoints[row.source] = hostinfo
                        testName = prow.test_name
                        duration = prow.duration

                data["ts"] = row.timestamp_value
                data["op"] = row.op
                data["payload"] = json.loads(row.raw_json)
                data["source"] = row.source
                events.append(data)

            # sort events for now
            events = sorted(events, key=lambda p: p["ts"], reverse=False)

            outDict["events"] = events
            # get first event and set start time
            outDict["start"] = events[0]["ts"]
            outDict["topology"] = endpoints
            outDict["test-name"] = testName
            outDict["duration"] = duration
        except Exception as e:
            logger.error("Error: {0}".format(e))
        else:
            return json.dumps(outDict)
