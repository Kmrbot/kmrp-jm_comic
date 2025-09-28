import os

import jmcomic
from typing import Tuple, Any
from nonebot.rule import to_me
from protocol_adapter.adapter_type import AdapterGroupMessageEvent, AdapterBot
from protocol_adapter.protocol_adapter import ProtocolAdapter
from nonebot import on_regex, logger
from nonebot.params import RegexGroup
from utils.permission import white_list_handle
from utils import group_only, get_time_zone, get_config_path
from utils.push_manager import PushManager
from utils.task_deliver import TaskDeliverManager

download_jm_comic = on_regex(
    pattern=r"^(JM|jm) ([0-9]*)$",
    rule=to_me(),
    priority=5,
)


download_jm_comic.__doc__ = """下载JM漫画"""
download_jm_comic.__help_type__ = None

download_jm_comic.handle()(white_list_handle("jm_comic"))
download_jm_comic.handle()(group_only)

async def download(**kwargs):
    bot = kwargs["bot"]
    event = kwargs["event"]
    id = kwargs["id"]
    # 首先判断一下有没有对应的zip，有就直接发
    file_path = f"{os.getcwd()}/jm_download/{id}.zip"
    if not os.path.exists(file_path):
        option = jmcomic.create_option_by_file(str(get_config_path().joinpath("jm_comic/config.yml")))
        try:
            jmcomic.download_album(id, option)
        except Exception as e:
            logger.warning(f"download jm comic id {id} fail.")
            await download_jm_comic.finish()
    else:
        logger.info(f"download jm comic id {id} file exist. Ignore.")
    # 找对应文件并上传到群中，默认存到./download里
    # await ProtocolAdapter.Group.create_group_file_folder(
    #     ProtocolAdapter.get_bot_id(bot),
    #     ProtocolAdapter.get_msg_type_id(event),
    #     "KMR_JM_DOWNLOAD"
    # )
    await ProtocolAdapter.Group.upload_group_file(
        ProtocolAdapter.get_bot_id(bot),
        ProtocolAdapter.get_msg_type_id(event),
        file_path,
        f"JM_{id}.zip",
        "") # 目前写了这个有问题，就先不写了

    # PushManager.notify(PushManager.PushData(
    #     msg_type=ProtocolAdapter.get_msg_type(event),
    #     msg_type_id=ProtocolAdapter.get_msg_type_id(event),
    #     message=ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text(f"本子ID {id}已上传至群文件中")))


@download_jm_comic.handle()
async def _(
        bot: AdapterBot,
        event: AdapterGroupMessageEvent,
        params: Tuple[Any, ...] = RegexGroup(),
):
    if len(params) < 2:
        download_jm_comic.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text("无效ID!"))
    id = params[1]
    TaskDeliverManager.add_task(download, bot=bot, event=event, id=id)
    await download_jm_comic.finish(ProtocolAdapter.MS.reply(event) + ProtocolAdapter.MS.text(f"正在尝试下载本子ID {id}..."))
