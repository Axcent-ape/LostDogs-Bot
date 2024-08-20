import random
from utils.lost_dogs import LostDogs
from data import config
from utils.core import logger
import datetime
import pandas as pd
from utils.core.telegram import Accounts
import asyncio
import os


async def start(thread: int, session_name: str, phone_number: str, proxy: [str, None]):
    dogs = LostDogs(session_name=session_name, phone_number=phone_number, thread=thread, proxy=proxy)
    account = session_name + '.session'

    await dogs.login()

    while True:
        try:
            current_round = await dogs.current_round_vote()

            for task in await dogs.get_tasks():
                if await dogs.complete_task(task['id']):
                    logger.success(f"Thread {thread} | {account} | Completed task «{task['name']}» and got {task['dogReward']} BONES & {dogs.from_nano(int(task['woofReward']))} WOOF")
                else:
                    logger.warning(f"Thread {thread} | {account} | Couldn't complete task «{task['name']}»")

                await asyncio.sleep(random.uniform(*config.DELAYS['TASK']))

            if not current_round:
                card = random.randint(1, 3)
                await dogs.vote(card)
                logger.info(f"Thread {thread} | {account} | Voted for card №{card}")

            sleep = await dogs.get_round_end() - dogs.current_time() + 1100 + round(random.uniform(*config.DELAYS['SLEEP']), 1)
            logger.info(f"Thread {thread} | {account} | Sleep {sleep} seconds")
            await asyncio.sleep(sleep)

            is_win, not_prize, woof_prize = await dogs.get_previous_round_vote()
            if is_win is not None:
                logger.info(f"Thread {thread} | {account} | {'Won' if is_win else 'Lost'} in vote round! Not prize: {not_prize}; Woof prize: {woof_prize}")

        except Exception as e:
            logger.error(f"Thread {thread} | {account} | Error: {e}")
            await asyncio.sleep(2)

    await dogs.logout()

async def stats():
    accounts = await Accounts().get_accounts()

    tasks = []
    for thread, account in enumerate(accounts):
        session_name, phone_number, proxy = account.values()
        tasks.append(asyncio.create_task(LostDogs(session_name=session_name, phone_number=phone_number, thread=thread, proxy=proxy).stats()))

    data = await asyncio.gather(*tasks)
    path = f"statistics/statistics_{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.csv"
    columns = ['Phone number', 'Name', 'BONES', 'WOOF', 'Referrals', 'Referral link', 'Proxy (login:password@ip:port)']

    if not os.path.exists('statistics'): os.mkdir('statistics')
    df = pd.DataFrame(data, columns=columns)
    df.to_csv(path, index=False, encoding='utf-8-sig')

    logger.success(f"Saved statistics to {path}")
