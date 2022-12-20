import asyncio
import telebot
from telebot.async_telebot import AsyncTeleBot, types

from data import storage
from secret import TOKEN

conn = storage.conn
cursor = storage.cursor

bot = AsyncTeleBot(TOKEN)


@bot.message_handler(commands=['start'])
async def start_message(message):
    await bot.reply_to(message, f"Вас приветствует бот!")


@bot.message_handler(content_types=["new_chat_members"])
async def hello_question(message):
    await bot.send_message(message.chat.id, "Новичкам привет!")
    await bot.send_message(message.chat.id,
                           "Узнать про функционал бота вы сможете с помощью команды */help*",
                           parse_mode="markdown")


@bot.message_handler(commands=['leave'])
async def admins_message(message):
    cur = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if not cur.status in ['creator', 'administrator']:
        await bot.send_message(message.chat.id, "Не админы не могут прогонять бота")
    else:
        await bot.send_message(message.chat.id, "Я ухожу")
        await bot.leave_chat(message.chat.id)


@bot.message_handler(commands=['stats'])
async def stats_message(message):
    admins = await bot.get_chat_administrators(message.chat.id)
    members = await bot.get_chat_members_count(message.chat.id)
    await bot.send_message(message.chat.id, "Участников")
    await bot.send_message(message.chat.id, "всего: " + str(members))
    await bot.send_message(message.chat.id, "админов: " + str(len(admins)))


@bot.message_handler(content_types=["sticker"])
async def ban_message(message):
    await bot.send_message(message.chat.id, "СТИКЕРЫ ЗАПРЕЩЕНЫ!!!")
    chat = message.chat.type
    cur = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if cur.status in ['creator', 'administrator']:
        await bot.send_message(message.chat.id, "Но админов не наказываем")
    elif chat == "private":
        await bot.send_message(message.chat.id, "Но в приватных чатах не наказываем")
    else:
        warning = cursor.execute(f'select Warnings from BannedUsers where ID = \'{message.from_user.id}\' and ChatID = \'{message.chat.id}\'').fetchone()
        if warning is not None:
            if warning[0] == 3:
                return
            warning = warning[0]
            cursor.execute(
                f'UPDATE BannedUsers SET Warnings = {warning + 1} WHERE ID = \'{message.from_user.id}\' and ChatID = \'{message.chat.id}\'')
            conn.commit()

            await bot.send_message(message.chat.id, "Еще *" + str(3 - warning - 1) + "* 🤔 и *бан*",
                                   parse_mode="markdown")
            if warning == 2:
                await bot.send_message(message.chat.id, "Так что прощай навечно, @" + str(message.from_user.username))
                await bot.ban_chat_member(message.chat.id, message.from_user.id)
                cursor.execute(
                    f'UPDATE BannedUsers SET Banned = 1 WHERE ID = \'{message.from_user.id}\' and ChatID = \'{message.chat.id}\'')
                conn.commit()
        else:
            cursor.execute(
                'INSERT INTO BannedUsers (ID, Username, Warnings, Banned, ChatID) VALUES (?, ?, ?, ?, ?)',
                (message.from_user.id, message.from_user.username, 1, 0, message.chat.id))
            conn.commit()
            await bot.send_message(message.chat.id, "Еще *2* 🤔 и *бан*",
                                   parse_mode="markdown")


@bot.message_handler(commands=['my_warnings'])
async def warnings_message(message):
    warning = cursor.execute(f'select Warnings from BannedUsers where ID = \'{message.from_user.id}\' and ChatID = \'{message.chat.id}\'').fetchone()
    if warning is None:
        await bot.send_message(message.chat.id, "Нет предупреждений 🎉")
    else:
        await bot.send_message(message.chat.id, "Предупреждений: " + str(warning[0]))


@bot.message_handler(commands=['unban'])
async def unban_message(message):
    to_be_unbanned = ' '.join(message.text.split()[1:])
    cur = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if not cur.status in ['creator', 'administrator']:
        await bot.send_message(message.chat.id, "Не админы не могут снять бан")
    elif to_be_unbanned == "":
        await bot.send_message(message.chat.id, "Введите аргумент после команды")
    else:
        is_banned = cursor.execute(
            f'select Banned from BannedUsers where Username = \'{to_be_unbanned}\' and ChatID = \'{message.chat.id}\'').fetchone()
        if is_banned is None or is_banned[0] == 0:
            await bot.send_message(message.chat.id, "Пользователь не найден в бан-базе этого чата")
        else:
            await bot.unban_chat_member(message.chat.id, cursor.execute(
                f'select ID from BannedUsers where Username = \'{to_be_unbanned}\' and ChatID = \'{message.chat.id}\'').fetchone()[0])
            await bot.send_message(message.chat.id, f"Теперь {to_be_unbanned} можно вернуть в чат")

            cursor.execute(f'DELETE FROM BannedUsers WHERE Username = \'{to_be_unbanned}\' and ChatID = \'{message.chat.id}\'')
            conn.commit()


@bot.message_handler(commands=['help'])
async def help_message(message):
    await bot.send_message(message.chat.id, "Для всех")
    await bot.send_message(message.chat.id, '''Функционал бота: */help*
Статистика чата: */stats*
Попытаться стать админом: */can_i_be_admin*
Словить бан можно за посылку стикеров 😔
Посмотреть свои предупреждения: */my_warnings*''', parse_mode="markdown")
    await bot.send_message(message.chat.id, "Для админов")
    await bot.send_message(message.chat.id, '''Заставить бота уйти: */leave*
Разбанить пользователя: */unban username*''', parse_mode="markdown")


@bot.message_handler(commands=['can_i_be_admin'])
async def can_i_be_admin_message(message):
    cur = await bot.get_chat_member(message.chat.id, message.from_user.id)
    if cur.status in ['creator', 'administrator']:
        await bot.send_message(message.chat.id, "@" + str(message.from_user.username) + " уже админ")
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        item_1 = types.KeyboardButton("! Бот, разреши !")
        item_2 = types.KeyboardButton("! Бот, откажи !")
        markup.add(item_1, item_2)
        await bot.send_message(message.chat.id, "Добавить @" + str(
            message.from_user.username) + " в админы?", reply_markup=markup)

        @bot.message_handler(content_types=["text"])
        async def can_i_be_admin_answer(answer, tmp_id=message.from_user.id,
                                        tmp_name=message.from_user.username):
            cur = await bot.get_chat_member(answer.chat.id, answer.from_user.id)
            if not cur.status in ['creator', 'administrator']:
                await bot.send_message(answer.chat.id, "У @" + str(
                    answer.from_user.username) + " нет прав делать админом")
            else:
                if answer.text == "! Бот, разреши !":
                    await bot.promote_chat_member(answer.chat.id, tmp_id, True)
                    await bot.send_message(answer.chat.id, "@" + str(
                        tmp_name) + " теперь в команде админов!")
                elif answer.text == "! Бот, откажи !":
                    await bot.send_message(answer.chat.id, "Отказано")


async def main():
    await bot.set_my_commands([
        types.BotCommand("/start", "starts the bot"),
        types.BotCommand("/help", "shows bot's commands"),
        types.BotCommand("/stats", "shows chat's statistics"),
        types.BotCommand("/can_i_be_admin", "ask for admin rights"),
        types.BotCommand("/my_warnings", "shows user's warnings"),
        types.BotCommand("/leave", "makes bot leave the chat"),
        types.BotCommand("/unban", "unbans user")
    ])
    await asyncio.gather(bot.infinity_polling())


if __name__ == '__main__':
    asyncio.run(main())
