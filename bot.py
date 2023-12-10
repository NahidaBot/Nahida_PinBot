import os
import json
import logging
import subprocess

import telegram
from telegram import Update, BotCommand, Message
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

from config import config


logger = logging.getLogger(__name__)

restart_data = os.path.join(os.getcwd(), "restart.json")

if config.debug:
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.DEBUG,
    )
    # set higher logging level for httpx to avoid all GET and POST requests being logged
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(rf"Hi {user.mention_html()}!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(config.txt_help, parse_mode=ParseMode.HTML)


async def set_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id not in config.bot_admin_chats:
        return await permission_denied(update.message)

    commands = [
        BotCommand("help", "帮助"),
        BotCommand("pin", "回复一条消息，置顶该消息"),
        BotCommand("unpin", "回复一条消息，取消置顶该消息"),
    ]

    r = await context.bot.set_my_commands(commands)
    await update.message.reply_text(str(r))

async def permission_denied(message: telegram.Message) -> None:
    # TODO 鉴权这块可以改成装饰器实现
    await message.reply_text("Permission denied")


# 定义一个异步的初始化函数
async def on_start(application: Application):
    await restore_from_restart()


async def restart(
    update: Update, context: ContextTypes.DEFAULT_TYPE, update_msg: str = ""
) -> None:
    if update.message.chat_id not in config.bot_admin_chats:
        return await permission_denied(update.message)
    msg = await update.message.reply_text(update_msg + "Restarting...")
    with open(restart_data, "w", encoding="utf-8") as f:
        f.write(msg.to_json())
    application.stop_running()


async def restore_from_restart() -> None:
    if os.path.exists(restart_data):
        with open(restart_data) as f:
            msg: Message = Message.de_json(json.load(f), bot)
            await msg.edit_text("Restart success!")
        os.remove(restart_data)


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id not in config.bot_admin_chats:
        return await permission_denied(update.message)
    try:
        command = ["git", "pull"]
        # 使用subprocess执行命令
        result: subprocess.CompletedProcess = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        logger.debug(result.stdout)
        logger.debug("更新成功！")
    except subprocess.CalledProcessError as e:
        logger.error("更新出错:" + e)
        return await update.message.reply_text("Update failed! Please check logs.")
    await restart(update, context, "Update success! ")

async def pin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message:
        return await update.message.reply_text("请回复一条消息！")
    success = await update.message.reply_to_message.pin(disable_notification=True)
    if not success:
        return await update.message.reply_text("呜呜呜，出错啦！请查看日志！")
    await update.message.delete()


async def unpin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message.reply_to_message:
        return await update.message.reply_text("请回复一条消息！")
    success = await update.message.reply_to_message.unpin()
    if not success:
        return await update.message.reply_text("呜呜呜，出错啦！请查看日志！")
    await update.message.delete()

def main() -> None:
    """Start the bot."""
    global application
    application = (
        Application.builder().token(config.bot_token).post_init(on_start).build()
    )

    global bot
    bot = application.bot_data

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("set_commands", set_commands))
    application.add_handler(CommandHandler("update", update))
    application.add_handler(CommandHandler("restart", restart))
    application.add_handler(CommandHandler("pin", pin))
    application.add_handler(CommandHandler("unpin", unpin))

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
