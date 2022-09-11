from datetime import date
from datetime import datetime
import argparse
import asyncio
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
    CAGEBALL = "XXXXXXXXXXXXx"
    PADEL = "XXXXXXXXXXXXXXXXx"
    RUN = "XXXXXXXXXXXXXX"
    SLEEP = False
    while True:
        if not SLEEP:
            event = await s.acceptEvent(RUN)
            invite_time = datetime.strptime(event['inviteTime'],'%Y-%m-%dT%H:%M:%SZ') if "inviteTime" in event.keys() else None
            SLEEP = True if invite_time and invite_time > datetime.utcnow() else False
            if event:
                if (("responses" in event.keys() and s.person['id'] in event["responses"]["acceptedIds"]) \
                    or ("acceptedIds" in event.keys() and s.person['id'] in event["acceptedIds"])):
                    break
        print("Invite time not passed time now. Sleeping 5s")
        time.sleep(5)
    await s.clientsession.close()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

# {'errorKey': 'inviteNotSent', 'message': 'Invitation has not been sent out', 'errorCode': 3004}
