#!/usr/bin/env python3
from secrets import token_hex
from aiofiles.os import makedirs, path as aiopath
from asyncio import sleep, create_subprocess_exec

from bot import (LOGGER, download_dict, download_dict_lock, non_queued_dl, queue_dict_lock)
from bot.helper.ext_utils.bot_utils import sync_to_async
from bot.helper.ext_utils.task_manager import is_queued, stop_duplicate_check
from bot.helper.mirror_utils.status_utils.direct_status import DirectStatus
from bot.helper.mirror_utils.status_utils.queue_status import QueueStatus
from bot.helper.telegram_helper.message_utils import sendMessage, sendStatusMessage

class DirectListener:
    def __init__(self, foldername, total_size, path, listener):
        self.__path = path
        self.__listener = listener
        self.__is_cancelled = False
        self.__proc_bytes = 0
        self.__failed = 0
        self.__speed = 0
        self.__completed_length = 0
        self.name = foldername
        self.total_size = total_size

    @property
    def processed_bytes(self):
        return self.__proc_bytes + self.__completed_length

    @property
    def speed(self):
        return self.__speed

    async def download(self, contents, header):
        for content in contents:
            if self.__is_cancelled:
                break

            fpath = f"{self.__path}/{content['path']}" if content['path'] else self.__path
            await makedirs(fpath, exist_ok=True)
            filename = content['filename'] or content['url'].split('/')[-1]
            out_path = f"{fpath}/{filename}"

            LOGGER.info(f"Downloading: {filename}")

            cmd = ["curl", "-L", "-k", "-C", "-", "--retry", "10", "--retry-delay", "3", "--user-agent", "Wget/1.12", "-o", out_path]
            if header:
                for h in header.split(' '):
                    if h:
                        cmd.extend(["-H", h])
            cmd.append(content['url'])

            try:
                process = await create_subprocess_exec(*cmd)

                while process.returncode is None:
                    if self.__is_cancelled:
                        process.kill()
                        break

                    if await aiopath.exists(out_path):
                        current_size = await aiopath.getsize(out_path)
                        self.__speed = current_size - self.__completed_length
                        self.__completed_length = current_size

                    await sleep(1)

                await process.wait()

                if process.returncode != 0 and not self.__is_cancelled:
                    LOGGER.error(f"Failed to download {filename}. Return code: {process.returncode}")
                    self.__failed += 1
                else:
                    if await aiopath.exists(out_path):
                        self.__proc_bytes += await aiopath.getsize(out_path)
                    self.__completed_length = 0
            except Exception as e:
                LOGGER.error(f"Error downloading {filename}: {e}")
                self.__failed += 1

        if self.__is_cancelled:
            return

        if self.__failed == len(contents):
            await self.__listener.onDownloadError('All files failed to download!')
        else:
            await self.__listener.onDownloadComplete()

    async def cancel_download(self):
        self.__is_cancelled = True
        LOGGER.info(f"Cancelling Download: {self.name}")
        await self.__listener.onDownloadError("Download Cancelled by User!")

async def add_direct_download(details, path, listener, foldername):
    if not (contents:= details.get('contents')):
        await sendMessage(listener.message, 'There is nothing to download!')
        return
    size = details.get('total_size', 0)

    if not foldername:
        foldername = details.get('title', 'DirectDownload')
    path = f'{path}/{foldername}'
    msg, button = await stop_duplicate_check(foldername, listener)
    if msg:
        await sendMessage(listener.message, msg, button)
        return

    gid = token_hex(5)
    added_to_queue, event = await is_queued(listener.uid)
    if added_to_queue:
        LOGGER.info(f"Added to Queue/Download: {foldername}")
        async with download_dict_lock:
            download_dict[listener.uid] = QueueStatus(
                foldername, size, gid, listener, 'dl')
        await listener.onDownloadStart()
        await sendStatusMessage(listener.message)
        await event.wait()
        async with download_dict_lock:
            if listener.uid not in download_dict:
                return
        from_queue = True
    else:
        from_queue = False

    directListener = DirectListener(foldername, size, path, listener)
    async with download_dict_lock:
        download_dict[listener.uid] = DirectStatus(directListener, gid, listener, listener.upload_details)

    async with queue_dict_lock:
        non_queued_dl.add(listener.uid)

    if from_queue:
        LOGGER.info(f'Start Queued Download from Direct Download: {foldername}')
    else:
        LOGGER.info(f"Download from Direct Download: {foldername}")
        await listener.onDownloadStart()
        await sendStatusMessage(listener.message)

    header = details.get('header')
    await directListener.download(contents, header)
