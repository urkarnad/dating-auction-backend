from abc import ABC, abstractmethod
from typing import Optional
import aiohttp
import asyncio
from django.conf import settings
from asgiref.sync import sync_to_async
import logging

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
                        logger.info(f"Discord notification sent to {recipient}")
                        return True
                    else:
                        logger.warning(f"Discord notification failed with status {response.status}")
                        return False

        except aiohttp.ClientConnectorError:
            logger.error(f"Discord bot server unavailable for {recipient}")
            return False
        except asyncio.TimeoutError:
            logger.error(f"Discord notification timeout for {recipient}")
            return False
        except Exception as e:
            logger.error(f"Discord notification error: {e}")
            return False

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

    async def notify_bid_overbid(self, previous_bid, new_bid, lot) -> bool:
        # Wrap Django ORM access in sync_to_async
        previous_bidder = await sync_to_async(lambda: previous_bid.user)()
        enabled_channels = self.get_enabled_channels(previous_bidder)

        if not enabled_channels:
            logger.info(f"No notification channels enabled for user {previous_bidder.id}")
            return False

        message = await self._format_overbid_message(previous_bid, new_bid, lot)

        channel_name = enabled_channels[0]
        channel = self.channels[channel_name]

        recipient = channel.get_recipient_id(previous_bidder)
        if not recipient:
            logger.warning(f"No recipient ID for channel {channel_name}")
            return False

        lot_id = await sync_to_async(lambda: lot.id)()

        success = await channel.send(
            recipient=recipient,
            message=message,
            lot_id=lot_id
        )

        return success

    async def _format_overbid_message(self, previous_bid, new_bid, lot) -> str:
        # Wrap all Django ORM access
        prev_amount = await sync_to_async(lambda: previous_bid.amount)()
        new_amount = await sync_to_async(lambda: new_bid.amount)()
        new_bidder_first_name = await sync_to_async(lambda: new_bid.user.first_name)()
        new_bidder_last_name = await sync_to_async(lambda: new_bid.user.last_name)()
        new_bidder = f'{new_bidder_first_name} {new_bidder_last_name}'.strip()

        first_name = await sync_to_async(lambda: lot.user.first_name)()
        last_name = await sync_to_async(lambda: lot.user.last_name)()
        lot_name = f"{first_name} {last_name}".strip()

        if not lot_name:
            lot_name = ""

        message = (
            f"Твоя ставка в {prev_amount} грн на лот {lot_name} була перебита!\n\n"
            f"Нова ставка: {new_amount} грн\n"
            f"Поставлена: {new_bidder}"
        )

        return message

    def notify_bid_overbid_sync(self, previous_bid, new_bid, lot) -> bool:
        import asyncio

        # Create new event loop for this thread
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.notify_bid_overbid(previous_bid, new_bid, lot)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error in notify_bid_overbid_sync: {e}")
            return False

notification_service = NotificationService()