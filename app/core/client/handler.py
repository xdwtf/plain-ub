import asyncio
import traceback

from pyrogram.types import Message as Msg

from app import Config, bot
from app.core import Message, filters


@bot.on_message(filters.owner_filter | filters.sudo_filter, group=1)
@bot.on_edited_message(filters.owner_filter | filters.sudo_filter, group=1)
async def cmd_dispatcher(bot, message) -> None:
    message = Message.parse_message(message)
    func = Config.CMD_DICT[message.cmd]
    coro = func(bot, message)
    x = await run_coro(coro, message)
    if not x and message.is_from_owner:
        await message.delete()


@bot.on_message(filters.convo_filter, group=0)
@bot.on_edited_message(filters.convo_filter, group=0)
async def convo_handler(bot: bot, message: Msg):
    conv_dict: dict = Config.CONVO_DICT[message.chat.id]
    conv_filters = conv_dict.get("filters")
    if conv_filters:
        check = await conv_filters(bot, message)
        if not check:
            message.continue_propagation()
        conv_dict["response"] = message
        message.continue_propagation()
    conv_dict["response"] = message
    message.continue_propagation()


async def run_coro(coro, message) -> None | int:
    try:
        task = asyncio.Task(coro, name=message.task_id)
        await task
    except asyncio.exceptions.CancelledError:
        await bot.log(text=f"<b>#Cancelled</b>:\n<code>{message.text}</code>")
    except BaseException:
        await bot.log(
            traceback=f"<pre language=python>{traceback.format_exc()}</pre>",
            chat=message.chat.title or message.chat.first_name,
            func=coro.__name__,
            name="traceback.txt",
        )
        return 1
