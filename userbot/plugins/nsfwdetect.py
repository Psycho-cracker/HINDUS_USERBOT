# Copyright (C) 2020 BY - GitHub.com/code-rgb [TG - @deleteduser420]
# ported to hindu by @HINDUS_USERBOT (@HINDUS_USERBOT)

import os

import requests

from userbot import hinduub

from ..Config import Config
from ..funcs.managers import edit_delete, edit_or_reply

plugin_category = "utils"


@hinduub.hindu_cmd(
    pattern="detect$",
    command=("detect", plugin_category),
    info={
        "header": "To detect the nudity in reply image.",
        "description": "Reply detect command to any image or non animated sticker to detect the nudity in that",
        "usage": "{tr}detect",
    },
)
async def detect(event):
    "To detect the nudity in reply image."
    if Config.DEEP_AI is None:
        return await edit_delete(
            event, "Add VAR `DEEP_AI` get Api Key from https://deepai.org/", 5
        )
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(
            event, "`Reply to any image or non animated sticker !`", 5
        )
    hinduevent = await edit_or_reply(event, "`Downloading the file to check...`")
    media = await event.client.download_media(reply)
    if not media.endswith(("png", "jpg", "webp")):
        return await edit_delete(
            event, "`Reply to any image or non animated sticker !`", 5
        )
    hinduevent = await edit_or_reply(event, "`Detecting NSFW limit...`")
    r = requests.post(
        "https://api.deepai.org/api/nsfw-detector",
        files={
            "image": open(media, "rb"),
        },
        headers={"api-key": Config.DEEP_AI},
    )
    os.remove(media)
    if "status" in r.json():
        return await edit_delete(hinduevent, r.json()["status"])
    r_json = r.json()["output"]
    pic_id = r.json()["id"]
    percentage = r_json["nsfw_score"] * 100
    detections = r_json["detections"]
    link = f"https://api.deepai.org/job-view-file/{pic_id}/inputs/image.jpg"
    result = f"<b>Detected Nudity :</b>\n<a href='{link}'>>>></a> <code>{percentage:.3f}%</code>\n\n"
    if detections:
        for parts in detections:
            name = parts["name"]
            confidence = int(float(parts["confidence"]) * 100)
            result += f"<b>• {name}:</b>\n   <code>{confidence} %</code>\n"
    await edit_or_reply(
        hinduevent,
        result,
        link_preview=False,
        parse_mode="HTML",
    )
