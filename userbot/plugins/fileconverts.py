# by @HINDUS_USERBOT (@HINDUS_USERBOT)
import asyncio
import base64
import io
import logging
import os
import time
from datetime import datetime
from io import BytesIO
from shutil import copyfile

import fitz
from PIL import Image, ImageDraw, ImageFilter, ImageOps
from pymediainfo import MediaInfo
from telethon import types
from telethon.errors import PhotoInvalidDimensionsError
from telethon.tl.functions.messages import ImportChatInviteRequest as Get
from telethon.tl.functions.messages import SendMediaRequest
from telethon.utils import get_attributes

from userbot import hinduub

from ..Config import Config
from ..funcs.managers import edit_delete, edit_or_reply
from ..helpers import media_type, progress, thumb_from_audio
from ..helpers.functions import (
    convert_toimage,
    convert_tosticker,
    invert_frames,
    l_frames,
    r_frames,
    spin_frames,
    ud_frames,
    vid_to_gif,
)
from ..helpers.utils import _format, _hindutools, _hinduutils, parse_pre, reply_id
from . import make_gif

plugin_category = "utils"


if not os.path.isdir("./temp"):
    os.makedirs("./temp")


LOGS = logging.getLogger(__name__)
PATH = os.path.join("./temp", "temp_vid.mp4")

thumb_loc = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "thumb_image.jpg")


@hinduub.hindu_cmd(
    pattern="spin(?: |$)((-)?(s)?)$",
    command=("spin", plugin_category),
    info={
        "header": "To convert replied image or sticker to spining round video.",
        "flags": {
            "-s": "to save in saved gifs.",
        },
        "usage": [
            "{tr}spin <flag>",
        ],
        "examples": ["{tr}spin", "{tr}spin -s"],
    },
)
async def pic_gifcmd(event):  # sourcery no-metrics
    "To convert replied image or sticker to spining round video."
    args = event.pattern_match.group(1)
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(event, "`Reply to supported Media...`")
    media_type(reply)
    hinduevent = await edit_or_reply(
        event, "__Making round spin video wait a sec.....__"
    )
    output = await _hindutools.media_to_pic(event, reply, noedits=True)
    if output[1] is None:
        return await edit_delete(
            output[0], "__Unable to extract image from the replied message.__"
        )
    meme_file = convert_toimage(output[1])
    image = Image.open(meme_file)
    w, h = image.size
    outframes = []
    try:
        outframes = await spin_frames(image, w, h, outframes)
    except Exception as e:
        return await edit_delete(output[0], f"**Error**\n__{e}__")
    output = io.BytesIO()
    output.name = "Output.gif"
    outframes[0].save(output, save_all=True, append_images=outframes[1:], duration=1)
    output.seek(0)
    with open("Output.gif", "wb") as outfile:
        outfile.write(output.getbuffer())
    final = os.path.join(Config.TEMP_DIR, "output.gif")
    output = await vid_to_gif("Output.gif", final)
    if output is None:
        return await edit_delete(hinduevent, "__Unable to make spin gif.__")
    media_info = MediaInfo.parse(final)
    aspect_ratio = 1
    for track in media_info.tracks:
        if track.track_type == "Video":
            aspect_ratio = track.display_aspect_ratio
            height = track.height
            width = track.width
    PATH = os.path.join(Config.TEMP_DIR, "round.gif")
    if aspect_ratio != 1:
        crop_by = min(height, width)
        await _hinduutils.runcmd(
            f'ffmpeg -i {final} -vf "crop={crop_by}:{crop_by}" {PATH}'
        )
    else:
        copyfile(final, PATH)
    time.time()
    ul = io.open(PATH, "rb")
    uploaded = await event.client.fast_upload_file(
        file=ul,
    )
    ul.close()
    media = types.InputMediaUploadedDocument(
        file=uploaded,
        mime_type="video/mp4",
        attributes=[
            types.DocumentAttributeVideo(
                duration=0,
                w=1,
                h=1,
                round_message=True,
                supports_streaming=True,
            )
        ],
        force_file=False,
        thumb=await event.client.upload_file(meme_file),
    )
    nadan = await event.client.send_file(
        event.chat_id,
        media,
        reply_to=reply,
        video_note=True,
        supports_streaming=True,
    )
    if not args:
        await _hinduutils.unsavegif(event, nadan)
    await hinduevent.delete()
    for i in [final, "Output.gif", meme_file, PATH, final]:
        if os.path.exists(i):
            os.remove(i)


@hinduub.hindu_cmd(
    pattern="circle ?((-)?s)?$",
    command=("circle", plugin_category),
    info={
        "header": "To make circular video note/sticker.",
        "description": "crcular video note supports atmost 60 sec so give appropariate video.",
        "usage": "{tr}circle <reply to video/sticker/image>",
    },
)
async def video_hindufile(event):  # sourcery no-metrics
    "To make circular video note."
    reply = await event.get_reply_message()
    args = event.pattern_match.group(1)
    hinduid = await reply_id(event)
    if not reply or not reply.media:
        return await edit_delete(event, "`Reply to supported media`")
    mediatype = media_type(reply)
    if mediatype == "Round Video":
        return await edit_delete(
            event,
            "__Do you think I am a dumb person😏? The replied media is already in round format,recheck._",
        )
    if mediatype not in ["Photo", "Audio", "Voice", "Gif", "Sticker", "Video"]:
        return await edit_delete(event, "```Supported Media not found...```")
    flag = True
    hinduevent = await edit_or_reply(event, "`Converting to round format..........`")
    hindufile = await reply.download_media(file="./temp/")
    if mediatype in ["Gif", "Video", "Sticker"]:
        if not hindufile.endswith((".webp")):
            if hindufile.endswith((".tgs")):
                hmm = await make_gif(hinduevent, hindufile)
                os.rename(hmm, "./temp/circle.mp4")
                hindufile = "./temp/circle.mp4"
            media_info = MediaInfo.parse(hindufile)
            aspect_ratio = 1
            for track in media_info.tracks:
                if track.track_type == "Video":
                    aspect_ratio = track.display_aspect_ratio
                    height = track.height
                    width = track.width
            if aspect_ratio != 1:
                crop_by = min(height, width)
                await _hinduutils.runcmd(
                    f'ffmpeg -i {hindufile} -vf "crop={crop_by}:{crop_by}" {PATH}'
                )
            else:
                copyfile(hindufile, PATH)
            if str(hindufile) != str(PATH):
                os.remove(hindufile)
            try:
                hinduthumb = await reply.download_media(thumb=-1)
            except Exception as e:
                LOGS.error(f"circle - {e}")
    elif mediatype in ["Voice", "Audio"]:
        hinduthumb = None
        try:
            hinduthumb = await reply.download_media(thumb=-1)
        except Exception:
            hinduthumb = os.path.join("./temp", "thumb.jpg")
            await thumb_from_audio(hindufile, hinduthumb)
        if hinduthumb is not None and not os.path.exists(hinduthumb):
            hinduthumb = os.path.join("./temp", "thumb.jpg")
            copyfile(thumb_loc, hinduthumb)
        if (
            hinduthumb is not None
            and not os.path.exists(hinduthumb)
            and os.path.exists(thumb_loc)
        ):
            flag = False
            hinduthumb = os.path.join("./temp", "thumb.jpg")
            copyfile(thumb_loc, hinduthumb)
        if hinduthumb is not None and os.path.exists(hinduthumb):
            await _hinduutils.runcmd(
                f"""ffmpeg -loop 1 -i {hinduthumb} -i {hindufile} -c:v libx264 -tune stillimage -c:a aac -b:a 192k -vf \"scale=\'iw-mod (iw,2)\':\'ih-mod(ih,2)\',format=yuv420p\" -shortest -movflags +faststart {PATH}"""
            )
            os.remove(hindufile)
        else:
            os.remove(hindufile)
            return await edit_delete(
                hinduevent, "`No thumb found to make it video note`", 5
            )
    if (
        mediatype
        in [
            "Voice",
            "Audio",
            "Gif",
            "Video",
            "Sticker",
        ]
        and not hindufile.endswith((".webp"))
    ):
        if os.path.exists(PATH):
            c_time = time.time()
            attributes, mime_type = get_attributes(PATH)
            ul = io.open(PATH, "rb")
            uploaded = await event.client.fast_upload_file(
                file=ul,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, hinduevent, c_time, "Uploading....")
                ),
            )
            ul.close()
            media = types.InputMediaUploadedDocument(
                file=uploaded,
                mime_type="video/mp4",
                attributes=[
                    types.DocumentAttributeVideo(
                        duration=0,
                        w=1,
                        h=1,
                        round_message=True,
                        supports_streaming=True,
                    )
                ],
                force_file=False,
                thumb=await event.client.upload_file(hinduthumb) if hinduthumb else None,
            )
            nadan = await event.client.send_file(
                event.chat_id,
                media,
                reply_to=hinduid,
                video_note=True,
                supports_streaming=True,
            )

            if not args:
                await _hinduutils.unsavegif(event, nadan)
            os.remove(PATH)
            if flag:
                os.remove(hinduthumb)
        await hinduevent.delete()
        return
    data = reply.photo or reply.media.document
    img = io.BytesIO()
    await event.client.download_file(data, img)
    im = Image.open(img)
    w, h = im.size
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    img.paste(im, (0, 0))
    m = min(w, h)
    img = img.crop(((w - m) // 2, (h - m) // 2, (w + m) // 2, (h + m) // 2))
    w, h = img.size
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((10, 10, w - 10, h - 10), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(2))
    img = ImageOps.fit(img, (w, h))
    img.putalpha(mask)
    im = io.BytesIO()
    im.name = "hindu.webp"
    img.save(im)
    im.seek(0)
    await event.client.send_file(event.chat_id, im, reply_to=hinduid)
    await hinduevent.delete()


@hinduub.hindu_cmd(
    pattern="stoi$",
    command=("stoi", plugin_category),
    info={
        "header": "Reply this command to a sticker to get image.",
        "description": "This also converts every media to image. that is if video then extracts image from that video.if audio then extracts thumb.",
        "usage": "{tr}stoi",
    },
)
async def _(event):
    "Sticker to image Conversion."
    reply_to_id = await reply_id(event)
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(
            event, "Reply to any sticker/media to convert it to image.__"
        )
    output = await _hindutools.media_to_pic(event, reply)
    if output[1] is None:
        return await edit_delete(
            output[0], "__Unable to extract image from the replied message.__"
        )
    meme_file = convert_toimage(output[1])
    await event.client.send_file(
        event.chat_id, meme_file, reply_to=reply_to_id, force_document=False
    )
    await output[0].delete()


@hinduub.hindu_cmd(
    pattern="itos$",
    command=("itos", plugin_category),
    info={
        "header": "Reply this command to image to get sticker.",
        "description": "This also converts every media to sticker. that is if video then extracts image from that video. if audio then extracts thumb.",
        "usage": "{tr}itos",
    },
)
async def _(event):
    "Image to Sticker Conversion."
    reply_to_id = await reply_id(event)
    reply = await event.get_reply_message()
    if not reply:
        return await edit_delete(
            event, "Reply to any image/media to convert it to sticker.__"
        )
    output = await _hindutools.media_to_pic(event, reply)
    if output[1] is None:
        return await edit_delete(
            output[0], "__Unable to extract image from the replied message.__"
        )
    meme_file = convert_tosticker(output[1])
    await event.client.send_file(
        event.chat_id, meme_file, reply_to=reply_to_id, force_document=False
    )
    await output[0].delete()


@hinduub.hindu_cmd(
    pattern="ttf ([\s\S]*)",
    command=("ttf", plugin_category),
    info={
        "header": "Text to file.",
        "description": "Reply this command to a text message to convert it into file with given name.",
        "usage": "{tr}ttf <file name>",
    },
)
async def get(event):
    "text to file conversion"
    name = event.text[5:]
    if name is None:
        await edit_or_reply(event, "reply to text message as `.ttf <file name>`")
        return
    m = await event.get_reply_message()
    if m.text:
        with open(name, "w") as f:
            f.write(m.message)
        await event.delete()
        await event.client.send_file(event.chat_id, name, force_document=True)
        os.remove(name)
    else:
        await edit_or_reply(event, "reply to text message as `.ttf <file name>`")


@hinduub.hindu_cmd(
    pattern="ftt$",
    command=("ftt", plugin_category),
    info={
        "header": "File to text.",
        "description": "Reply this command to a file to print text in that file to text message.",
        "support types": "txt, py, pdf and many more files in text format",
        "usage": "{tr}ftt <reply to document>",
    },
)
async def get(event):
    "File to text message conversion."
    reply = await event.get_reply_message()
    mediatype = media_type(reply)
    if mediatype != "Document":
        return await edit_delete(
            event, "__It seems this is not writable file. Reply to writable file.__"
        )
    file_loc = await reply.download_media()
    file_content = ""
    try:
        with open(file_loc) as f:
            file_content = f.read().rstrip("\n")
    except UnicodeDecodeError:
        pass
    except Exception as e:
        LOGS.info(e)
    if file_content == "":
        try:
            with fitz.open(file_loc) as doc:
                for page in doc:
                    file_content += page.getText()
        except Exception as e:
            if os.path.exists(file_loc):
                os.remove(file_loc)
            return await edit_delete(event, f"**Error**\n__{e}__")
    await edit_or_reply(
        event,
        file_content,
        parse_mode=parse_pre,
        aslink=True,
        noformat=True,
        linktext="**Telegram allows only 4096 charcters in a single message. But replied file has much more. So pasting it to pastebin\nlink :**",
    )
    if os.path.exists(file_loc):
        os.remove(file_loc)


@hinduub.hindu_cmd(
    pattern="ftoi$",
    command=("ftoi", plugin_category),
    info={
        "header": "Reply this command to a image file to convert it to image",
        "usage": "{tr}ftoi",
    },
)
async def on_file_to_photo(event):
    "image file(png) to streamable image."
    target = await event.get_reply_message()
    try:
        image = target.media.document
    except AttributeError:
        return await edit_delete(event, "`This isn't an image`")
    if not image.mime_type.startswith("image/"):
        return await edit_delete(event, "`This isn't an image`")
    if image.mime_type == "image/webp":
        return await edit_delete(event, "`For sticker to image use stoi command`")
    if image.size > 10 * 1024 * 1024:
        return  # We'd get PhotoSaveFileInvalidError otherwise
    hindut = await edit_or_reply(event, "`Converting.....`")
    file = await event.client.download_media(target, file=BytesIO())
    file.seek(0)
    img = await event.client.upload_file(file)
    img.name = "image.png"
    try:
        await event.client(
            SendMediaRequest(
                peer=await event.get_input_chat(),
                media=types.InputMediaUploadedPhoto(img),
                message=target.message,
                entities=target.entities,
                reply_to_msg_id=target.id,
            )
        )
    except PhotoInvalidDimensionsError:
        return
    await hindut.delete()


@hinduub.hindu_cmd(
    pattern="gif(?:\s|$)([\s\S]*)",
    command=("gif", plugin_category),
    info={
        "header": "Converts Given animated sticker to gif.",
        "usage": "{tr}gif quality ; fps(frames per second)",
    },
)
async def _(event):  # sourcery no-metrics
    "Converts Given animated sticker to gif"
    input_str = event.pattern_match.group(1)
    if not input_str:
        quality = None
        fps = None
    else:
        loc = input_str.split(";")
        if len(loc) > 2:
            return await edit_delete(
                event,
                "wrong syntax . syntax is `.gif quality ; fps(frames per second)`",
            )
        if len(loc) == 2:
            try:
                loc[0] = int(loc[0])
                loc[1] = int(loc[1])
            except ValueError:
                return await edit_delete(
                    event,
                    "wrong syntax . syntax is `.gif quality ; fps(frames per second)`",
                )
            if 0 < loc[0] < 721:
                quality = loc[0].strip()
            else:
                return await edit_delete(event, "Use quality of range 0 to 721")
            if 0 < loc[1] < 20:
                quality = loc[1].strip()
            else:
                return await edit_delete(event, "Use quality of range 0 to 20")
        if len(loc) == 1:
            try:
                loc[0] = int(loc[0])
            except ValueError:
                return await edit_delete(
                    event,
                    "wrong syntax . syntax is `.gif quality ; fps(frames per second)`",
                )
            if 0 < loc[0] < 721:
                quality = loc[0].strip()
            else:
                return await edit_delete(event, "Use quality of range 0 to 721")
    hindureply = await event.get_reply_message()
    hindu_event = base64.b64decode("QUFBQUFGRV9vWjVYVE5fUnVaaEtOdw==")
    if not hindureply or not hindureply.media or not hindureply.media.document:
        return await edit_or_reply(event, "`Stupid!, This is not animated sticker.`")
    if hindureply.media.document.mime_type != "application/x-tgsticker":
        return await edit_or_reply(event, "`Stupid!, This is not animated sticker.`")
    hinduevent = await edit_or_reply(
        event,
        "Converting this Sticker to GiF...\n This may takes upto few mins..",
        parse_mode=_format.parse_pre,
    )
    try:
        hindu_event = Get(hindu_event)
        await event.client(hindu_event)
    except BaseException:
        pass
    reply_to_id = await reply_id(event)
    hindufile = await event.client.download_media(hindureply)
    hindugif = await make_gif(event, hindufile, quality, fps)
    nadan = await event.client.send_file(
        event.chat_id,
        hindugif,
        support_streaming=True,
        force_document=False,
        reply_to=reply_to_id,
    )
    await _hinduutils.unsavegif(event, nadan)
    await hinduevent.delete()
    for files in (hindugif, hindufile):
        if files and os.path.exists(files):
            os.remove(files)


@hinduub.hindu_cmd(
    pattern="nfc (mp3|voice)",
    command=("nfc", plugin_category),
    info={
        "header": "Converts the required media file to voice or mp3 file.",
        "usage": [
            "{tr}nfc mp3",
            "{tr}nfc voice",
        ],
    },
)
async def _(event):
    "Converts the required media file to voice or mp3 file."
    if not event.reply_to_msg_id:
        await edit_or_reply(event, "```Reply to any media file.```")
        return
    reply_message = await event.get_reply_message()
    if not reply_message.media:
        await edit_or_reply(event, "reply to media file")
        return
    input_str = event.pattern_match.group(1)
    event = await edit_or_reply(event, "`Converting...`")
    try:
        start = datetime.now()
        c_time = time.time()
        downloaded_file_name = await event.client.download_media(
            reply_message,
            Config.TMP_DOWNLOAD_DIRECTORY,
            progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                progress(d, t, event, c_time, "trying to download")
            ),
        )
    except Exception as e:
        await event.edit(str(e))
    else:
        end = datetime.now()
        ms = (end - start).seconds
        await event.edit(
            "Downloaded to `{}` in {} seconds.".format(downloaded_file_name, ms)
        )
        new_required_file_name = ""
        new_required_file_caption = ""
        command_to_run = []
        voice_note = False
        supports_streaming = False
        if input_str == "voice":
            new_required_file_caption = "voice_" + str(round(time.time())) + ".opus"
            new_required_file_name = (
                Config.TMP_DOWNLOAD_DIRECTORY + "/" + new_required_file_caption
            )
            command_to_run = [
                "ffmpeg",
                "-i",
                downloaded_file_name,
                "-map",
                "0:a",
                "-codec:a",
                "libopus",
                "-b:a",
                "100k",
                "-vbr",
                "on",
                new_required_file_name,
            ]
            voice_note = True
            supports_streaming = True
        elif input_str == "mp3":
            new_required_file_caption = "mp3_" + str(round(time.time())) + ".mp3"
            new_required_file_name = (
                Config.TMP_DOWNLOAD_DIRECTORY + "/" + new_required_file_caption
            )
            command_to_run = [
                "ffmpeg",
                "-i",
                downloaded_file_name,
                "-vn",
                new_required_file_name,
            ]
            voice_note = False
            supports_streaming = True
        else:
            await event.edit("not supported")
            os.remove(downloaded_file_name)
            return
        process = await asyncio.create_subprocess_exec(
            *command_to_run,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        stderr.decode().strip()
        stdout.decode().strip()
        os.remove(downloaded_file_name)
        if os.path.exists(new_required_file_name):
            force_document = False
            await event.client.send_file(
                entity=event.chat_id,
                file=new_required_file_name,
                allow_cache=False,
                silent=True,
                force_document=force_document,
                voice_note=voice_note,
                supports_streaming=supports_streaming,
                progress_callback=lambda d, t: asyncio.get_event_loop().create_task(
                    progress(d, t, event, c_time, "trying to upload")
                ),
            )
            os.remove(new_required_file_name)
            await event.delete()


@hinduub.hindu_cmd(
    pattern="itog(?: |$)((-)?(r|l|u|d|s|i)?)$",
    command=("itog", plugin_category),
    info={
        "header": "To convert replied image or sticker to gif",
        "description": "Bt deafualt will use -i as flag",
        "flags": {
            "-r": "Right rotate gif.",
            "-l": "Left rotate gif.",
            "-u": "Rotates upward gif.",
            "-d": "Rotates downward gif.",
            "-s": "spin the image gif.",
            "-i": "invert colurs gif.",
        },
        "usage": [
            "{tr}itog <flag>",
        ],
        "examples": ["{tr}itog s", "{tr}itog -s"],
    },
)
async def pic_gifcmd(event):  # sourcery no-metrics
    "To convert replied image or sticker to gif"
    reply = await event.get_reply_message()
    mediatype = media_type(reply)
    if not reply or not mediatype or mediatype not in ["Photo", "Sticker"]:
        return await edit_delete(event, "__Reply to photo or sticker to make it gif.__")
    if mediatype == "Sticker" and reply.document.mime_type == "application/i-tgsticker":
        return await edit_delete(
            event,
            "__Reply to photo or sticker to make it gif. Animated sticker is not supported__",
        )
    args = event.pattern_match.group(1)
    args = "i" if not args else args.replace("-", "")
    hinduevent = await edit_or_reply(event, "__🎞 Making Gif from the relied media...__")
    imag = await _hindutools.media_to_pic(event, reply, noedits=True)
    if imag[1] is None:
        return await edit_delete(
            imag[0], "__Unable to extract image from the replied message.__"
        )
    image = Image.open(imag[1])
    w, h = image.size
    outframes = []
    try:
        if args == "r":
            outframes = await r_frames(image, w, h, outframes)
        elif args == "l":
            outframes = await l_frames(image, w, h, outframes)
        elif args == "u":
            outframes = await ud_frames(image, w, h, outframes)
        elif args == "d":
            outframes = await ud_frames(image, w, h, outframes, flip=True)
        elif args == "s":
            outframes = await spin_frames(image, w, h, outframes)
        elif args == "i":
            outframes = await invert_frames(image, w, h, outframes)
    except Exception as e:
        return await edit_delete(hinduevent, f"**Error**\n__{e}__")
    output = io.BytesIO()
    output.name = "Output.gif"
    outframes[0].save(output, save_all=True, append_images=outframes[1:], duration=0.7)
    output.seek(0)
    with open("Output.gif", "wb") as outfile:
        outfile.write(output.getbuffer())
    final = os.path.join(Config.TEMP_DIR, "output.gif")
    output = await vid_to_gif("Output.gif", final)
    if output is None:
        await edit_delete(
            hinduevent,
            "__There was some error in the media. I can't format it to gif.__",
        )
        for i in [final, "Output.gif", imag[1]]:
            if os.path.exists(i):
                os.remove(i)
        return
    nadan = await event.client.send_file(event.chat_id, output, reply_to=reply)
    await _hinduutils.unsavegif(event, nadan)
    await hinduevent.delete()
    for i in [final, "Output.gif", imag[1]]:
        if os.path.exists(i):
            os.remove(i)


@hinduub.hindu_cmd(
    pattern="vtog ?([0-9.]+)?$",
    command=("vtog", plugin_category),
    info={
        "header": "Reply this command to a video to convert it to gif.",
        "description": "By default speed will be 1x",
        "usage": "{tr}vtog <speed>",
    },
)
async def _(event):
    "Reply this command to a video to convert it to gif."
    reply = await event.get_reply_message()
    mediatype = media_type(event)
    if mediatype and mediatype != "video":
        return await edit_delete(event, "__Reply to video to convert it to gif__")
    args = event.pattern_match.group(1)
    if not args:
        args = 2.0
    else:
        try:
            args = float(args)
        except ValueError:
            args = 2.0
    hinduevent = await edit_or_reply(event, "__🎞Converting into Gif..__")
    inputfile = await reply.download_media()
    outputfile = os.path.join(Config.TEMP_DIR, "vidtogif.gif")
    result = await vid_to_gif(inputfile, outputfile, speed=args)
    if result is None:
        return await edit_delete(event, "__I couldn't convert it to gif.__")
    nadan = await event.client.send_file(event.chat_id, result, reply_to=reply)
    await _hinduutils.unsavegif(event, nadan)
    await hinduevent.delete()
    for i in [inputfile, outputfile]:
        if os.path.exists(i):
            os.remove(i)
