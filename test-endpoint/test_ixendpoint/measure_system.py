#!/usr/bin/env python

import logging
import psutil
import threading
from test_common.database import database

INTERVAL = 5            # 1 second
AVG_LOW_PASS = 0.2      # Simple Complemetary Filter

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


class MeasureSystem:
    def __init__(self, type, interface):
        try:
            self.obj = dict()
            self.ifaces = {}
            self.cpuStats = []
            self.cpuFreeStats = []
            self.memStats = []
            self.memFreeStats = []
            self.TXStats = []
            self.RXStats = []
            self.interface = interface
            self.db = database('testtier')
            self.db.connect()

            if ('packets' in type):
                logger.info("Loading Network Interfaces")
                idata = GetNetworkInterfaces('tun0')
                logger.info("Filling tables")
                for eth in idata:
                    ifaces[eth["interface"]] = {
                        "rxrate": 0,
                        "txrate": 0,
                        "avgrx": 0,
                        "avgtx": 0,
                        "toptx": 0,
                        "toprx": 0,
                        "sendbytes": eth["tx"]["bytes"],
                        "recvbytes": eth["rx"]["bytes"]
                    }
                # kick of timer thread
                t = threading.Timer(INTERVAL, self.measurePackets)
                t.start()
            elif ('cpu' in type):
                t = threading.Timer(INTERVAL, self.measureCPU)
                t.start()
        except Exception as e:
            logger.error('Error: %s' % e)

    def __del__(self):
        logger.error('Remove timers')
        t.cancel()

    def recordPackets(self):
        try:
            t.cancel()
            rx_max = self.ifaces[eth["interface"]]["toprx"]
            self.db.UpdateGatewayStats(test_id, max(cpuStats), min(cpuFreeStats), max(memStats),  min(memFreeStats), rx_max)
        except Exception as e:
            pass

    def measurePackets(self):
        try:
            logger.info("Loading Network Interfaces")
            idata = self.GetNetworkInterfaces('tun0')
            for eth in idata:
                logger.info("Date: {0}".format(eth))
                #   Calculate the Rate
                self.ifaces[eth["interface"]]["rxrate"] = (eth["rx"]["bytes"] - self.ifaces[eth["interface"]]["recvbytes"]) / INTERVAL  # noqa
                self.ifaces[eth["interface"]]["txrate"] = (eth["tx"]["bytes"] - self.ifaces[eth["interface"]]["sendbytes"]) / INTERVAL  # noqa

                #   Set the rx/tx bytes
                self.ifaces[eth["interface"]]["recvbytes"] = eth["rx"]["bytes"]
                self.ifaces[eth["interface"]]["sendbytes"] = eth["tx"]["bytes"]

                #   Calculate the Average Rate
                self.ifaces[eth["interface"]]["avgrx"] = int(ifaces[eth["interface"]]["rxrate"] * AVG_LOW_PASS + self.ifaces[eth["interface"]]["avgrx"] * (1.0-AVG_LOW_PASS))  # noqa
                self.ifaces[eth["interface"]]["avgtx"] = int(ifaces[eth["interface"]]["txrate"] * AVG_LOW_PASS + self.ifaces[eth["interface"]]["avgtx"] * (1.0-AVG_LOW_PASS))  # noqa

                #   Set the Max Rates
                self.ifaces[eth["interface"]]["toprx"] = self.ifaces[eth["interface"]]["rxrate"] if ifaces[eth["interface"]]["rxrate"] > self.ifaces[eth["interface"]]["toprx"] else self.ifaces[eth["interface"]]["toprx"]  # noqa
                self.ifaces[eth["interface"]]["toptx"] = self.ifaces[eth["interface"]]["txrate"] if ifaces[eth["interface"]]["txrate"] > self.ifaces[eth["interface"]]["toptx"] else self.ifaces[eth["interface"]]["toptx"]  # noqa

                logger.info("%s: in B/S" %(eth["interface"]))
                logger.info("\tRX - MAX: %s AVG: %s CUR: %s" %(self.ifaces[eth["interface"]]["toprx"], self.ifaces[eth["interface"]]["avgrx"], self.ifaces[eth["interface"]]["rxrate"]))  # noqa
                logger.info("\tTX - MAX: %s AVG: %s CUR: %s" %(self.ifaces[eth["interface"]]["toptx"], self.ifaces[eth["interface"]]["avgtx"], self.ifaces[eth["interface"]]["txrate"]))  # noqa
                logger.info("")
        except Exception as e:
            logger.error('Error: %s' % e)

    def measureCPU(self):
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent()  / psutil.cpu_count()

        logger.info("CPU: {0} MEM: {1}".format(cpu, mem))

        cpuStats.append(cpu)
        cpuFreeStats.append(0)  # todo
        memStats.append(mem)
        memFreeStats.append(0)  # todo

    def insert(self, table):
        try:
            session.execute('USE testtier;')
            insert_statment = session.prepare('INSERT INTO {0} JSON ?'.format(table))
            session.execute(insert_statement, [self.obj])
        except Exception as e:
            logger.error('Error: %s' % e)
            pass

    def GetNetworkInterfaces(self, interface):
        try:
            self.ifaces = []
            f = open("/proc/net/dev")
            data = f.read()
            f.close()
            data = data.split("\n")[2:]

            for i in data:
                if len(i.strip()) > 0:
                    x = i.split()

                    if interface in x[0][:len(x[0])-1]:
                        # Interface |                        Receive                          |                         Transmit
                        #   iface   | bytes packets errs drop fifo frame compressed multicast | bytes packets errs drop fifo frame compressed multicast
                        k = {
                            "interface": x[0][:len(x[0])-1],
                            "tx": {
                                "bytes": int(x[1]),
                                "packets": int(x[2]),
                                "errs": int(x[3]),
                                "drop": int(x[4]),
                                "fifo": int(x[5]),
                                "frame": int(x[6]),
                                "compressed": int(x[7]),
                                "multicast": int(x[8])
                            },
                            "rx": {
                                "bytes": int(x[9]),
                                "packets": int(x[10]),
                                "errs": int(x[11]),
                                "drop": int(x[12]),
                                "fifo": int(x[13]),
                                "frame": int(x[14]),
                                "compressed": int(x[15]),
                                "multicast": int(x[16])
                            }
                        }
                        ifaces.append(k)

            logger.info('interface: {0}'.format(ifaces))

        except Exception as e:
            logger.error('Error: %s' % e)

        return ifaces
