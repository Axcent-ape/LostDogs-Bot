import random
import time
from utils.core import logger
from pyrogram import Client
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
import asyncio
from urllib.parse import unquote, quote
from data import config
import aiohttp
from fake_useragent import UserAgent
from aiohttp_socks import ProxyConnector


class LostDogs:
    def __init__(self, thread: int, session_name: str, phone_number: str, proxy: [str, None]):
        self.account = session_name + '.session'
        self.thread = thread
        self.proxy = f"{config.PROXY['TYPE']['REQUESTS']}://{proxy}" if proxy is not None else None
        connector = ProxyConnector.from_url(self.proxy) if proxy else aiohttp.TCPConnector(verify_ssl=False)

        if proxy:
            proxy = {
                "scheme": config.PROXY['TYPE']['TG'],
                "hostname": proxy.split(":")[1].split("@")[1],
                "port": int(proxy.split(":")[2]),
                "username": proxy.split(":")[0],
                "password": proxy.split(":")[1].split("@")[0]
            }

        self.client = Client(
            name=session_name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            workdir=config.WORKDIR,
            proxy=proxy,
            lang_code='ru'
        )

        headers = {
            'User-Agent': UserAgent(os='android', browsers='chrome').random,
            'Content-Type': 'application/json',
            'Connection': 'keep-alive',
            'Origin': 'https://dog-ways.newcoolproject.io',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
        }
        self.session = aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def stats(self):
        await self.login()

        r = await (await self.session.get('https://api.getgems.io/graphql?operationName=getHomePage&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d89d3ccd8d9fd69d37d181e2e8303ee78b80e6a26e4500c42e6d9f695257f9be%22%7D%7D')).json()
        bones = r.get('data').get('lostDogsWayUserInfo').get('gameDogsBalance')
        woof = str(self.from_nano(int(r.get('data').get('lostDogsWayUserInfo').get('woofBalance'))))

        r = await (await self.session.get('https://api.getgems.io/graphql?operationName=lostDogsWayUserReferralInfo&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22b8715a45063000b04aceb73f791b95dfbecf3f85e5399b34c02a0d544bb84008%22%7D%7D')).json()
        referral_link = r.get('data').get('lostDogsWayUserReferralInfo').get('referralLink')
        referrals = r.get('data').get('lostDogsWayUserReferralInfo').get('invitedPeopleCount')

        await self.logout()

        await self.client.connect()
        me = await self.client.get_me()
        phone_number, name = "'" + me.phone_number, f"{me.first_name} {me.last_name if me.last_name is not None else ''}"
        await self.client.disconnect()

        proxy = self.proxy.replace('http://', "") if self.proxy is not None else '-'

        return [phone_number, name, bones, woof, referrals, referral_link, proxy]

    async def complete_task(self, task_id: str):
        json_data = {"operationName": "lostDogsWayCompleteCommonTask", "variables": {"id": task_id}, "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "313971cc7ece72b8e8edce3aa0bc72f6e40ef1c242250804d72b51da20a8626d"}}}
        r = await (await self.session.post('https://api.getgems.io/graphql', json=json_data)).json()
        return r.get('data').get('lostDogsWayCompleteCommonTask').get('success')

    async def get_tasks(self):
        r = await (await self.session.get('https://api.getgems.io/graphql?operationName=getDogsPage&variables=%7B%22withCommonTasks%22%3Atrue%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22a23b386ba13302517841d83364cd25ea6fcbf07e1a34a40a5314da8cfd1c6565%22%7D%7D')).json()

        task_list = r.get('data').get('lostDogsWayCommonTasks').get('items')
        done_tasks = r.get('data').get('lostDogsWayUserCommonTasksDone')

        tasks = [task for task in task_list if task["id"] not in done_tasks and task['name'] not in config.BLACKLIST_TASK]

        return tasks

    async def get_round_end(self):
        r = await (await self.session.get('https://api.getgems.io/graphql?operationName=getHomePage&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d89d3ccd8d9fd69d37d181e2e8303ee78b80e6a26e4500c42e6d9f695257f9be%22%7D%7D')).json()
        round_ends_at = r.get('data').get('lostDogsWayGameStatus').get('gameState').get('roundEndsAt')
        return round_ends_at

    async def current_round_vote(self):
        r = await (await self.session.get('https://api.getgems.io/graphql?operationName=getHomePage&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d89d3ccd8d9fd69d37d181e2e8303ee78b80e6a26e4500c42e6d9f695257f9be%22%7D%7D')).json()
        current_round = r.get('data').get('lostDogsWayUserInfo').get('currentRoundVote')
        return current_round

    async def get_previous_round_vote(self):
        r = await (await self.session.get('https://api.getgems.io/graphql?operationName=getHomePage&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d89d3ccd8d9fd69d37d181e2e8303ee78b80e6a26e4500c42e6d9f695257f9be%22%7D%7D')).json()
        round_vote = r.get('data').get('lostDogsWayUserInfo').get('prevRoundVote')
        if round_vote is None:
            return None, None, None

        is_win = round_vote.get('userStatus') == 'winner'
        not_prize = self.from_nano(r.get('notPrize')) if r.get('notPrize') else 0
        woof_prize = self.from_nano(r.get('woofPrize')) if r.get('woofPrize') else 0
        return is_win, not_prize, woof_prize

    async def vote(self, card: int):
        json_data = {"operationName": "lostDogsWayVote", "variables": {"value": str(card)}, "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "6fc1d24c3d91a69ebf7467ebbed43c8837f3d0057a624cdb371786477c12dc2f"}}}
        r = await (await self.session.post('https://api.getgems.io/graphql', json=json_data)).json()
        return 'lostDogsWayGenerateWallet' in str(r.get('data'))

    async def register(self):
        json_data = {"operationName": "lostDogsWayGenerateWallet", "variables": {}, "extensions": {"persistedQuery": {"version": 1, "sha256Hash": "d78ea322cda129ec3958fe21013f35ab630830479ea9510549963956127a44dd"}}}
        r = await (await self.session.post('https://api.getgems.io/graphql', json=json_data)).json()
        return 'lostDogsWayGenerateWallet' in str(r.get('data'))

    async def logout(self):
        await self.session.close()

    async def login(self,):
        await asyncio.sleep(random.uniform(*config.DELAYS['ACCOUNT']))
        query = await self.get_tg_web_data()

        if query is None:
            logger.error(f"Thread {self.thread} | {self.account} | Session {self.account} invalid")
            await self.logout()
            return None, None

        self.session.headers['X-Auth-Token'] = query
        self.session.headers['X-Gg-Client'] = 'v:1 l:ru'

        r = await (await self.session.get('https://api.getgems.io/graphql?operationName=getHomePage&variables=%7B%7D&extensions=%7B%22persistedQuery%22%3A%7B%22version%22%3A1%2C%22sha256Hash%22%3A%22d89d3ccd8d9fd69d37d181e2e8303ee78b80e6a26e4500c42e6d9f695257f9be%22%7D%7D')).json()
        if r.get('errors') is not None:
            if await self.register():
                logger.success(f"Thread {self.thread} | {self.account} | Register")

    async def get_tg_web_data(self):
        try:
            await self.client.connect()

            web_view = await self.client.invoke(RequestAppWebView(
                peer=await self.client.resolve_peer('lost_dogs_bot'),
                app=InputBotAppShortName(bot_id=await self.client.resolve_peer('lost_dogs_bot'), short_name="lodoapp"),
                platform='android',
                write_allowed=True,
                start_param=f"ref-u_6008239182__s_661959"
            ))
            await self.client.disconnect()
            auth_url = web_view.url
            query = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
            return query

        except:
            return None

    @staticmethod
    def from_nano(amount: int):
        return amount/1e9

    @staticmethod
    def current_time():
        return int(time.time())
