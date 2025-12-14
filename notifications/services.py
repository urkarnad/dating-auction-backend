import asyncio
import logging
from typing import Optional

import aiohttp
from abc import ABC, abstractmethod
from asgiref.sync import async_to_sync

from DatingAuction import settings


logger = logging.getLogger(__name__)


class NotificationChannel(ABC):
    @abstractmethod
    async def send(self, recipient: str, message: str, **kwargs) -> bool:
        pass

    @abstractmethod
    def is_enabled_for_user(self, user) -> bool:
        pass

    @abstractmethod
    def get_recipient_id(self, user) -> Optional[str]:
        pass


class DiscordChannel(NotificationChannel):
    def __init__(self):
        self.bot_url = getattr(settings, 'DISCORD_BOT_URL', 'http://localhost:5005')

    async def send(self, recipient: str, message: str, **kwargs) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=5)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f'{self.bot_url}/notify',
                    json={
                        'discord_id': recipient,
                        'message': message,
                        **kwargs
                    }
                ) as response:
                    if response.status == 200:
                        logger.info(f'Sent notification to {recipient}')
                        return True
                    else:
                        logger.warning(f'Failed to send notification to {recipient}')
                        return False

        except aiohttp.ClientConnectionError:
            logger.error(f'Discord bot server unavailable for {recipient}')
            return False
        except asyncio.TimeoutError:
            logger.error(f'Discord notification timeout for {recipient}')
            return False
        except Exception as e:
            logger.error(f'Discord notification error: {e}')

    def is_enabled_for_user(self, user) -> bool:
        return bool(getattr(user, 'discord_id', None))

    def get_recipient_id(self, user) -> Optional[str]:
        return getattr(user, 'discord_id', None)


class NotificationService:
    def __init__(self):
        self.channels = {'discord': DiscordChannel()}

    def get_enabled_channels(self, user):
        return [
            name for name, channel in self.channels.items()
            if channel.is_enabled_for_user(user)
        ]

    def format_overbid_message(self, new_bid, lot) -> str:
        message = (
            f'Ваша ставка на лот {lot.user.first_name} {lot.user.last_name} була перебита!\n\n'
            f'Нова ставка в {new_bid.amount} грн була зроблена користувачем {new_bid.user.first_name} {new_bid.user.last_name}'
        )
        return message

    async def notify_bid_overbid(self, previous_bid, new_bid, lot) -> bool:
        previous_bidder = previous_bid.user
        enabled_channels = self.get_enabled_channels(previous_bidder)

        if not enabled_channels:
            logger.info(f'No enabled channels for {previous_bidder}')
            return False

        message = self.format_overbid_message(previous_bid, new_bid, lot)

        channel_name = enabled_channels[0]
        channel = self.channels[channel_name]

        recipient = channel.get_recipient_id(previous_bidder)
        if not recipient:
            logger.warning(f'No recipient for channel {channel_name}')
            return False

        success = await channel.send(recipient=recipient, message=message, lot_id=lot.id)

        return success

    def notify_bid_overbid_sync(self, previous_bid, new_bid, lot) -> bool:
        return async_to_sync(self.notify_bid_overbid)(previous_bid, new_bid, lot)

notification_service = NotificationService()
