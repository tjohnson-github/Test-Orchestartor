#!/usr/bin/env python

from __future__ import print_function

import json
import logging
import psutil
import socket
import sys
import time
import uuid

from test_common.database import database

db = {}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main():
    global d
    """main program"""

    version = ""
    gateway_version = ""
    gateway_addr4 = ""
    ip_addr4 = ""
    test_id = ""
    host_id = ""
    test_name = ""
    num_clients = 0
    tier = ""

    session_key = ""

    logger.info("Database Create cluster")
    try:
        # -i {3} -h {4} -n {5} -c {6} -t {7} -k {key}
        # ixendpoint won't have key yet for now
        if len(sys.argv) >= 2:
            if (sys.argv[1] == "-a"):
                endpoint_type = int(sys.argv[2])
                logger.info("Database endpoint type: %s" % endpoint_type)
        if len(sys.argv) >= 4:
            if (sys.argv[3] == "-i"):
                test_id = sys.argv[4]
                logger.info("Database test_id %s" % test_id)
        if len(sys.argv) >= 6:
            if (sys.argv[5] == "-h"):
                host_id = sys.argv[6]
                logger.info("Database host_id %s" % host_id)
        if len(sys.argv) >= 8:
            if (sys.argv[7] == "-n"):
                test_name = sys.argv[8]
                logger.info("Database test_name %s" % test_name)
        if len(sys.argv) >= 10:
            if (sys.argv[9] == "-c"):
                num_clients = int(sys.argv[10])
                logger.info("Database clients %d" % num_clients)
        if len(sys.argv) >= 12:
            if (sys.argv[11] == "-t"):
                tier = sys.argv[12]
                logger.info("Database teir %s" % tier)
        if len(sys.argv) >= 14:
            if (sys.argv[13] == "-k"):
                session_key = sys.argv[14]
                logger.info("Database session %s" % session_key)
        if len(sys.argv) >= 15:
            if (sys.argv[13] == "-e"):
                error = sys.argv[14] + sys.argv[15]

        # look up session key in database
        try:
            if session_key != "":
                dbJumpnet = database('jumpnettest')
                dbJumpnet.connect()

                rows_clientd = dbJumpnet.queryKey('sessions', 'key', session_key)

                logger.info("** Got Result **")
                session_clientd = rows_clientd[0]
                logger.info("** Got clientd session **")
                gateway_key = session_clientd.gateway
                ip_addr4 = session_clientd.addr4
                version = str(session_clientd.version)

                logger.info("Found clientd session {0} ".format(session_clientd.key))

                rows_gatewayd = dbJumpnet.queryKey('sessions', 'key', gateway_key)
                session_gatewayd = rows_gatewayd[0]
                gateway_addr4 = session_gatewayd.addr4[0]

                logger.info("Found gatewayd version {0} session {1} ".format(gateway_version, session_gatewayd.key))

        except Exception as e:
            logger.error("Error %s" % e)

        jsonstr = ""
        i = 0
        m = False
        for line in sys.stdin:
            i += 1
            if line == "{\n":
                jsonstr = "{"
                # print("found open line %d",i)
                m = True
            elif line == "}\n":
                jsonstr += "}"
                # print("found close line %d",i)
                if m:
                    process(jsonstr,
                            endpoint_type,
                            test_id,
                            host_id,
                            test_name,
                            num_clients,
                            tier,
                            gateway_version,
                            version,
                            ip_addr4,
                            gateway_addr4,
                            session_key)
                m = False
                jsonstr = ""
            else:
                # print("else at line %d = %s",i,line)
                if m:
                    jsonstr += line
                # else:
                #     print("bogus at line %d = %s",i,line)

    except Exception as e:
        logger.error('iperf error: %s' % e)


def process(js, endpoint_type, test_id, host_id, test_name, num_clients, tier, gateway_version, version, ip_addr4, gateway_addr4, session_key):
    perf = dict()

    if test_id == "":
        test_id = str(uuid.uuid4())
    if host_id == "":
        host_id = str(uuid.uuid4())
    if test_name == "":
        test_name = "cell"
    if version == "":
        version = ""

    mem = psutil.virtual_memory()
    hostname = socket.gethostname()

    ip_gateway = gateway_addr4
    ip = ip_addr4
    cpu = 0
    cpu_free = 0
    mem_free = 0
    mem = 0
    host_size = ""
    error_no = 0
    error_text = ""

    try:
        logger.info("Process json output..")
        obj = json.loads(js)
    except Exception:
        logger.error("bad json")
        pass
        return False
    try:
        # caveat: assumes multiple streams are all from same IP so we take the 1st one
        # todo: handle errors and missing elements
        ip = str((obj["start"]["connected"][0]["remote_host"]).encode('ascii', 'ignore'), 'utf-8')
        local_port = obj["start"]["connected"][0]["local_port"]
        remote_port = obj["start"]["connected"][0]["remote_port"]

        logger.info("Database 1")
        sent = obj["end"]["sum_sent"]["bytes"]
        rcvd = obj["end"]["sum_received"]["bytes"]
        sent_speed = obj["end"]["sum_sent"]["bits_per_second"] / 1000 / 1000
        rcvd_speed = obj["end"]["sum_received"]["bits_per_second"] / 1000 / 1000
        cpu = obj["end"]["cpu_utilization_percent"]["host_total"]

        logger.info("Database 2")
        reverse = obj["start"]["test_start"]["reverse"]
        time_secs = obj["start"]["timestamp"]["timesecs"]
        logger.info("Database time convert %f" % time_secs)

        stime = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time_secs)) + "Z"
        logger.info("Database time converted %s" % stime)
        cookie = str((obj["start"]["cookie"]).encode('ascii', 'ignore'), 'utf-8')
        protocol = str((obj["start"]["test_start"]["protocol"]).encode('ascii', 'ignore'), 'utf-8')
        duration = obj["start"]["test_start"]["duration"]
        num_streams = obj["start"]["test_start"]["num_streams"]

        logger.info("Database got all objects for insert")

        s = 0
        r = 0

        if reverse not in [0, 1]:
            sys.exit("unknown reverse")

        logger.info("Reverse check succedded")

        if ip in db:
            (s, r) = db[ip]

        logger.info("Database ip check succedded")

        if reverse == 0:
            r += rcvd
            sent = 0
            sent_speed = 0
        else:
            s += sent
            rcvd = 0
            rcvd_speed = 0

        db[ip] = (s, r)

        logger.info("Database insert {0} {1}".format(test_id, host_id))

        # csvwriter.writerow([time, ip, local_port, remote_port, duration, protocol, num_streams, cookie, sent, sent_speed, rcvd, rcvd_speed, s, r])

        dbTestTier = database('testtier')
        dbTestTier.connect()

        perf["test_id"] = test_id
        perf["host_id"] = host_id
        perf["test_name"] = test_name
        perf["test_type"] = endpoint_type
        perf["num_clients"] = num_clients
        perf["host_size"] = host_size
        perf["version"] = version
        perf["gateway_version"] = gateway_version
        perf["date"] = stime
        perf["host_name"] = hostname
        perf["ip"] = ip
        perf["ip_gateway"] = ip_gateway
        perf["tier"] = tier
        perf["gateway_cpu_utilization"] = cpu
        perf["gateway_cpu_free"] = cpu_free
        perf["gateway_memory"] = mem
        perf["gateway_memory_free"] = mem_free
        perf["local_port"] = str(local_port)
        perf["remote_port"] = str(remote_port)
        perf["duration"] = duration
        perf["protocol"] = protocol
        perf["num_streams"] = num_streams
        perf["cookie"] = cookie
        perf["sent"] = sent
        perf["sent_mbps"] = sent_speed
        perf["rcvd"] = rcvd
        perf["rcvd_mbps"] = rcvd_speed
        perf["totalsent"] = s
        perf["totalreceived"] = r
        perf["error_no"] = error_no
        perf["error_text"] = error_text
        perf["raw_json"] = js
        perf["session_key"] = session_key

        dbTestTier.insert('perf2', perf)

        logger.info("Database Insert Completed!")

        return True
    except Exception as e:
        logger.error(e)
        return False


def dumpdb(database):
    """ dump db to text """
    for i in database:
        (s, r) = database[i]
        print("%s, %d , %d " % (i, s, r))


if __name__ == '__main__':
    main()
