from random import SystemRandom
from string import ascii_letters, digits
from telegram.ext import CommandHandler
from threading import Thread
from time import time, sleep

from bot import LOG_CHAT, LOG_CHAT_URL
from bot.helper.mirror_utils.upload_utils.gdriveTools import GoogleDriveHelper
from bot.helper.telegram_helper.message_utils import sendMessage, sendPrivateMarkup, sendMarkup, deleteMessage, delete_all_messages, update_all_messages, sendStatusMessage
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.mirror_utils.status_utils.clone_status import CloneStatus
from bot import dispatcher, LOGGER, STOP_DUPLICATE, download_dict, download_dict_lock, Interval
from bot.helper.ext_utils.bot_utils import *
from bot.helper.mirror_utils.download_utils.direct_link_generator import *
from bot.helper.ext_utils.exceptions import DirectDownloadLinkException


def _clone(message, bot, multi=0):
	elapsed_time = time()
    args = message.text.split(maxsplit=1)
    reply_to = message.reply_to_message
    link = ''
    if len(args) > 1:
        link = args[1].strip()
        if link.isdigit():
            multi = int(link)
            link = ''
        elif message.from_user.username:
            tag = f"@{message.from_user.username}"
        else:
            tag = message.from_user.mention_html(message.from_user.first_name)
    if reply_to:
        if len(link) == 0:
            link = reply_to.text.strip()
        if reply_to.from_user.username:
            tag = f"@{reply_to.from_user.username}"
        else:
            tag = reply_to.from_user.mention_html(reply_to.from_user.first_name)
    is_gdtot = is_gdtot_link(link)
    is_unified = is_unified_link(link)
    is_udrive = is_udrive_link(link)
    is_sharer = is_sharer_link(link)
    is_drivehubs = is_drivehubs_link(link)
    if (is_gdtot or is_unified or is_udrive or is_sharer or is_drivehubs):
    if is_gdtot:
        try:
            msg = sendMessage(f"<b>Processing:</b> <code>{link}</code>", bot, message)
            LOGGER.info(f"Processing: {link}")
            if is_unified:
                link = unified(link)
            if is_gdtot:
                link = gdtot(link)
            if is_udrive:
                link = udrive(link)
            if is_sharer:
                link = sharer_pw_dl(link)
            if is_drivehubs:
                link = drivehubs(link)
            deleteMessage(bot, msg)
        except DirectDownloadLinkException as e:
            deleteMessage(bot, msg)
            return sendMessage(str(e), bot, message)
    if is_gdrive_link(link):
        gd = GoogleDriveHelper()
        res, size, name, files = gd.helper(link)
        if res != "":
            return sendMessage(res, bot, message)
        if STOP_DUPLICATE:
            LOGGER.info('Checking File/Folder if already in Drive...')
            smsg, button = gd.drive_list(name, True, True)
            if smsg:
                msg3 = "File/Folder is already available in Drive.\nHere are the search results:"
                return sendMarkup(msg3, bot, message, button)
        if multi > 1:
            sleep(4)
            nextmsg = type('nextmsg', (object, ), {'chat_id': message.chat_id, 'message_id': message.reply_to_message.message_id + 1})
            nextmsg = sendMessage(args[0], bot, nextmsg)
            nextmsg.from_user.id = message.from_user.id
            multi -= 1
            sleep(4)
            Thread(target=_clone, args=(nextmsg, bot, multi)).start()
        if files <= 20:
            msg = sendMessage(f"Cloning: <code>{link}</code>", bot, message)
            result, button = gd.clone(link)
            deleteMessage(bot, msg)
        else:
            drive = GoogleDriveHelper(name)
            gid = ''.join(SystemRandom().choices(ascii_letters + digits, k=12))
            clone_status = CloneStatus(drive, size, message, gid)
            with download_dict_lock:
                download_dict[message.message_id] = clone_status
            sendStatusMessage(message, bot)
            result, button = drive.clone(link)
            with download_dict_lock:
                del download_dict[message.message_id]
                count = len(download_dict)
            try:
                if count == 0:
                    Interval[0].cancel()
                    del Interval[0]
                    delete_all_messages()
                else:
                    update_all_messages()
            except IndexError:
                pass
        cc = f"\n\n<b>Elapsed Time:</b> {get_readable_time(time() - elapsed_time)}"
        cc += f'\n\n<b>#Cloned For: </b>{tag}'
        pmsg = '\n\nI Hᴀᴠᴇ Sᴇɴᴛ Yᴏᴜʀ Lɪɴᴋs Iɴ PM'
        if button in ["cancelled", ""]:
            sendMessage(f"{tag} {result}", bot, message)
        else:
            fmsg = sendPrivateMarkup(result + cc, bot, message, button)
            if LOG_CHAT:
                fmsg.copy(chat_id=LOG_CHAT, reply_markup=button)
                pmsg += f'I Have Sent Links in <a href='{LOG_CHAT_URL}'>Logs Channel</a>'
            sendMessage(result + cc + pmsg, bot, message)
            LOGGER.info(f'Cloning Done: {name}')
        if is_gdtot:
            gd.deletefile(link)
    else:
        sendMessage('Send Gdrive or GDToT/AppDrive/DriveApp/GDFlix/DriveAce/DriveLinks/DriveBit/DriveSharer/Anidrive/Driveroot/Driveflix/Indidrive/drivehub(in)/HubDrive/DriveHub(ws)/KatDrive/Kolop/DriveFire/DriveBuzz/SharerPw Link along with command or by replying to the link by command", bot, message)
', bot, message)

@new_thread
def cloneNode(update, context):
    _clone(update.message, context.bot)

clone_handler = CommandHandler(BotCommands.CloneCommand, cloneNode, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
dispatcher.add_handler(clone_handler)
