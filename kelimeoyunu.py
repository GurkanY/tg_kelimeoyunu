import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = "8204230760:AAHtuR-fsaqrUlBOUzOEbvfe39DQ3LjP73g"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# 🔧 Oyun durum değişkenleri
game_active = False
used_words = set()
current_letter = ""
scores = defaultdict(int)
last_player = None
timeout_task = None
ANSWER_TIMEOUT = 20


def reset_game():
    global game_active, used_words, current_letter, scores, last_player, timeout_task
    game_active = False
    used_words.clear()
    current_letter = ""
    scores.clear()
    last_player = None
    timeout_task = None


async def start_timeout(message: Message):
    global timeout_task
    try:
        await asyncio.sleep(ANSWER_TIMEOUT)
        await message.answer("⏰ Süre doldu! Kimse cevap vermedi. Oyun bitti.")
        reset_game()
    except asyncio.CancelledError:
        pass


@dp.message(Command("oyun_baslat"))
async def start_game(message: Message):
    global game_active, used_words, current_letter, scores, timeout_task

    if game_active:
        await message.answer("⚠️ Zaten bir oyun devam ediyor!")
        return

    reset_game()
    game_active = True
    first_word = "elma"
    used_words.add(first_word)
    current_letter = first_word[-1]

    await message.answer(
        f"🎮 *Son Harf Oyunu Başladı!*\n"
        f"İlk kelime: *{first_word}*\n"
        f"Son harf: *{current_letter.upper()}*\n"
        f"Sıradaki kişi bu harfle başlayan bir kelime yazmalı!",
        parse_mode="Markdown",
    )

    timeout_task = asyncio.create_task(start_timeout(message))


@dp.message(F.text)
async def play_game(message: Message):
    global current_letter, last_player, timeout_task, game_active

    if not game_active:
        await message.answer("👋 Oyun başlatmak için /oyun_baslat yazabilirsin.")
        return

    word = message.text.lower().strip()
    user = message.from_user.first_name

    if not word.isalpha():
        await message.reply("❌ Sadece harflerden oluşan bir kelime yazmalısın.")
        return

    if word in used_words:
        await message.reply("🚫 Bu kelime zaten söylendi.")
        return

    if not word.startswith(current_letter):
        await message.reply(f"❌ Kelime '{current_letter.upper()}' harfiyle başlamalı.")
        return

    if user == last_player:
        await message.reply("🕹️ Aynı kişi arka arkaya oynayamaz! Başkası denesin.")
        return

    # Süreyi sıfırla
    if timeout_task:
        timeout_task.cancel()
    timeout_task = asyncio.create_task(start_timeout(message))

    used_words.add(word)
    current_letter = word[-1]
    last_player = user
    scores[user] += 1

    await message.answer(
        f"✅ *{word}* kabul edildi!\n{user} +1 puan kazandı.\nSon harf: *{current_letter.upper()}*",
        parse_mode="Markdown",
    )


@dp.message(Command("puanlar"))
async def show_scores(message: Message):
    if not scores:
        await message.answer("📊 Henüz puan yok.")
        return

    text = "🏆 *Puan Tablosu:*\n"
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    for user, score in sorted_scores:
        text += f"• {user}: {score} puan\n"

    await message.answer(text, parse_mode="Markdown")


@dp.message(Command("bitir"))
async def end_game(message: Message):
    global game_active, timeout_task
    if not game_active:
        await message.answer("⚠️ Şu anda aktif bir oyun yok.")
        return

    if timeout_task:
        timeout_task.cancel()

    game_active = False
    await message.answer("🎮 Oyun sona erdi! Herkesin eline sağlık 🙌")
    reset_game()


@dp.message(Command("yardim"))
async def help_command(message: Message):
    text = (
        "🧩 *Son Harf Oyunu Botu Komutları:*\n\n"
        "/oyun_baslat - Yeni oyun başlatır\n"
        "/puanlar - Puan durumunu gösterir\n"
        "/bitir - Oyunu bitirir\n"
        "/yardim - Bu mesajı gösterir\n\n"
        "📖 Kurallar:\n"
        "• Her kelime, önceki kelimenin son harfiyle başlamalı.\n"
        "• Aynı kelimeyi tekrar söyleyemezsin.\n"
        "• Aynı kişi iki kez üst üste oynayamaz.\n"
        f"• {ANSWER_TIMEOUT} saniye içinde cevap gelmezse oyun biter."
    )
    await message.answer(text, parse_mode="Markdown")


async def main():
    print("🤖 Bot çalışıyor (aiogram v3)...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
