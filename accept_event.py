from datetime import date
import os
import argparse
import asyncio
import csv
from spond import spond
from config import username, password
import time


parser = argparse.ArgumentParser(description="Creates an attendance.csv for organizers of events.")
parser.add_argument("-f", "--from", help="First date to query for. Date is included in results (format YYYY-MM-DD)", type=date.fromisoformat, dest="f")
parser.add_argument("-t", "--to", help="Last date to query for. Date is excluded from results (format YYYY-MM-DD)", type=date.fromisoformat, dest="t")
parser.add_argument("-a", help="Also include all members", default=False, action='store_true')
args = parser.parse_args()

async def main():
    s = spond.Spond(username=username, password=password)
    CAGEBALL = ""
    PADEL = ""
    RUN = ""
        
    while True:
        event = await s.acceptEvent(RUN)
        if event:
            if s.person['id'] in event["responses"]["acceptedIds"]:
                break
        time.sleep(5)
    await s.clientsession.close()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())

# {'errorKey': 'inviteNotSent', 'message': 'Invitation has not been sent out', 'errorCode': 3004}
