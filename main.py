# -*- coding: utf-8 -*-
from logging import info
from threading import Thread
from telebot.types import InputMediaPhoto
from config import config
from language import language
from utils import *
import telebot
import sys
import datetime
import traceback

sys.stdout.encoding  # 'UTF-8'
bot = telebot.TeleBot(config['token'])

@bot.message_handler(commands=['start'])
def start_command(message):
    if message.from_user.id not in [i[1] for i in GetUsers()]:
        Logging(f'Add new user {message.from_user.username} ({message.from_user.id})', 'NEW UESR', message.from_user.id)
        AddUser(message)
    Logging(f'Enter /start', 'COMMAND', message.from_user.id)
    main_menu(message.from_user.id)


@bot.message_handler(content_types=['text'])
def text_messages(message):
    if message.text == language['profile_btn']:
        Logging(f'View profile', 'COMMAND', message.from_user.id)
        user = GetUser(message.from_user.id)
        bot.send_message(message.from_user.id, language['profile_text'].format(user[3], user[6], user[7], datetime.datetime.fromtimestamp(user[5]).strftime('%d.%m.%Y %H:%M:%S')), parse_mode="Markdown")
    elif message.text == language['buy_btn']:
        Logging(f'Go buying', 'COMMAND', message.from_user.id)
        bot.send_message(message.from_user.id, language['wait_url'], parse_mode="Markdown")
        bot.register_next_step_handler(message, wait_url)
    elif message.text == language['info_btn']:
        Logging(f'View info', 'COMMAND', message.from_user.id)
        bot.send_message(message.from_user.id, language['information_text'], parse_mode="Markdown")
    else:
        Logging(f'Enter wrong command', 'COMMAND', message.from_user.id)
        bot.send_message(message.from_user.id, language['wrong_message'], parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if 'Confirm' in call.data:
        _asd, userid, comment, summa, delete, vkurl = call.data.split('|')
        user = GetUser(userid)
        #print(user[2])
        payment = GetPayment(userid, summa, comment)
        if payment and payment[0][4] == 'SUCCESS':
            return
        #print(summa, comment)
        #print(GetHistoryPayments())
        if CheckPayment(summa, comment):
            AddBuyCount(userid, 1)
            UpdatePayment(userid, summa, comment, 'SUCCESS')
            if delete == 'True':
                bot.send_message(userid, language['deposit_suсcess_delete_text'])
            else:
                with open(config['archive_send'], 'rb') as file_:
                    bot.send_document(userid, file_, caption=language['deposit_suсcess_text'], parse_mode='Markdown')
            bot.send_message(config['support_chat_id'], language['deposit_moderator_text'].format(f'{user[2]} ({userid})', vkurl, config['price']), parse_mode="Markdown")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            Logging(f'Successful: {comment}', 'DEPOSIT', userid)
        else:
            Logging(f'Not found: {comment}', 'DEPOSIT', userid)
            bot.send_message(userid, language['deposit_notfound_text'], parse_mode="Markdown")
    elif 'Decline' in call.data:
        _asd, userid, comment, summa = call.data.split('|')
        UpdatePayment(userid, summa, comment, 'DECLINE')
        bot.send_message(userid, language['deposit_decline_text'], parse_mode="Markdown")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        Logging(f'Decline: {comment}', 'DEPOSIT', userid)
    elif 'BuySliv' in call.data:
        _asd, userid, url = call.data.split('|')
        wait_deposit(userid, url, False)
    elif 'DeleteSliv' in call.data:
        _asd, userid, url = call.data.split('|')
        wait_deposit(userid, url, True)

def main_menu(userid):
    bot.send_message(userid, text=language['home_text'], parse_mode="Markdown", reply_markup=telebot.types.ReplyKeyboardMarkup(True).row(language['buy_btn']).row(language['profile_btn'], language['info_btn']))

def wait_deposit(userid, vkurl, delete):
    text = config['price']
    login = config['qiwi_username'] if config['qiwi_username'] else '+' + config['qiwi_number']
    login_number = '999' if config['qiwi_username'] else ''
    comment = GenerateString()
    CreatePayment(userid, text, comment)
    th = Thread(target=check_payment, args=(userid, text, comment, vkurl, ))
    th.start()
    bot.send_message(userid, language['deposit_create_text'].format(int(config['time_for_payment']) // 60, text, login, comment), parse_mode="Markdown", \
        reply_markup=telebot.types.InlineKeyboardMarkup().add(\
            telebot.types.InlineKeyboardButton(text="Перейти к оплате", url=f'https://qiwi.com/payment/form/99{login_number}?extra[%27account%27]={login}&currency=643&comment={comment}&amountInteger={text}&amountFraction=0&blocked[0]=account&blocked[1]=comment&blocked[2]=sum')).add(\
                telebot.types.InlineKeyboardButton(text="✅ Проверить оплату", callback_data=f"Confirm|{userid}|{comment}|{text}|{delete}|{vkurl}"), telebot.types.InlineKeyboardButton(text="❌ Отменить платеж", callback_data=f"Decline|{userid}|{comment}|{text}")))
    Logging(f'Created: {login} // {comment} // {vkurl} // {delete}', 'DEPOSIT', userid)

def wait_url(message):
    text = ''.join(message.text.split())
    if 'https://vk.com/' not in text:
        bot.send_message(message.from_user.id, language['wrong_url'], parse_mode="Markdown")
        return
    text = text.split('/')[3]
    text = text[2:] if text.startswith('id') else text
    information = GetInformation(text)
    if 'error' in information.keys():
        bot.send_message(message.from_user.id, language['profile_not_found'], parse_mode="Markdown")
        return
    information = information['response'][0]
    reg = GetRegister(information['id'])
    AddCount(message.from_user.id, 1)
    try:
        ls = datetime.datetime.fromtimestamp(information['last_seen']['time']).strftime('%d.%m.%Y %H:%M:%S')
    except:
        ls = 'Неизвестно'
    if information['sex'] != 1:
        Logging(f'Find {message.from_user.id}, male', 'FOUND', message.from_user.id)
        bot.send_photo(message.from_user.id, information['photo_max'], language['text_profile_notfound'].format(\
        f'https://vk.com/id{information["id"]}', information['first_name'] + ' ' + information['last_name'], GetSex(information['sex']), GetBirthday(information), ls), parse_mode="Markdown")
        return
    Logging(f'Find {message.from_user.id}, female', 'FOUND', message.from_user.id)
    bot.send_media_group(message.from_user.id, [InputMediaPhoto(information['photo_max']), InputMediaPhoto(GetImage(information['id']))])
    bot.send_message(message.from_user.id, language['text_profile_found'].format(\
        f'https://vk.com/id{information["id"]}', information['first_name'] + ' ' + information['last_name'], GetSex(information['sex']), GetBirthday(information), ls, \
            reg.strftime('%d.%m.%Y'), GetTypeFishing(information['id']), GetDateSliv(reg), config['price'], int(information["id"]) % 5),\
                reply_markup=telebot.types.InlineKeyboardMarkup().add(telebot.types.InlineKeyboardButton(text="✅ Купить", callback_data=f"BuySliv|{message.from_user.id}|{information['id']}")).add(\
                    telebot.types.InlineKeyboardButton(text="❌ Удалить слив", callback_data=f"DeleteSliv|{message.from_user.id}|{information['id']}")), parse_mode="Markdown")


def check_payment(userid, summa, comment, vkurl):
    while 1:
        payment = GetPayment(userid, summa, comment)
        if payment and payment[0][4] == 'SUCCESS':
            break
        if payment and payment[0][4] == 'WAIT' and round(time.time()) >= int(payment[0][6]) + config['time_for_payment']:
            bot.send_message(userid, language['deposit_timeout_text'], parse_mode="Markdown")
            UpdatePayment(userid, summa, comment, 'TIMEOUT')
            Logging(f'Timeout: {comment} // {vkurl}', 'DEPOSIT', userid)
            break
        time.sleep(5)

if __name__ == '__main__':
    # print(GetHistoryPayments()[:200])
    # print(CheckPayment(19, 'suwizE3y'))
    Logging('Bot is running', 'START')
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            time.sleep(5)
            print(traceback.format_exc())
            Logging(f'Bot error... Restart', 'STOP')
