#!/usr/bin/env python3

import asyncio
import aiohttp

from datetime import datetime, timedelta

class Spond():
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.apiurl = "https://spond.com/api/2.1/"
        self.clientsession = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())
        self.chaturl = None
        self.auth = None
        self.cookie = None
        self.groups = None
        self.events = None
        self.person = None



    async def login(self):
        url = self.apiurl + "login"
        data = { 'email': self.username, 'password': self.password }
        async with self.clientsession.post(url, json=data) as r:
            self.cookie = r.cookies['auth']
        # print(self.cookie.value)
        url = self.apiurl + "chat"
        # headers = { 'content-length': '0', 'accept': '*/*', 'api-level': '2.5.25', 'origin': 'https://spond.com', 'referer': 'https://spond.com/client/', 'content-type': 'application/json;charset=utf-8' }
        headers = { 'content-type': 'application/json;charset=utf-8' }
        res = await self.clientsession.post(url, headers=headers)
        result = await res.json()

        self.chaturl = result['url']
        self.auth = result['auth']
        self.person = await self.getPerson(self.username)

    async def getGroups(self):
        """
        Get all groups.
        Subject to authenticated user's access.

        Returns
        -------
        list of dict
            Groups; each group is a dict.
        """
        if not self.cookie:
            await self.login()
        url = self.apiurl + "groups/"
        async with self.clientsession.get(url) as r:
            self.groups = await r.json()
            return self.groups

    async def getGroup(self, uid):
        """
        Get a group by unique ID.
        Subject to authenticated user's access.

        Parameters
        ----------
        uid : str
            UID of the group.

        Returns
        -------
        dict
            Details of the group.
        """
        if not self.cookie:
            await self.login()
        if not self.groups:
            await self.getGroups()
        for group in self.groups:
            if group['id'] == uid:
                return group

    async def getPerson(self, user):
        """
        Get a member or guardian by matching various identifiers.
        Subject to authenticated user's access.

        Parameters
        ----------
        user : str
            Identifier to match against member/guardian's id, email, full name, or
            profile id.

        Returns
        -------
        dict
             Member or guardian's details.
        """
        if not self.cookie:
            await self.login()
        if not self.groups:
            await self.getGroups()
        for group in self.groups:
            for member in group['members']:
                if member['id'] == user or ('email' in member and member['email']) == user or member['firstName'] + " " + member['lastName'] == user or ( 'profile' in member and member['profile']['id'] == user):
                    return member
                if 'guardians' in member:
                    for guardian in member['guardians']:
                        if guardian['id'] == user or ('email' in guardian and guardian['email']) == user or guardian['firstName'] + " " + guardian['lastName'] == user or ( 'profile' in guardian and guardian['profile']['id'] == user):
                            return guardian

    async def getMessages(self):
        if not self.cookie:
            await self.login()
        url = self.chaturl + "/chats/?max=10"
        headers = { 'auth': self.auth }
        async with self.clientsession.get(url, headers=headers) as r:
            return await r.json()


    async def sendMessage(self, recipient, text):
        if not self.cookie:
            await self.login()
        url = self.chaturl + "/messages"
        data = { 'recipient': recipient, 'text': text, 'type': "TEXT" }
        headers = { 'auth': self.auth }
        r = await self.clientsession.post(url, json=data, headers=headers)
        print(r)
        return await r.json()

    async def getEvents(self, from_date = None):
        """
        Get up to 100 events up to present.
        Subject to authenticated user's access.
        Excludes cancelled events.

        Parameters
        ----------
        from_date : datetime, optional
            Only return events which finish after this value.
            If omitted, the last 14 days.

        Returns
        -------
        list of dict
            Events; each event is a dict.
        """
        if not self.cookie:
            await self.login()
        if not from_date:
            from_date = datetime.now() - timedelta(days=14)
        url = self.apiurl + "sponds/?max=100&minEndTimestamp={}&order=asc&scheduled=true".format(from_date.strftime("%Y-%m-%dT00:00:00.000Z"))
        async with self.clientsession.get(url) as r:
            self.events = await r.json()
            return self.events

    async def getEventsBetween(self, from_date, to_date, max_events=100) -> list[dict[str,str]]:
        """
        Get events between two datetimes.
        Subject to authenticated user's access.
        Excludes cancelled events.

        Parameters
        ----------
        from_date : datetime
            Only return events which finish after this value.
        to_date : datetime
            Only return events which finish before this value.
        max_events : int, optional
            Set a limit on the number of events returned

        Returns
        -------
        list of dict
            Events; each event is a dict.
        """
        if not self.cookie:
            await self.login()
        url = (
            f"{self.apiurl}sponds/?"
            f"max={max_events}&"
            f"minEndTimestamp={from_date.strftime('%Y-%m-%dT00:00:00.000Z')}&"
            f"maxEndTimestamp={to_date.strftime('%Y-%m-%dT00:00:00.000Z')}&"
            f"order=asc&scheduled=true"
        )
        async with self.clientsession.get(url) as r:
            self.events = await r.json()
            return self.events

    async def getEvent(self, uid) -> dict[str,str]:
        """
        Get an event by unique ID.
        Subject to authenticated user's access.

        Parameters
        ----------
        uid : str
            UID of the event.

        Returns
        -------
        dict
            Details of the event.
        """
        if not self.cookie:
            await self.login()
        if not self.events:
            await self.getEvents()
        for event in self.events:
            if event['id'] == uid:
                return event
            
    async def acceptEvent(self, uid:str) -> dict[str,str]:
        """
        Accept an event by unique ID.
        - Subject to authenticated user's access.
        - Will check if user id has already accepted.
        - Will check if invite is sent out before running PUT request.

        Parameters
        ----------
        uid : str
            UID of the event.

        Returns
        -------
        dict
            Details of the event
        """
        if not self.cookie:
            await self.login()
        event = await self.getEvent(uid)
        if "inviteTime" in event.keys() and datetime.strptime(event['inviteTime'],'%Y-%m-%dT%H:%M:%SZ') > datetime.utcnow():
            print(F"Invite time: ({event['inviteTime']}) for event: {event['heading']} is greater than now...try again later.")
            return event
        url = f"{self.apiurl}sponds/{uid}/responses/{self.person['id']}"
        data = {"accepted": True}
        headers = { 'auth': self.auth }
        if self.person['id'] not in event["responses"]["acceptedIds"]:
            async with self.clientsession.put(url, json=data, headers=headers) as r:
                event = await r.json()
                if self.person['id'] in event["responses"]["acceptedIds"]:
                    print(f"User: {self.person['firstName']} {self.person['lastName']} is now accepted.")
        else:
            print(f"{self.person['firstName']} {self.person['lastName']} has already accepted")
        return event

