#!/usr/bin/env python3
from random import choice
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.filters import command, regex, create
from pyrogram.enums import ChatType
from functools import partial
from collections import OrderedDict
from asyncio import create_subprocess_exec, create_subprocess_shell, sleep, gather
from aiofiles.os import remove, rename, path as aiopath
from aiofiles import open as aiopen
from os import environ, getcwd
from dotenv import load_dotenv
import json
from time import time
from io import BytesIO
from aioshutil import rmtree as aiormtree

from bot import config_dict, user_data, DATABASE_URL, MAX_SPLIT_SIZE, list_drives_dict, categories_dict, GLOBAL_EXTENSION_FILTER, status_reply_dict_lock, Interval, IS_PREMIUM_USER, download_dict, qbit_options, get_client, LOGGER, bot, extra_buttons, shorteners_list
from bot.helper.telegram_helper.message_utils import sendMessage, sendFile, editMessage, deleteMessage, update_all_messages
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.button_build import ButtonMaker
from bot.helper.ext_utils.bot_utils import setInterval, sync_to_async, new_thread
from bot.helper.ext_utils.db_handler import DbManger
from bot.helper.ext_utils.task_manager import start_from_queued
from bot.helper.ext_utils.help_messages import default_desp
from bot.helper.mirror_utils.rclone_utils.serve import rclone_serve_booter
from bot.modules.torrent_search import initiate_search_tools
from bot.modules.rss import addJob
from bot.helper.themes import AVL_THEMES

START = 0
STATE = 'view'
handler_dict = {}
default_values = {'AUTO_DELETE_MESSAGE_DURATION': 30,
                  'DEFAULT_UPLOAD': 'gd',
                  'DOWNLOAD_DIR': '/usr/src/app/downloads/',
                  'LEECH_SPLIT_SIZE': MAX_SPLIT_SIZE,
                  'RSS_DELAY': 600,
                  'STATUS_UPDATE_INTERVAL': 2,
                  'SEARCH_LIMIT': 0,
                  'UPSTREAM_BRANCH': 'update',
                  'BOT_THEME': 'minimal',
                  'BOT_LANG': 'en',
                  'IMG_PAGE': 1,
                  'AUTHOR_NAME': 'ʀᴀʀᴇ ʙᴏᴛꜱ ʜᴜʙ',
                  'AUTHOR_URL': 'https://t.me/Rare_Bots_Hub',
                  'TITLE_NAME': 'ʀᴀʀᴇ ʙᴏᴛꜱ ʜᴜʙ',
                  'GD_INFO': 'Uploaded by Rare Leech Bot',
                  'GD_DESP': 'Uploaded with WZ Bot',
                  'YT_DESP': 'Uploaded to YouTube by WZML-X bot',
                  'YT_CATEGORY_ID': 22,
                  'YT_PRIVACY_STATUS': 'unlisted',
                  'RSS_DELAY': 600,
                  }
bool_vars = ['AS_DOCUMENT', 'BOT_PM', 'STOP_DUPLICATE', 'SET_COMMANDS', 'SAVE_MSG', 'SHOW_MEDIAINFO', 'SOURCE_LINK', 'SAFE_MODE', 'SHOW_EXTRA_CMDS',
             'IS_TEAM_DRIVE', 'USE_SERVICE_ACCOUNTS', 'WEB_PINCODE', 'EQUAL_SPLITS', 'DISABLE_DRIVE_LINK', 'DELETE_LINKS', 'CLEAN_LOG_MSG', 'USER_TD_MODE', 
             'INCOMPLETE_TASK_NOTIFIER', 'UPGRADE_PACKAGES', 'SCREENSHOTS_MODE', 'MEDIA_STORE', 'DISABLE_MEGA', 'DISABLE_TORRENTS', 'DISABLE_LEECH',
             'DISABLE_BULK', 'DISABLE_MULTI', 'DISABLE_SEED', 'DISABLE_FF_MODE', 'USE_IMAGES', 'UPDATE_PKGS', 'SHOW_CLOUD_LINK',
             'USER_TRANSMISSION', 'HYBRID_LEECH']


async def load_config():

    BOT_TOKEN = environ.get('BOT_TOKEN', '')
    if len(BOT_TOKEN) == 0:
        BOT_TOKEN = config_dict['BOT_TOKEN']

    TELEGRAM_API = environ.get('TELEGRAM_API', '')
    if len(TELEGRAM_API) == 0:
        TELEGRAM_API = config_dict['TELEGRAM_API']
    else:
        TELEGRAM_API = int(TELEGRAM_API)

    TELEGRAM_HASH = environ.get('TELEGRAM_HASH', '')
    if len(TELEGRAM_HASH) == 0:
        TELEGRAM_HASH = config_dict['TELEGRAM_HASH']

    BOT_MAX_TASKS = environ.get('BOT_MAX_TASKS', '')
    BOT_MAX_TASKS = int(BOT_MAX_TASKS) if BOT_MAX_TASKS.isdigit() else ''
    
    OWNER_ID = environ.get('OWNER_ID', '')
    OWNER_ID = config_dict['OWNER_ID'] if len(OWNER_ID) == 0 else int(OWNER_ID)

    DATABASE_URL = environ.get('DATABASE_URL', '')
    if len(DATABASE_URL) == 0:
        DATABASE_URL = ''

    DOWNLOAD_DIR = environ.get('DOWNLOAD_DIR', '')
    if len(DOWNLOAD_DIR) == 0:
        DOWNLOAD_DIR = '/usr/src/app/downloads/'
    elif not DOWNLOAD_DIR.endswith("/"):
        DOWNLOAD_DIR = f'{DOWNLOAD_DIR}/'

    GDRIVE_ID = environ.get('GDRIVE_ID', '')
    if len(GDRIVE_ID) == 0:
        GDRIVE_ID = ''

    RCLONE_PATH = environ.get('RCLONE_PATH', '')
    if len(RCLONE_PATH) == 0:
        RCLONE_PATH = ''

    DEFAULT_UPLOAD = environ.get('DEFAULT_UPLOAD', '')
    if DEFAULT_UPLOAD != 'rc' and DEFAULT_UPLOAD != 'ddl':
        DEFAULT_UPLOAD = 'gd'

    DEFAULT_LANG = environ.get('DEFAULT_LANG', 'en')

    TG_PROXY = environ.get('TG_PROXY', '')
    if len(TG_PROXY) > 0:
        try:
            TG_PROXY = json.loads(TG_PROXY)
        except Exception as e:
            LOGGER.error(f"TG_PROXY error: {e}")
            TG_PROXY = {}
    else:
        TG_PROXY = {}

    RCLONE_FLAGS = environ.get('RCLONE_FLAGS', '')
    if len(RCLONE_FLAGS) == 0:
        RCLONE_FLAGS = ''

    AUTHORIZED_CHATS = environ.get('AUTHORIZED_CHATS', '')
    if len(AUTHORIZED_CHATS) != 0:
        aid = AUTHORIZED_CHATS.split()
        for id_ in aid:
            chat_id, *topic_ids = id_.split(':')
            chat_id = int(chat_id)
            user_data.setdefault(chat_id, {'is_auth': True})
            if topic_ids:
                user_data[chat_id].setdefault('topic_ids', []).extend(map(int, topic_ids))

    SUDO_USERS = environ.get('SUDO_USERS', '')
    if len(SUDO_USERS) != 0:
        aid = SUDO_USERS.split()
        for id_ in aid:
            user_data[int(id_.strip())] = {'is_sudo': True}
            
    BLACKLIST_USERS = environ.get('BLACKLIST_USERS', '')
    if len(BLACKLIST_USERS) != 0:
        aid = BLACKLIST_USERS.split()
        for id_ in aid:
            user_data[int(id_.strip())] = {'is_blacklist': True}

    EXTENSION_FILTER = environ.get('EXTENSION_FILTER', '')
    if len(EXTENSION_FILTER) > 0:
        fx = EXTENSION_FILTER.split()
        GLOBAL_EXTENSION_FILTER.clear()
        GLOBAL_EXTENSION_FILTER.extend(['!qB'])
        for x in fx:
            x = x.lstrip('.')
            GLOBAL_EXTENSION_FILTER.append(x.strip().lower())

    MEGA_EMAIL = environ.get('MEGA_EMAIL', '')
    MEGA_PASSWORD = environ.get('MEGA_PASSWORD', '')
    if len(MEGA_EMAIL) == 0 or len(MEGA_PASSWORD) == 0:
        MEGA_EMAIL = ''
        MEGA_PASSWORD = ''

    METADATA = environ.get('METADATA', '')
    if len(METADATA) == 0:
        METADATA = ''

    ATTACHMENT = environ.get('ATTACHMENT', '')
    if len(ATTACHMENT) == 0:
        ATTACHMENT = ''
      
    GDTOT_CRYPT = environ.get('GDTOT_CRYPT', '')
    if len(GDTOT_CRYPT) == 0:
        GDTOT_CRYPT = ''
        
    REAL_DEBRID_API = environ.get('REAL_DEBRID_API', '')
    if len(REAL_DEBRID_API) == 0:
        REAL_DEBRID_API = ''
        
    DEBRID_LINK_API = environ.get('DEBRID_LINK_API', '')
    if len(DEBRID_LINK_API) == 0:
        DEBRID_LINK_API = ''

    INDEX_URL = environ.get('INDEX_URL', '').rstrip("/")
    if len(INDEX_URL) == 0:
        INDEX_URL = ''

    SEARCH_API_LINK = environ.get('SEARCH_API_LINK', '').rstrip("/")
    if len(SEARCH_API_LINK) == 0:
        SEARCH_API_LINK = ''

    CAP_FONT = environ.get('CAP_FONT', '').lower()
    if CAP_FONT.strip() not in ['', 'b', 'i', 'u', 's', 'spoiler', 'code']:
        CAP_FONT = 'b'
        
    LEECH_FILENAME_PREFIX = environ.get('LEECH_FILENAME_PREFIX', '')
    if len(LEECH_FILENAME_PREFIX) == 0:
        LEECH_FILENAME_PREFIX = ''

    LEECH_FILENAME_SUFFIX = environ.get('LEECH_FILENAME_SUFFIX', '')
    if len(LEECH_FILENAME_SUFFIX) == 0:
        LEECH_FILENAME_SUFFIX = ''

    LEECH_FILENAME_CAPTION = environ.get('LEECH_FILENAME_CAPTION', '')
    if len(LEECH_FILENAME_CAPTION) == 0:
        LEECH_FILENAME_CAPTION = ''

    LEECH_FILENAME_REMNAME = environ.get('LEECH_FILENAME_REMNAME', '')
    if len(LEECH_FILENAME_REMNAME) == 0:
        LEECH_FILENAME_REMNAME = ''

    MIRROR_FILENAME_PREFIX = environ.get('MIRROR_FILENAME_PREFIX', '')
    if len(MIRROR_FILENAME_PREFIX) == 0:
        MIRROR_FILENAME_PREFIX = ''

    MIRROR_FILENAME_SUFFIX = environ.get('MIRROR_FILENAME_SUFFIX', '')
    if len(MIRROR_FILENAME_SUFFIX) == 0:
        MIRROR_FILENAME_SUFFIX = ''

    MIRROR_FILENAME_REMNAME = environ.get('MIRROR_FILENAME_REMNAME', '')
    if len(MIRROR_FILENAME_REMNAME) == 0:
        MIRROR_FILENAME_REMNAME = ''
        
    SEARCH_PLUGINS = environ.get('SEARCH_PLUGINS', '')
    if len(SEARCH_PLUGINS) == 0:
        SEARCH_PLUGINS = ''

    MAX_SPLIT_SIZE = 4194304000 if IS_PREMIUM_USER else 2097152000

    LEECH_SPLIT_SIZE = environ.get('LEECH_SPLIT_SIZE', '')
    if len(LEECH_SPLIT_SIZE) == 0 or int(LEECH_SPLIT_SIZE) > MAX_SPLIT_SIZE:
        LEECH_SPLIT_SIZE = MAX_SPLIT_SIZE
    else:
        LEECH_SPLIT_SIZE = int(LEECH_SPLIT_SIZE)

    STATUS_UPDATE_INTERVAL = environ.get('STATUS_UPDATE_INTERVAL', '')
    if len(STATUS_UPDATE_INTERVAL) == 0:
        STATUS_UPDATE_INTERVAL = 2
    else:
        STATUS_UPDATE_INTERVAL = int(STATUS_UPDATE_INTERVAL)
    if len(download_dict) != 0:
        async with status_reply_dict_lock:
            if Interval:
                Interval[0].cancel()
                Interval.clear()
                Interval.append(setInterval(STATUS_UPDATE_INTERVAL, update_all_messages))

    AUTO_DELETE_MESSAGE_DURATION = environ.get(
        'AUTO_DELETE_MESSAGE_DURATION', '')
    if len(AUTO_DELETE_MESSAGE_DURATION) == 0:
        AUTO_DELETE_MESSAGE_DURATION = 30
    else:
        AUTO_DELETE_MESSAGE_DURATION = int(AUTO_DELETE_MESSAGE_DURATION)

    YT_DLP_OPTIONS = environ.get('YT_DLP_OPTIONS', '')
    if len(YT_DLP_OPTIONS) == 0:
        YT_DLP_OPTIONS = ''

    SEARCH_LIMIT = environ.get('SEARCH_LIMIT', '')
    SEARCH_LIMIT = 0 if len(SEARCH_LIMIT) == 0 else int(SEARCH_LIMIT)

    STATUS_LIMIT = environ.get('STATUS_LIMIT', '')
    STATUS_LIMIT = 10 if len(STATUS_LIMIT) == 0 else int(STATUS_LIMIT)

    RSS_CHAT = environ.get('RSS_CHAT', '')
    RSS_CHAT = '' if len(RSS_CHAT) == 0 else int(RSS_CHAT)

    RSS_DELAY = environ.get('RSS_DELAY', '')
    RSS_DELAY = 600 if len(RSS_DELAY) == 0 else int(RSS_DELAY)

    RSS_SIZE_LIMIT = environ.get('RSS_SIZE_LIMIT', '')
    RSS_SIZE_LIMIT = 0 if len(RSS_SIZE_LIMIT) == 0 else int(RSS_SIZE_LIMIT)

    CMD_SUFFIX = environ.get('CMD_SUFFIX', '')

    USER_SESSION_STRING = environ.get('USER_SESSION_STRING', '')

    TORRENT_TIMEOUT = environ.get('TORRENT_TIMEOUT', '')
    if len(TORRENT_TIMEOUT) == 0:
        TORRENT_TIMEOUT = ''
    else:
        TORRENT_TIMEOUT = int(TORRENT_TIMEOUT)

    QUEUE_ALL = environ.get('QUEUE_ALL', '')
    QUEUE_ALL = '' if len(QUEUE_ALL) == 0 else int(QUEUE_ALL)

    QUEUE_DOWNLOAD = environ.get('QUEUE_DOWNLOAD', '')
    QUEUE_DOWNLOAD = '' if len(QUEUE_DOWNLOAD) == 0 else int(QUEUE_DOWNLOAD)

    QUEUE_UPLOAD = environ.get('QUEUE_UPLOAD', '')
    QUEUE_UPLOAD = '' if len(QUEUE_UPLOAD) == 0 else int(QUEUE_UPLOAD)

    INCOMPLETE_TASK_NOTIFIER = environ.get('INCOMPLETE_TASK_NOTIFIER', '')
    INCOMPLETE_TASK_NOTIFIER = INCOMPLETE_TASK_NOTIFIER.lower() == 'true'
    if not INCOMPLETE_TASK_NOTIFIER and DATABASE_URL:
        await DbManger().trunc_table('tasks')

    STOP_DUPLICATE = environ.get('STOP_DUPLICATE', '')
    STOP_DUPLICATE = STOP_DUPLICATE.lower() == 'true'

    IS_TEAM_DRIVE = environ.get('IS_TEAM_DRIVE', '')
    IS_TEAM_DRIVE = IS_TEAM_DRIVE.lower() == 'true'

    USE_SERVICE_ACCOUNTS = environ.get('USE_SERVICE_ACCOUNTS', '')
    USE_SERVICE_ACCOUNTS = USE_SERVICE_ACCOUNTS.lower() == 'true'

    WEB_PINCODE = environ.get('WEB_PINCODE', '')
    WEB_PINCODE = WEB_PINCODE.lower() == 'true'

    AS_DOCUMENT = environ.get('AS_DOCUMENT', 'true')
    AS_DOCUMENT = AS_DOCUMENT.lower() == 'true'
    
    USER_TD_MODE = environ.get('USER_TD_MODE', '')
    USER_TD_MODE = USER_TD_MODE.lower() == 'true'

    USER_TD_SA = environ.get('USER_TD_SA', '')
    USER_TD_SA = USER_TD_SA.lower() if len(USER_TD_SA) != 0 else ''

    SHOW_MEDIAINFO = environ.get('SHOW_MEDIAINFO', '')
    SHOW_MEDIAINFO = SHOW_MEDIAINFO.lower() == 'true'
    
    SOURCE_LINK = environ.get('SOURCE_LINK', '')
    SOURCE_LINK = SOURCE_LINK.lower() == 'true'

    DELETE_LINKS = environ.get('DELETE_LINKS', '')
    DELETE_LINKS = DELETE_LINKS.lower() == 'true'

    EQUAL_SPLITS = environ.get('EQUAL_SPLITS', '')
    EQUAL_SPLITS = EQUAL_SPLITS.lower() == 'true'

    MEDIA_GROUP = environ.get('MEDIA_GROUP', '')
    MEDIA_GROUP = MEDIA_GROUP.lower() == 'true'

    BASE_URL_PORT = environ.get('BASE_URL_PORT', '')
    BASE_URL_PORT = 80 if len(BASE_URL_PORT) == 0 else int(BASE_URL_PORT)

    RCLONE_SERVE_URL = environ.get('RCLONE_SERVE_URL', '')
    if len(RCLONE_SERVE_URL) == 0:
        RCLONE_SERVE_URL = ''

    RCLONE_SERVE_PORT = environ.get('RCLONE_SERVE_PORT', '')
    RCLONE_SERVE_PORT = 8080 if len(
        RCLONE_SERVE_PORT) == 0 else int(RCLONE_SERVE_PORT)

    RCLONE_SERVE_USER = environ.get('RCLONE_SERVE_USER', '')
    if len(RCLONE_SERVE_USER) == 0:
        RCLONE_SERVE_USER = ''

    RCLONE_SERVE_PASS = environ.get('RCLONE_SERVE_PASS', '')
    if len(RCLONE_SERVE_PASS) == 0:
        RCLONE_SERVE_PASS = ''

    await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
    BASE_URL = environ.get('BASE_URL', '').rstrip("/")
    if len(BASE_URL) == 0:
        BASE_URL = ''
    else:
        await create_subprocess_shell(f"gunicorn web.wserver:app --bind 0.0.0.0:{BASE_URL_PORT} --worker-class gevent")

    UPSTREAM_REPO = environ.get('UPSTREAM_REPO', '')
    if len(UPSTREAM_REPO) == 0:
        UPSTREAM_REPO = 'https://github.com/Tamilupdates/KPSML-X'

    UPSTREAM_BRANCH = environ.get('UPSTREAM_BRANCH', '')
    if len(UPSTREAM_BRANCH) == 0:
        UPSTREAM_BRANCH = 'kpsmlx'

    UPGRADE_PACKAGES = environ.get('UPGRADE_PACKAGES', '')
    if len(UPGRADE_PACKAGES) == 0:
        UPGRADE_PACKAGES = environ.get('UPDATE_PKGS', '')
    UPGRADE_PACKAGES = UPGRADE_PACKAGES.lower() == 'true'

    STORAGE_THRESHOLD = environ.get('STORAGE_THRESHOLD', '')
    STORAGE_THRESHOLD = '' if len(
        STORAGE_THRESHOLD) == 0 else float(STORAGE_THRESHOLD)

    TORRENT_LIMIT = environ.get('TORRENT_LIMIT', '')
    TORRENT_LIMIT = '' if len(TORRENT_LIMIT) == 0 else float(TORRENT_LIMIT)

    DIRECT_LIMIT = environ.get('DIRECT_LIMIT', '')
    DIRECT_LIMIT = '' if len(DIRECT_LIMIT) == 0 else float(DIRECT_LIMIT)

    YTDLP_LIMIT = environ.get('YTDLP_LIMIT', '')
    YTDLP_LIMIT = '' if len(YTDLP_LIMIT) == 0 else float(YTDLP_LIMIT)

    GDRIVE_LIMIT = environ.get('GDRIVE_LIMIT', '')
    GDRIVE_LIMIT = '' if len(GDRIVE_LIMIT) == 0 else float(GDRIVE_LIMIT)

    CLONE_LIMIT = environ.get('CLONE_LIMIT', '')
    CLONE_LIMIT = '' if len(CLONE_LIMIT) == 0 else float(CLONE_LIMIT)

    MEGA_LIMIT = environ.get('MEGA_LIMIT', '')
    MEGA_LIMIT = '' if len(MEGA_LIMIT) == 0 else float(MEGA_LIMIT)

    LEECH_LIMIT = environ.get('LEECH_LIMIT', '')
    LEECH_LIMIT = '' if len(LEECH_LIMIT) == 0 else float(LEECH_LIMIT)

    FSUB_IDS = environ.get('FSUB_IDS', '')
    if len(FSUB_IDS) == 0:
        FSUB_IDS = ''
    
    LINKS_LOG_ID = environ.get('LINKS_LOG_ID', '')
    LINKS_LOG_ID = '' if len(LINKS_LOG_ID) == 0 else int(LINKS_LOG_ID)

    MIRROR_LOG_ID = environ.get('MIRROR_LOG_ID', '')
    if len(MIRROR_LOG_ID) == 0:
        MIRROR_LOG_ID = ''
        
    LEECH_LOG_ID = environ.get('LEECH_LOG_ID', '')

    EXCEP_CHATS = environ.get('EXCEP_CHATS', '')
    if len(EXCEP_CHATS) == 0:
        EXCEP_CHATS = ''

    USER_MAX_TASKS = environ.get('USER_MAX_TASKS', '')
    USER_MAX_TASKS = int(USER_MAX_TASKS) if USER_MAX_TASKS.isdigit() else ''

    USER_TIME_INTERVAL = environ.get('USER_TIME_INTERVAL', '')
    USER_TIME_INTERVAL = int(USER_TIME_INTERVAL) if USER_TIME_INTERVAL.isdigit() else 0

    PLAYLIST_LIMIT = environ.get('PLAYLIST_LIMIT', '')
    PLAYLIST_LIMIT = '' if len(PLAYLIST_LIMIT) == 0 else int(PLAYLIST_LIMIT)

    BOT_PM = environ.get('BOT_PM', 'true')
    BOT_PM = BOT_PM.lower() == 'true'

    DAILY_TASK_LIMIT = environ.get('DAILY_TASK_LIMIT', '')
    DAILY_TASK_LIMIT = '' if len(DAILY_TASK_LIMIT) == 0 else int(DAILY_TASK_LIMIT)

    DAILY_MIRROR_LIMIT = environ.get('DAILY_MIRROR_LIMIT', '')
    DAILY_MIRROR_LIMIT = '' if len(DAILY_MIRROR_LIMIT) == 0 else float(DAILY_MIRROR_LIMIT)

    DAILY_LEECH_LIMIT = environ.get('DAILY_LEECH_LIMIT', '')
    DAILY_LEECH_LIMIT = '' if len(DAILY_LEECH_LIMIT) == 0 else float(DAILY_LEECH_LIMIT)

    DISABLE_DRIVE_LINK = environ.get('DISABLE_DRIVE_LINK', '')
    DISABLE_DRIVE_LINK = DISABLE_DRIVE_LINK.lower() == 'true'

    BOT_THEME = environ.get('BOT_THEME', '')
    if len(BOT_THEME) == 0:
        BOT_THEME = 'minimal'

    IMG_SEARCH = environ.get('IMG_SEARCH', '')
    IMG_SEARCH = (IMG_SEARCH.replace("'", '').replace('"', '').replace('[', '').replace(']', '').replace(",", "")).split()
    
    IMG_PAGE = environ.get('IMG_PAGE', '')
    IMG_PAGE = int(IMG_PAGE) if IMG_PAGE.isdigit() else ''

    IMAGES = environ.get('IMAGES', '')
    IMAGES = (IMAGES.replace("'", '').replace('"', '').replace('[', '').replace(']', '').replace(",", "")).split()

    AUTHOR_NAME = environ.get('AUTHOR_NAME', '')
    if len(AUTHOR_NAME) == 0:
        AUTHOR_NAME = 'KPS Bots'

    AUTHOR_URL = environ.get('AUTHOR_URL', '')
    if len(AUTHOR_URL) == 0:
        AUTHOR_URL = 'https://telegram.me/KPSBots'

    TITLE_NAME = environ.get('TITLE_NAME', '')
    if len(TITLE_NAME) == 0:
        TITLE_NAME = 'KPSML-X Leech Bot'
        
    COVER_IMAGE = environ.get('COVER_IMAGE', '')
    if len(COVER_IMAGE) == 0:
        COVER_IMAGE = 'https://graph.org/file/0ff9d5e94a070fe4154c0.jpg'

    GD_INFO = environ.get('GD_INFO', '')
    if len(GD_INFO) == 0:
        GD_INFO = 'Uploaded by KPSML-X Leech Bot'

    GD_DESP = environ.get('GD_DESP', 'Uploaded with WZ Bot')
    if len(GD_DESP) == 0:
        GD_DESP = 'Uploaded with WZ Bot'

    SAVE_MSG = environ.get('SAVE_MSG', '')
    SAVE_MSG = SAVE_MSG.lower() == 'true'

    SET_COMMANDS = environ.get('SET_COMMANDS', '')
    SET_COMMANDS = SET_COMMANDS.lower() == 'true'
    
    SAFE_MODE = environ.get('SAFE_MODE', '')
    SAFE_MODE = SAFE_MODE.lower() == 'true'
    
    SCREENSHOTS_MODE = environ.get('SCREENSHOTS_MODE', '')
    SCREENSHOTS_MODE = SCREENSHOTS_MODE.lower() == 'true'

    CLEAN_LOG_MSG = environ.get('CLEAN_LOG_MSG', '')
    CLEAN_LOG_MSG = CLEAN_LOG_MSG.lower() == 'true'
    
    SHOW_EXTRA_CMDS = environ.get('SHOW_EXTRA_CMDS', '')
    SHOW_EXTRA_CMDS = SHOW_EXTRA_CMDS.lower() == 'true'
    
    TOKEN_TIMEOUT = environ.get('TOKEN_TIMEOUT', '')
    TOKEN_TIMEOUT = int(TOKEN_TIMEOUT) if TOKEN_TIMEOUT.isdigit() else ''

    LOGIN_PASS = environ.get('LOGIN_PASS', '')
    if len(LOGIN_PASS) == 0:
        LOGIN_PASS = None

    FILELION_API = environ.get('FILELION_API', '')
    if len(FILELION_API) == 0:
        FILELION_API = ''

    DEF_IMDB_TEMP  = environ.get('IMDB_TEMPLATE', '')
    if len(DEF_IMDB_TEMP) == 0:
        DEF_IMDB_TEMP = '''<b>Title: </b> {title} [{year}]
<b>Also Known As:</b> {aka}
<b>Rating ⭐️:</b> <i>{rating}</i>
<b>Release Info: </b> <a href="{url_releaseinfo}">{release_date}</a>
<b>Genre: </b>{genres}
<b>IMDb URL:</b> {url}
<b>Language: </b>{languages}
<b>Country of Origin : </b> {countries}

<b>Story Line: </b><code>{plot}</code>

<a href="{url_cast}">Read More ...</a>'''

    DEF_ANI_TEMP  = environ.get('ANIME_TEMPLATE', '')
    if len(DEF_ANI_TEMP) == 0:
        DEF_ANI_TEMP = '''<b>{ro_title}</b>({na_title})
<b>Format</b>: <code>{format}</code>
<b>Status</b>: <code>{status}</code>
<b>Start Date</b>: <code>{startdate}</code>
<b>End Date</b>: <code>{enddate}</code>
<b>Season</b>: <code>{season}</code>
<b>Country</b>: {country}
<b>Episodes</b>: <code>{episodes}</code>
<b>Duration</b>: <code>{duration}</code>
<b>Average Score</b>: <code>{avgscore}</code>
<b>Genres</b>: {genres}
<b>Hashtag</b>: {hashtag}
<b>Studios</b>: {studios}

<b>Description</b>: <i>{description}</i>'''

    MDL_TEMPLATE = environ.get('MDL_TEMPLATE', '')
    if len(MDL_TEMPLATE) == 0:
        MDL_TEMPLATE = '''<b>Title:</b> {title}
<b>Also Known As:</b> {aka}
<b>Rating ⭐️:</b> <i>{rating}</i>
<b>Release Info:</b> {aired_date}
<b>Genre:</b> {genres}
<b>MyDramaList URL:</b> {url}
<b>Language:</b> #Korean
<b>Country of Origin:</b> {country}

<b>Story Line:</b> {synopsis}

<a href='{url}'>Read More ...</a>'''
    
    TIMEZONE = environ.get('TIMEZONE', '')
    if len(TIMEZONE) == 0:
        TIMEZONE = 'Asia/Kolkata'

    FFMPEG_CMDS = environ.get('FFMPEG_CMDS', '')
    if len(FFMPEG_CMDS) > 0:
        try:
            FFMPEG_CMDS = json.loads(FFMPEG_CMDS)
        except Exception as e:
            LOGGER.error(f"FFMPEG_CMDS error: {e}")
            FFMPEG_CMDS = {}
    else:
        FFMPEG_CMDS = {}

    UPLOAD_PATHS = environ.get('UPLOAD_PATHS', '')
    if len(UPLOAD_PATHS) > 0:
        try:
            UPLOAD_PATHS = json.loads(UPLOAD_PATHS)
        except Exception as e:
            LOGGER.error(f"UPLOAD_PATHS error: {e}")
            UPLOAD_PATHS = {}
    else:
        UPLOAD_PATHS = {}

    NAME_SWAP = environ.get('NAME_SWAP', '')
    if len(NAME_SWAP) == 0:
        NAME_SWAP = ''

    WEB_ACCESS_PASSWORD = environ.get('WEB_ACCESS_PASSWORD', '')
    if len(WEB_ACCESS_PASSWORD) == 0:
        WEB_ACCESS_PASSWORD = ''

    DISABLE_MEGA = environ.get('DISABLE_MEGA', '')
    DISABLE_MEGA = DISABLE_MEGA.lower() == 'true'

    DISABLE_TORRENTS = environ.get('DISABLE_TORRENTS', '')
    DISABLE_TORRENTS = DISABLE_TORRENTS.lower() == 'true'

    DISABLE_LEECH = environ.get('DISABLE_LEECH', '')
    DISABLE_LEECH = DISABLE_LEECH.lower() == 'true'

    DISABLE_BULK = environ.get('DISABLE_BULK', '')
    DISABLE_BULK = DISABLE_BULK.lower() == 'true'

    DISABLE_MULTI = environ.get('DISABLE_MULTI', '')
    DISABLE_MULTI = DISABLE_MULTI.lower() == 'true'

    DISABLE_SEED = environ.get('DISABLE_SEED', '')
    DISABLE_SEED = DISABLE_SEED.lower() == 'true'

    DISABLE_FF_MODE = environ.get('DISABLE_FF_MODE', '')
    DISABLE_FF_MODE = DISABLE_FF_MODE.lower() == 'true'

    USE_IMAGES = environ.get('USE_IMAGES', '')
    USE_IMAGES = USE_IMAGES.lower() == 'true'

    IMG_SOURCES = environ.get('IMG_SOURCES', '')
    if len(IMG_SOURCES) > 0:
        try:
            IMG_SOURCES = json.loads(IMG_SOURCES)
        except Exception as e:
            LOGGER.error(f"IMG_SOURCES error: {e}")
            IMG_SOURCES = IMG_SOURCES.split()
    else:
        IMG_SOURCES = ["wallpaperflare"]

    MEDIA_STORE = environ.get('MEDIA_STORE', 'true')
    MEDIA_STORE = MEDIA_STORE.lower() == 'true'

    USER_TRANSMISSION = environ.get('USER_TRANSMISSION', 'true')
    USER_TRANSMISSION = USER_TRANSMISSION.lower() == 'true'

    HYBRID_LEECH = environ.get('HYBRID_LEECH', 'true')
    HYBRID_LEECH = HYBRID_LEECH.lower() == 'true'

    LEECH_FONT = environ.get('LEECH_FONT', '')
    if len(LEECH_FONT) == 0:
        LEECH_FONT = ''

    THUMBNAIL_LAYOUT = environ.get('THUMBNAIL_LAYOUT', '')
    if len(THUMBNAIL_LAYOUT) == 0:
        THUMBNAIL_LAYOUT = ''

    YT_DESP = environ.get('YT_DESP', 'Uploaded to YouTube by WZML-X bot')
    if len(YT_DESP) == 0:
        YT_DESP = 'Uploaded to YouTube by WZML-X bot'

    YT_TAGS = environ.get('YT_TAGS', '')
    if len(YT_TAGS) > 0:
        try:
            YT_TAGS = json.loads(YT_TAGS)
        except Exception as e:
            LOGGER.error(f"YT_TAGS error: {e}")
            YT_TAGS = [x.strip() for x in YT_TAGS.split(',')]
    else:
        YT_TAGS = ["telegram", "bot", "youtube"]

    YT_CATEGORY_ID = environ.get('YT_CATEGORY_ID', '')
    YT_CATEGORY_ID = int(YT_CATEGORY_ID) if YT_CATEGORY_ID.isdigit() else 22

    YT_PRIVACY_STATUS = environ.get('YT_PRIVACY_STATUS', 'unlisted')
    if len(YT_PRIVACY_STATUS) == 0:
        YT_PRIVACY_STATUS = 'unlisted'

    SHOW_CLOUD_LINK = environ.get('SHOW_CLOUD_LINK', 'true')
    SHOW_CLOUD_LINK = SHOW_CLOUD_LINK.lower() == 'true'

    list_drives_dict.clear()
    if GDRIVE_ID:
        list_drives_dict['Main'] = {"drive_id": GDRIVE_ID, "index_link": INDEX_URL}
        categories_dict['Root'] = {"drive_id": GDRIVE_ID, "index_link": INDEX_URL}

    if await aiopath.exists('list_drives.txt'):
        async with aiopen('list_drives.txt', 'r+') as f:
            lines = await f.readlines()
            for line in lines:
                sep = 2 if line.strip().split()[-1].startswith('http') else 1
                temp = line.strip().rsplit(maxsplit=sep)
                name = "Main Custom" if temp[0].casefold() == "Main" else temp[0]
                list_drives_dict[name] = {'drive_id': temp[1], 'index_link': (temp[2] if sep == 2 else '')}

    categories_dict.clear()
    if await aiopath.exists('categories.txt'):
        async with aiopen('categories.txt', 'r+') as f:
            lines = await f.readlines()
            for line in lines:
                sep = 2 if line.strip().split()[-1].startswith('http') else 1
                temp = line.strip().rsplit(maxsplit=sep)
                name = "Root Custom" if temp[0].casefold() == "Root" else temp[0]
                categories_dict[name] = {'drive_id': temp[1], 'index_link': (temp[2] if sep == 2 else '')}

    extra_buttons.clear()
    if await aiopath.exists('buttons.txt'):
        async with aiopen('buttons.txt', 'r+') as f:
            lines = await f.readlines()
            for line in lines:
                temp = line.strip().split()
                if len(extra_buttons.keys()) == 4:
                    break
                if len(temp) == 2:
                    extra_buttons[temp[0].replace("_", " ")] = temp[1]

    shorteners_list.clear()
    if await aiopath.exists('shorteners.txt'):
        async with aiopen('shorteners.txt', 'r+') as f:
            lines = await f.readlines()
            for line in lines:
                temp = line.strip().split()
                if len(temp) == 2:
                    shorteners_list.append({'domain': temp[0],'api_key': temp[1]})

    config_dict.update({'ANIME_TEMPLATE': DEF_ANI_TEMP,
                        'AS_DOCUMENT': AS_DOCUMENT,
                        'AUTHORIZED_CHATS': AUTHORIZED_CHATS,
                        'AUTO_DELETE_MESSAGE_DURATION': AUTO_DELETE_MESSAGE_DURATION,
                        'BASE_URL': BASE_URL,
                        'BASE_URL_PORT': BASE_URL_PORT,
                        'BLACKLIST_USERS': BLACKLIST_USERS,
                        'BOT_TOKEN': BOT_TOKEN,
                        'BOT_MAX_TASKS': BOT_MAX_TASKS,
                        'CAP_FONT': CAP_FONT,
                        'CMD_SUFFIX': CMD_SUFFIX,
                        'DATABASE_URL': DATABASE_URL,
                        'REAL_DEBRID_API': REAL_DEBRID_API,
                        'DEBRID_LINK_API': DEBRID_LINK_API,
                        'FILELION_API': FILELION_API,
                        'DELETE_LINKS': DELETE_LINKS,
                        'DEFAULT_UPLOAD': DEFAULT_UPLOAD,
                        'DEFAULT_LANG': DEFAULT_LANG,
                        'TG_PROXY': TG_PROXY,
                        'DOWNLOAD_DIR': DOWNLOAD_DIR,
                        'EXCEP_CHATS': EXCEP_CHATS,
                        'STORAGE_THRESHOLD': STORAGE_THRESHOLD,
                        'TORRENT_LIMIT': TORRENT_LIMIT,
                        'DIRECT_LIMIT': DIRECT_LIMIT,
                        'YTDLP_LIMIT': YTDLP_LIMIT,
                        'GDRIVE_LIMIT': GDRIVE_LIMIT,
                        'CLONE_LIMIT': CLONE_LIMIT,
                        'MEGA_LIMIT': MEGA_LIMIT,
                        'LEECH_LIMIT': LEECH_LIMIT,
                        'FSUB_IDS': FSUB_IDS,
                        'USER_MAX_TASKS': USER_MAX_TASKS,
                        'USER_TIME_INTERVAL': USER_TIME_INTERVAL,
                        'PLAYLIST_LIMIT': PLAYLIST_LIMIT,
                        'DAILY_TASK_LIMIT': DAILY_TASK_LIMIT,
                        'DAILY_MIRROR_LIMIT': DAILY_MIRROR_LIMIT,
                        'DAILY_LEECH_LIMIT': DAILY_LEECH_LIMIT,
                        'MIRROR_LOG_ID': MIRROR_LOG_ID,
                        'LEECH_LOG_ID': LEECH_LOG_ID,
                        'LINKS_LOG_ID': LINKS_LOG_ID,
                        'BOT_PM': BOT_PM,
                        'DISABLE_DRIVE_LINK': DISABLE_DRIVE_LINK,
                        'BOT_THEME': BOT_THEME,
                        'IMAGES': IMAGES,
                        'IMG_SEARCH': IMG_SEARCH,
                        'IMG_PAGE': IMG_PAGE,
                        'IMG_SOURCES': IMG_SOURCES,
                        'IMDB_TEMPLATE': DEF_IMDB_TEMP,
                        'AUTHOR_NAME': AUTHOR_NAME,
                        'AUTHOR_URL': AUTHOR_URL,
                        'COVER_IMAGE': COVER_IMAGE,
                        'TITLE_NAME': TITLE_NAME,
                        'GD_INFO': GD_INFO,
                        'GD_DESP': GD_DESP,
                        'GDTOT_CRYPT': GDTOT_CRYPT,
                        'EQUAL_SPLITS': EQUAL_SPLITS,
                        'EXTENSION_FILTER': EXTENSION_FILTER,
                        'GDRIVE_ID': GDRIVE_ID,
                        'INCOMPLETE_TASK_NOTIFIER': INCOMPLETE_TASK_NOTIFIER,
                        'INDEX_URL': INDEX_URL,
                        'IS_TEAM_DRIVE': IS_TEAM_DRIVE,
                        'METADATA': METADATA,
                        'ATTACHMENT': ATTACHMENT,
                        'LEECH_FILENAME_PREFIX': LEECH_FILENAME_PREFIX,
                        'LEECH_FILENAME_SUFFIX': LEECH_FILENAME_SUFFIX,
                        'LEECH_FILENAME_CAPTION': LEECH_FILENAME_CAPTION,
                        'LEECH_FILENAME_REMNAME': LEECH_FILENAME_REMNAME,
                        'MIRROR_FILENAME_PREFIX': MIRROR_FILENAME_PREFIX,
                        'MIRROR_FILENAME_SUFFIX': MIRROR_FILENAME_SUFFIX,
                        'MIRROR_FILENAME_REMNAME': MIRROR_FILENAME_REMNAME,
                        'LEECH_SPLIT_SIZE': LEECH_SPLIT_SIZE,
                        'LEECH_FONT': LEECH_FONT,
                        'THUMBNAIL_LAYOUT': THUMBNAIL_LAYOUT,
                        'LOGIN_PASS': LOGIN_PASS,
                        'TOKEN_TIMEOUT': TOKEN_TIMEOUT,
                        'MEDIA_GROUP': MEDIA_GROUP,
                        'MEDIA_STORE': MEDIA_STORE,
                        'MEGA_EMAIL': MEGA_EMAIL,
                        'MEGA_PASSWORD': MEGA_PASSWORD,
                        'MDL_TEMPLATE': MDL_TEMPLATE,
                        'OWNER_ID': OWNER_ID,
                        'QUEUE_ALL': QUEUE_ALL,
                        'QUEUE_DOWNLOAD': QUEUE_DOWNLOAD,
                        'QUEUE_UPLOAD': QUEUE_UPLOAD,
                        'RCLONE_FLAGS': RCLONE_FLAGS,
                        'RCLONE_PATH': RCLONE_PATH,
                        'RCLONE_SERVE_URL': RCLONE_SERVE_URL,
                        'RCLONE_SERVE_USER': RCLONE_SERVE_USER,
                        'RCLONE_SERVE_PASS': RCLONE_SERVE_PASS,
                        'RCLONE_SERVE_PORT': RCLONE_SERVE_PORT,
                        'SHOW_CLOUD_LINK': SHOW_CLOUD_LINK,
                        'RSS_CHAT': RSS_CHAT,
                        'RSS_DELAY': RSS_DELAY,
                        'RSS_SIZE_LIMIT': RSS_SIZE_LIMIT,
                        'SAVE_MSG': SAVE_MSG,
                        'SAFE_MODE': SAFE_MODE,
                        'SEARCH_API_LINK': SEARCH_API_LINK,
                        'SEARCH_LIMIT': SEARCH_LIMIT,
                        'SEARCH_PLUGINS': SEARCH_PLUGINS,
                        'SET_COMMANDS': SET_COMMANDS,
                        'SHOW_MEDIAINFO': SHOW_MEDIAINFO,
                        'SCREENSHOTS_MODE': SCREENSHOTS_MODE,
                        'CLEAN_LOG_MSG': CLEAN_LOG_MSG,
                        'SHOW_EXTRA_CMDS': SHOW_EXTRA_CMDS,
                        'SOURCE_LINK': SOURCE_LINK,
                        'STATUS_LIMIT': STATUS_LIMIT,
                        'STATUS_UPDATE_INTERVAL': STATUS_UPDATE_INTERVAL,
                        'STOP_DUPLICATE': STOP_DUPLICATE,
                        'SUDO_USERS': SUDO_USERS,
                        'TELEGRAM_API': TELEGRAM_API,
                        'TELEGRAM_HASH': TELEGRAM_HASH,
                        'TIMEZONE': TIMEZONE,
                        'TORRENT_TIMEOUT': TORRENT_TIMEOUT,
                        'UPSTREAM_REPO': UPSTREAM_REPO,
                        'UPSTREAM_BRANCH': UPSTREAM_BRANCH,
                        'UPGRADE_PACKAGES': UPGRADE_PACKAGES,
                        'USER_SESSION_STRING': USER_SESSION_STRING,
                        'USER_TD_MODE':USER_TD_MODE,
                        'USER_TD_SA': USER_TD_SA,
                        'USE_SERVICE_ACCOUNTS': USE_SERVICE_ACCOUNTS,
                        'WEB_PINCODE': WEB_PINCODE,
                        'YT_DLP_OPTIONS': YT_DLP_OPTIONS,
                        'YT_DESP': YT_DESP,
                        'YT_TAGS': YT_TAGS,
                        'YT_CATEGORY_ID': YT_CATEGORY_ID,
                        'YT_PRIVACY_STATUS': YT_PRIVACY_STATUS,
                        'FFMPEG_CMDS': FFMPEG_CMDS,
                        'UPLOAD_PATHS': UPLOAD_PATHS,
                        'NAME_SWAP': NAME_SWAP,
                        'WEB_ACCESS_PASSWORD': WEB_ACCESS_PASSWORD,
                        'DISABLE_MEGA': DISABLE_MEGA,
                        'DISABLE_TORRENTS': DISABLE_TORRENTS,
                        'DISABLE_LEECH': DISABLE_LEECH,
                        'DISABLE_BULK': DISABLE_BULK,
                        'DISABLE_MULTI': DISABLE_MULTI,
                        'DISABLE_SEED': DISABLE_SEED,
                        'DISABLE_FF_MODE': DISABLE_FF_MODE,
                        'USE_IMAGES': USE_IMAGES,
                        'USER_TRANSMISSION': USER_TRANSMISSION,
                        'HYBRID_LEECH': HYBRID_LEECH})

    if DATABASE_URL:
        await DbManger().update_config(config_dict)
    await gather(initiate_search_tools(), start_from_queued(), rclone_serve_booter())


async def get_buttons(key=None, edit_type=None, edit_mode=None, mess=None):
    buttons = ButtonMaker()
    if key is None:
        buttons.ibutton('Config Variables', "botset var")
        buttons.ibutton('Private Files', "botset private")
        buttons.ibutton('Qbit Settings', "botset qbit")
        buttons.ibutton('Close', "botset close")
        msg = '<b><i>Bot Settings:</i></b>'
    elif key == 'var':
        for k in list(OrderedDict(sorted(config_dict.items())).keys())[START:10+START]:
            buttons.ibutton(k, f"botset editvar {k}")
        buttons.ibutton('Back', "botset back")
        buttons.ibutton('Close', "botset close")
        for x in range(0, len(config_dict)-1, 10):
            buttons.ibutton(f'{int(x/10)+1}', f"botset start var {x}", position='footer')
        msg = f'<b>Config Variables</b> | <b>Page: {int(START/10)+1}</b>'
    elif key == 'private':
        buttons.ibutton('Back', "botset back")
        buttons.ibutton('Close', "botset close")
        msg = '''<u>Send any of these private files:</u>
        
<code>config.env, token.pickle, accounts.zip, list_drives.txt, categories.txt, shorteners.txt, cookies.txt, terabox.txt, .netrc or any other file!</code>

<i>To delete private file send only the file name as text message with or without extension.</i>

<b>Timeout:</b> 60 sec'''
    elif key == 'qbit':
        for k in list(qbit_options.keys())[START:10+START]:
            buttons.ibutton(k, f"botset editqbit {k}")
        if STATE == 'view':
            buttons.ibutton('Edit', "botset edit qbit")
        else:
            buttons.ibutton('View', "botset view qbit")
        buttons.ibutton('Back', "botset back")
        buttons.ibutton('Close', "botset close")
        for x in range(0, len(qbit_options)-1, 10):
            buttons.ibutton(
                f'{int(x/10)+1}', f"botset start qbit {x}", position='footer')
        msg = f'Qbittorrent Options | Page: {int(START/10)+1} | State: {STATE}'
    elif edit_type == 'editvar':
        msg = f'<b>Variable:</b> <code>{key}</code>\n\n'
        msg += f'<b>Description:</b> {default_desp.get(key, "No Description Provided")}\n\n'
        if mess.chat.type == ChatType.PRIVATE:
            msg += f'<b>Value:</b> <spoiler> {config_dict.get(key, "None")} </spoiler>\n\n'
        else:
            buttons.ibutton('View Var Value',
                            f"botset showvar {key}", position="header")
        buttons.ibutton('Back', "botset back var", position="footer")
        if key not in bool_vars:
            if not edit_mode:
                buttons.ibutton('Edit Value', f"botset editvar {key} edit")
            else:
                buttons.ibutton('Stop Edit', f"botset editvar {key}")
        if key not in ['TELEGRAM_HASH', 'TELEGRAM_API', 'OWNER_ID', 'BOT_TOKEN'] and key not in bool_vars:
            buttons.ibutton('Reset', f"botset resetvar {key}")
        buttons.ibutton('Close', "botset close", position="footer")
        if edit_mode and key in ['SUDO_USERS', 'CMD_SUFFIX', 'OWNER_ID', 'USER_SESSION_STRING', 'TELEGRAM_HASH',
                                 'TELEGRAM_API', 'AUTHORIZED_CHATS', 'DATABASE_URL', 'BOT_TOKEN', 'DOWNLOAD_DIR']:
            msg += '<b>Note:</b> Restart required for this edit to take effect!\n\n'
        if edit_mode and key not in bool_vars:
            msg += '<i>Send a valid value for the above Var.</i> <b>Timeout:</b> 60 sec'
        if key in bool_vars:
            msg += '<i>Choose a valid value for the above Var</i>'
            buttons.ibutton('True', f"botset boolvar {key} on")
            buttons.ibutton('False', f"botset boolvar {key} off")
    elif edit_type == 'editqbit':
        buttons.ibutton('Back', "botset back qbit")
        buttons.ibutton('Empty String', f"botset emptyqbit {key}")
        buttons.ibutton('Close', "botset close")
        msg = f'Send a valid value for {key}. Timeout: 60 sec'
    button = buttons.build_menu(1) if key is None else buttons.build_menu(2)
    return msg, button


async def update_buttons(message, key=None, edit_type=None, edit_mode=None):
    msg, button = await get_buttons(key, edit_type, edit_mode, message)
    await editMessage(message, msg, button)


async def edit_variable(_, message, pre_message, key):
    handler_dict[message.chat.id] = False
    value = message.text
    if key == 'RSS_DELAY':
        value = int(value)
        addJob(value)
    elif key == 'DOWNLOAD_DIR':
        if not value.endswith('/'):
            value += '/'
    elif key in ['LINKS_LOG_ID', 'RSS_CHAT']:
        value = int(value)
    elif key == 'STATUS_UPDATE_INTERVAL':
        value = int(value)
        if len(download_dict) != 0:
            async with status_reply_dict_lock:
                if Interval:
                    Interval[0].cancel()
                    Interval.clear()
                    Interval.append(setInterval(value, update_all_messages))
    elif key == 'TORRENT_TIMEOUT':
        value = int(value)
    elif key == 'LEECH_SPLIT_SIZE':
        value = min(int(value), MAX_SPLIT_SIZE)
    elif key == 'BOT_THEME':
        if not value.strip() in AVL_THEMES.keys():
            value = 'minimal'
    elif key == 'CAP_FONT':
        value = value.strip().lower()
        if value not in ['b', 'i', 'u', 's', 'spoiler', 'code']:
            value = 'code'
    elif key == 'BASE_URL_PORT':
        value = int(value)
        if config_dict['BASE_URL']:
            await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
            await create_subprocess_shell(f"gunicorn web.wserver:app --bind 0.0.0.0:{value} --worker-class gevent")
    elif key == 'EXTENSION_FILTER':
        fx = value.split()
        GLOBAL_EXTENSION_FILTER.clear()
        GLOBAL_EXTENSION_FILTER.extend(['!qB'])
        for x in fx:
            if x.strip().startswith('.'):
                x = x.lstrip('.')
            GLOBAL_EXTENSION_FILTER.append(x.strip().lower())
    elif key == 'GDRIVE_ID':
        list_drives_dict['Main'] = {"drive_id": value, "index_link": config_dict['INDEX_URL']}
        categories_dict['Root'] = {"drive_id": value, "index_link": config_dict['INDEX_URL']}
    elif key == 'INDEX_URL':
        list_drives_dict['Main'] = {"drive_id": config_dict['GDRIVE_ID'], "index_link": value}
        categories_dict['Root'] = {"drive_id": config_dict['GDRIVE_ID'], "index_link": value}
    elif value.isdigit():
        value = int(value)
    config_dict[key] = value
    await update_buttons(pre_message, key, 'editvar', False)
    await deleteMessage(message)
    if DATABASE_URL:
        await DbManger().update_config({key: value})
    if key in ['SEARCH_PLUGINS', 'SEARCH_API_LINK']:
        await initiate_search_tools()
    elif key in ['QUEUE_ALL', 'QUEUE_DOWNLOAD', 'QUEUE_UPLOAD']:
        await start_from_queued()
    elif key in ['RCLONE_SERVE_URL', 'RCLONE_SERVE_PORT', 'RCLONE_SERVE_USER', 'RCLONE_SERVE_PASS']:
        await rclone_serve_booter()


async def edit_qbit(_, message, pre_message, key):
    handler_dict[message.chat.id] = False
    value = message.text
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    elif key == 'max_ratio':
        value = float(value)
    elif value.isdigit():
        value = int(value)
    await sync_to_async(get_client().app_set_preferences, {key: value})
    qbit_options[key] = value
    await update_buttons(pre_message, 'qbit')
    await deleteMessage(message)
    if DATABASE_URL:
        await DbManger().update_qbittorrent(key, value)


async def update_private_file(_, message, pre_message):
    handler_dict[message.chat.id] = False
    if not message.media and (file_name := message.text):
        path = file_name
        fn = file_name.rsplit('.zip', 1)[0]
        if await aiopath.isfile(fn) and file_name != 'config.env':
            await remove(fn)
        if fn == 'accounts':
            if await aiopath.exists('accounts'):
                await aiormtree('accounts')
            if await aiopath.exists('rclone_sa'):
                await aiormtree('rclone_sa')
            config_dict['USE_SERVICE_ACCOUNTS'] = False
            if DATABASE_URL:
                await DbManger().update_config({'USE_SERVICE_ACCOUNTS': False})
        elif file_name in ['.netrc', 'netrc']:
            await (await create_subprocess_exec("touch", ".netrc")).wait()
            await (await create_subprocess_exec("chmod", "600", ".netrc")).wait()
            await (await create_subprocess_exec("cp", ".netrc", "/root/.netrc")).wait()
        elif file_name.startswith('kpsml_'):
            path = f"bot/helper/themes/{file_name.rsplit('.py', 1)[0]}.py"
            if await aiopath.isfile(path):
                await remove(path)
        elif file_name in ['buttons.txt', 'buttons']:
            extra_buttons.clear()
        elif file_name in ['categories.txt', 'categories']:
            categories_dict.clear()
            if GDRIVE_ID := config_dict['GDRIVE_ID']:
                categories_dict['Root'] = {"drive_id": GDRIVE_ID, "index_link": config_dict['INDEX_URL']}
        elif file_name in ['list_drives.txt', 'list_drives']:
            list_drives_dict.clear()
            if GDRIVE_ID := config_dict['GDRIVE_ID']:
                list_drives_dict['Main'] = {"drive_id": GDRIVE_ID, "index_link": config_dict['INDEX_URL']}
        elif file_name in ['shorteners.txt', 'shorteners']:
            shorteners_list.clear()
        await deleteMessage(message)
    elif doc := message.document:
        file_name = doc.file_name
        path = file_name
        if file_name.startswith('kpsml_') and file_name.endswith('.py'):
            path = f'bot/helper/themes/{file_name}'
        await message.download(file_name=f'{getcwd()}/{path}')
        if file_name == 'accounts.zip':
            if await aiopath.exists('accounts'):
                await aiormtree('accounts')
            if await aiopath.exists('rclone_sa'):
                await aiormtree('rclone_sa')
            await (await create_subprocess_exec("7z", "x", "-o.", "-aoa", "accounts.zip", "accounts/*.json")).wait()
            await (await create_subprocess_exec("chmod", "-R", "777", "accounts")).wait()
        elif file_name == 'list_drives.txt':
            list_drives_dict.clear()
            if GDRIVE_ID := config_dict['GDRIVE_ID']:
                list_drives_dict['Main'] = {"drive_id": GDRIVE_ID, "index_link": config_dict['INDEX_URL']}
            async with aiopen('list_drives.txt', 'r+') as f:
                lines = await f.readlines()
                for line in lines:
                    sep = 2 if line.strip().split()[-1].startswith('http') else 1
                    temp = line.strip().rsplit(maxsplit=sep)
                    name = "Main Custom" if temp[0].casefold() == "Main" else temp[0]
                    list_drives_dict[name] = {'drive_id': temp[1], 'index_link': (temp[2] if sep == 2 else '')}
        elif file_name == 'categories.txt':
            categories_dict.clear()
            if GDRIVE_ID := config_dict['GDRIVE_ID']:
                categories_dict['Root'] = {"drive_id": GDRIVE_ID, "index_link": config_dict['INDEX_URL']}
            async with aiopen('categories.txt', 'r+') as f:
                lines = await f.readlines()
                for line in lines:
                    sep = 2 if line.strip().split()[-1].startswith('http') else 1
                    temp = line.strip().rsplit(maxsplit=sep)
                    name = "Root Custom" if temp[0].casefold() == "Root" else temp[0]
                    categories_dict[name] = {'drive_id': temp[1], 'index_link': (temp[2] if sep == 2 else '')}
        elif file_name == 'buttons.txt':
            extra_buttons.clear()
            async with aiopen('buttons.txt', 'r+') as f:
                lines = await f.readlines()
                for line in lines:
                    temp = line.strip().rsplit(maxsplit=1)
                    if len(extra_buttons.keys()) >= 20:
                        break
                    elif temp[1].startswith('http'):
                        extra_buttons[temp[0]] = temp[1]
        elif file_name == 'shorteners.txt':
            shorteners_list.clear()
            async with aiopen('shorteners.txt', 'r+') as f:
                lines = await f.readlines()
                for line in lines:
                    temp = line.strip().split()
                    if len(temp) == 2:
                        shorteners_list.append({'domain': temp[0],'api_key': temp[1]})
        elif file_name in ['.netrc', 'netrc']:
            if file_name == 'netrc':
                await rename('netrc', '.netrc')
                file_name = '.netrc'
            await (await create_subprocess_exec("chmod", "600", ".netrc")).wait()
            await (await create_subprocess_exec("cp", ".netrc", "/root/.netrc")).wait()
        elif file_name == 'config.env':
            load_dotenv('config.env', override=True)
            await load_config()
        if '@github.com' in config_dict['UPSTREAM_REPO']:
            buttons = ButtonMaker()
            msg = '<i>Do you want to Upload (Git Push) your file to <b>UPSTREAM_REPO</b> ?</i>'
            buttons.ibutton('Yes!', f"botset push {file_name}")
            buttons.ibutton('No!', "botset close")
            await sendMessage(message, msg, buttons.build_menu(2))
        else:
            await deleteMessage(message)
    if file_name == 'wcl.conf':
        await rclone_serve_booter()
    await update_buttons(pre_message)
    if DATABASE_URL:
        await DbManger().update_private_file(path)
    if await aiopath.exists('accounts.zip'):
        await remove('accounts.zip')


async def event_handler(client, query, pfunc, rfunc, document=False):
    chat_id = query.message.chat.id
    handler_dict[chat_id] = True
    start_time = time()

    async def event_filter(_, __, event):
        user = event.from_user or event.sender_chat
        return bool(user.id == query.from_user.id and event.chat.id == chat_id and (event.text or event.document and document))
    handler = client.add_handler(MessageHandler(
        pfunc, filters=create(event_filter)), group=-1)
    while handler_dict[chat_id]:
        await sleep(0.5)
        if time() - start_time > 60:
            handler_dict[chat_id] = False
            await rfunc()
    client.remove_handler(*handler)


@new_thread
async def edit_bot_settings(client, query):
    data = query.data.split()
    message = query.message
    if data[1] == 'close':
        handler_dict[message.chat.id] = False
        await query.answer()
        await deleteMessage(message)
        await deleteMessage(message.reply_to_message)
    elif data[1] == 'back':
        handler_dict[message.chat.id] = False
        await query.answer()
        key = data[2] if len(data) == 3 else None
        if key is None:
            globals()['START'] = 0
        await update_buttons(message, key)
    elif data[1] in ['var', 'qbit']:
        await query.answer()
        await update_buttons(message, data[1])
    elif data[1] == 'resetvar':
        handler_dict[message.chat.id] = False
        await query.answer('Reset Done!', show_alert=True)
        value = ''
        if data[2] in default_values:
            value = default_values[data[2]]
            if data[2] == "STATUS_UPDATE_INTERVAL" and len(download_dict) != 0:
                async with status_reply_dict_lock:
                    if Interval:
                        Interval[0].cancel()
                        Interval.clear()
                        Interval.append(setInterval(
                            value, update_all_messages))
        elif data[2] == 'EXTENSION_FILTER':
            GLOBAL_EXTENSION_FILTER.clear()
            GLOBAL_EXTENSION_FILTER.extend(['!qB'])
        elif data[2] == 'TORRENT_TIMEOUT':
            pass
        elif data[2] == 'BASE_URL':
            await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
        elif data[2] == 'BASE_URL_PORT':
            value = 80
            if config_dict['BASE_URL']:
                await (await create_subprocess_exec("pkill", "-9", "-f", "gunicorn")).wait()
                await create_subprocess_shell("gunicorn web.wserver:app --bind 0.0.0.0:80 --worker-class gevent")
        elif data[2] == 'GDRIVE_ID':
            if 'Main' in list_drives_dict:
                del list_drives_dict['Main']
            if 'Root' in categories_dict:
                del categories_dict['Root']
        elif data[2] == 'INDEX_URL':
            if (GDRIVE_ID := config_dict['GDRIVE_ID']) and 'Main' in list_drives_dict:
                list_drives_dict['Main'] = {"drive_id": GDRIVE_ID, "index_link": ''}
            if (GDRIVE_ID := config_dict['GDRIVE_ID']) and 'Root' in categories_dict:
                categories_dict['Root'] = {"drive_id": GDRIVE_ID, "index_link": ''}
        elif data[2] == 'INCOMPLETE_TASK_NOTIFIER' and DATABASE_URL:
            await DbManger().trunc_table('tasks')
        config_dict[data[2]] = value
        await update_buttons(message, data[2], 'editvar', False)
        if DATABASE_URL:
            await DbManger().update_config({data[2]: value})
        if data[2] in ['SEARCH_PLUGINS', 'SEARCH_API_LINK']:
            await initiate_search_tools()
        elif data[2] in ['QUEUE_ALL', 'QUEUE_DOWNLOAD', 'QUEUE_UPLOAD']:
            await start_from_queued()
        elif data[2] in ['RCLONE_SERVE_URL', 'RCLONE_SERVE_PORT', 'RCLONE_SERVE_USER', 'RCLONE_SERVE_PASS']:
            await rclone_serve_booter()
    elif data[1] == 'emptyqbit':
        handler_dict[message.chat.id] = False
        await query.answer()
        await sync_to_async(get_client().app_set_preferences, {data[2]: value})
        qbit_options[data[2]] = ''
        await update_buttons(message, 'qbit')
        if DATABASE_URL:
            await DbManger().update_qbittorrent(data[2], '')
    elif data[1] == 'private':
        handler_dict[message.chat.id] = False
        await query.answer()
        await update_buttons(message, data[1])
        pfunc = partial(update_private_file, pre_message=message)
        rfunc = partial(update_buttons, message)
        await event_handler(client, query, pfunc, rfunc, True)
    elif data[1] == 'boolvar':
        handler_dict[message.chat.id] = False
        value = data[3] == "on"
        await query.answer(f'Successfully Var changed to {value}!', show_alert=True)
        config_dict[data[2]] = value
        if not value and data[2] == 'INCOMPLETE_TASK_NOTIFIER' and DATABASE_URL:
            await DbManger().trunc_table('tasks')
        await update_buttons(message, data[2], 'editvar', False)
        if DATABASE_URL:
            await DbManger().update_config({data[2]: value})
    elif data[1] == 'editvar':
        handler_dict[message.chat.id] = False
        await query.answer()
        edit_mode = len(data) == 4
        await update_buttons(message, data[2], data[1], edit_mode)
        if data[2] in bool_vars or not edit_mode:
            return
        pfunc = partial(edit_variable, pre_message=message, key=data[2])
        rfunc = partial(update_buttons, message, data[2], data[1], edit_mode)
        await event_handler(client, query, pfunc, rfunc)
    elif data[1] == 'showvar':
        value = config_dict[data[2]]
        if len(str(value)) > 200:
            await query.answer()
            with BytesIO(str.encode(value)) as out_file:
                out_file.name = f"{data[2]}.txt"
                await sendFile(message, out_file)
            return
        elif value == '':
            value = None
        await query.answer(f'{value}', show_alert=True)
    elif data[1] == 'editqbit' and STATE == 'edit':
        handler_dict[message.chat.id] = False
        await query.answer()
        await update_buttons(message, data[2], data[1])
        pfunc = partial(edit_qbit, pre_message=message, key=data[2])
        rfunc = partial(update_buttons, message, 'var')
        await event_handler(client, query, pfunc, rfunc)
    elif data[1] == 'editqbit' and STATE == 'view':
        value = qbit_options[data[2]]
        if len(str(value)) > 200:
            await query.answer()
            with BytesIO(str.encode(value)) as out_file:
                out_file.name = f"{data[2]}.txt"
                await sendFile(message, out_file)
            return
        elif value == '':
            value = None
        await query.answer(f'{value}', show_alert=True)
    elif data[1] == 'edit':
        await query.answer()
        globals()['STATE'] = 'edit'
        await update_buttons(message, data[2])
    elif data[1] == 'view':
        await query.answer()
        globals()['STATE'] = 'view'
        await update_buttons(message, data[2])
    elif data[1] == 'start':
        await query.answer()
        if START != int(data[3]):
            globals()['START'] = int(data[3])
            await update_buttons(message, data[2])
    elif data[1] == 'push':
        await query.answer()
        filename = data[2].rsplit('.zip', 1)[0]
        if await aiopath.exists(filename):
            await (await create_subprocess_shell(f"git add -f {filename} \
                                                   && git commit -sm botsettings -q \
                                                   && git push origin {config_dict['UPSTREAM_BRANCH']} -qf")).wait()
        else:
            await (await create_subprocess_shell(f"git rm -r --cached {filename} \
                                                   && git commit -sm botsettings -q \
                                                   && git push origin {config_dict['UPSTREAM_BRANCH']} -qf")).wait()
        await deleteMessage(message)
        await deleteMessage(message.reply_to_message)


async def bot_settings(_, message):
    msg, button = await get_buttons()
    globals()['START'] = 0
    await sendMessage(message, msg, button, 'IMAGES')


bot.add_handler(MessageHandler(bot_settings, filters=command(
    BotCommands.BotSetCommand) & CustomFilters.sudo))
bot.add_handler(CallbackQueryHandler(edit_bot_settings,
                filters=regex("^botset") & CustomFilters.sudo))
