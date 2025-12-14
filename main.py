import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from yt_dlp import YoutubeDL

API_TOKEN = "8289693562:AAHuplNSFW2T94bs47Z8Mz8p5lPksiaNyYc"

bot = Bot(API_TOKEN)
dp = Dispatcher()

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# vaqtincha qidiruv natijalarini saqlash
search_cache = {}


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🎵 <b>Musiqa bot</b>\n\n"
        "Qo‘shiq nomini yozing va variantlardan tanlang 👇",
        parse_mode="HTML"
    )


@dp.message(F.text)
async def search_music(message: types.Message):
    query = message.text
    msg = await message.answer("⏳ Musiqa qidirilyapti...")

    ydl_opts = {"quiet": True, "skip_download": True}

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch10:{query}", download=False)
            entries = info["entries"]
    except Exception as e:
        await msg.edit_text(f"❌ Xatolik yuz berdi: {e}")
        return

    if not entries:
        await msg.edit_text("❌ Hech narsa topilmadi")
        return

    search_cache[message.from_user.id] = entries

    text = ""
    kb = []

    for i, e in enumerate(entries, start=1):
        title = e["title"]
        duration = int(e.get("duration", 0))
        minutes = duration // 60
        seconds = duration % 60
        text += f"{i}. {title} {minutes}:{seconds:02d}\n"

        kb.append(
            InlineKeyboardButton(
                text=str(i),
                callback_data=f"music_{i}"
            )
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[kb[i:i+5] for i in range(0, len(kb), 5)]
    )

    await msg.edit_text(text, reply_markup=keyboard)


@dp.callback_query(F.data.startswith("music_"))
async def download_selected(call: types.CallbackQuery):
    index = int(call.data.split("_")[1]) - 1
    entries = search_cache.get(call.from_user.id)

    if not entries or index >= len(entries):
        await call.answer("Xatolik", show_alert=True)
        return

    video = entries[index]

    loading_msg = await call.message.edit_text("⬇️ Yuklanmoqda...")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video["webpage_url"]])
            file_path = os.path.splitext(ydl.prepare_filename(video))[0] + ".mp3"

        await call.message.answer_audio(FSInputFile(file_path))
    except Exception as e:
        await call.message.answer(f"❌ Yuklashda xatolik yuz berdi: {e}")
    finally:
        # Faylni o‘chirib disk to‘ldirmaslik
        if os.path.exists(file_path):
            os.remove(file_path)

        await loading_msg.delete()

    await call.answer("🎧 Tayyor!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())