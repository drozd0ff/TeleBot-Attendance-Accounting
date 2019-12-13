import telebot
from telebot import types
import mysql.connector
import datetime
import random

mySQLConnection = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="mydatabase"
)

knownUsers = []
userStep = {}


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        knownUsers.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


def listener(messages):
    """
    When new messages arrive TeleBot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(str(m.chat.first_name) + " [" + str(m.chat.id) + "]: " + m.text)


commands = {  # command description used in the "help" command
    'start': 'Get used to the bot',
    'help': 'Gives you information about the available commands',
    'sendLongText': 'A test using the \'send_chat_action\' command',
    'getImage': 'A test using multi-stage messages, custom keyboard, and media sending'
}

TOKEN = "PLEASE INSERT TOKEN"                                       #TODO INSERT TOKEN
bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener)  # register listener


def workers_names(id):
    try:
        mySQLConnection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="mydatabase"
        )

        mycursor = mySQLConnection.cursor(buffered=True)
        get_company_id_sql = """SELECT company_id FROM users WHERE user_id = %s ORDER BY id DESC LIMIT 1"""
        mycursor.execute(get_company_id_sql, (id,))
        current_company_id = mycursor.fetchall()[0][0]
        print("Текущий компани айди: " + str(current_company_id))
        sql = """SELECT name, last_name FROM users WHERE company_id = %s """
        mycursor.execute(sql, (current_company_id,))
        global names
        names = []
        result = mycursor.fetchall()
        for i in result:
            if i[0] and i[1] != "NULL":
                name = str(i[0]) + " " + str(i[1])
                names.append(name)
        mySQLConnection.commit()
        return names
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))
    finally:
        if (mySQLConnection.is_connected()):
            mycursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


def stat_calc(cid, mid, start_date, user_id):
    try:
        mySQLConnection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="mydatabase"
        )

        mycursor = mySQLConnection.cursor(buffered=True)
        get_company_id_sql = """SELECT company_id FROM users WHERE user_id = %s ORDER BY id DESC LIMIT 1"""
        mycursor.execute(get_company_id_sql, (cid,))
        current_company_id = mycursor.fetchall()[0][0]
        get_vacation_days = """SELECT vacation_time_days FROM users WHERE company_id = %s AND name IS NULL 
                                AND last_name IS NULL ORDER BY ID DESC"""
        mycursor.execute(get_vacation_days, (current_company_id,))
        vacation_days = mycursor.fetchall()[0][0]
        get_free_time_hours = """SELECT free_time_hours FROM users WHERE company_id = %s AND name IS NULL 
                                AND last_name IS NULL ORDER BY ID DESC"""
        mycursor.execute(get_free_time_hours, (current_company_id,))
        free_time_hours = mycursor.fetchall()[0][0]
        current_date = datetime.datetime.now().date()
        if start_date is None:
            start_date = '2019-01-01'
        val = [current_company_id, start_date, current_date]
        if user_id is None:
            get_test_stats = """SELECT time_difference, work_start_difference, work_finish_difference, status_id, id 
                                FROM workers WHERE company_id = %s AND DATE(arrival_time) between %s and %s ORDER BY id"""
        else:
            get_test_stats = """SELECT time_difference, work_start_difference, work_finish_difference, status_id, id 
                                FROM workers WHERE company_id = %s AND user_id = %s 
                                AND DATE(arrival_time) between %s and %s ORDER BY id"""
            val.insert(1, user_id)
        mycursor.execute(get_test_stats, val)
        result = mycursor.fetchall()

        office_total_time = 0
        free_time_total = 0
        home_total_time = 0
        sick_leave_total_time = 0
        vacation_total_time = 0
        neg_work_start_delay = 0
        pos_work_start_delay = 0
        neg_work_finish_delay = 0
        pos_work_finish_delay = 0

        for i in result:
            print("current element: " + str(i))
            if isinstance(i[1], datetime.timedelta):
                if i[1].days == -1:
                    pos_work_seconds = 86400 - i[1].seconds
                    pos_work_start_delay += pos_work_seconds
                    print("pos start delay: " + str(pos_work_start_delay))
                elif i[1].days == 0:
                    neg_work_start_delay += i[1].seconds
                    print("neg start delay: " + str(neg_work_start_delay))
            if isinstance(i[2], datetime.timedelta):
                if i[2].days == -1:
                    neg_work_seconds = 86400 - i[2].seconds
                    neg_work_finish_delay += neg_work_seconds
                    print("neg finish delay: " + str(neg_work_finish_delay))
                elif i[2].days == 0:
                    pos_work_finish_delay += i[2].seconds
                    print("pos finish delay: " + str(pos_work_finish_delay))

            if i[3] == 1 and isinstance(i[0], int):
                office_total_time += i[0]

            if i[3] == 2 and isinstance(i[0], int):
                free_time_total += i[0]

            if i[3] == 3 and isinstance(i[0], int):
                home_total_time += i[0]

            if i[3] == 4 and isinstance(i[0], int):
                sick_leave_total_time += i[0]

            if i[3] == 5 and isinstance(i[0], int):
                vacation_total_time += i[0]

        office_total_hours = str(office_total_time / 3600).split(".")[0]
        office_total_minutes = str((office_total_time % 3600) / 60).split(".")[0]
        office_total_seconds = str((office_total_time % 3600) % 60).split(".")[0]
        office_total_days = 0
        if (office_total_time / 3600) > 24:
            office_total_days = str((office_total_time / 3600) / 24).split(".")[0]
            office_total_hours = str((office_total_time / 3600) % 24).split(".")[0]
            result_office_time = f"Всего работы в офисе за этот промежуток времени:\n" \
                                 f"{office_total_days} дней{office_total_hours} часов, " \
                                 f"{office_total_minutes} минут {office_total_seconds} секунд\n\n"
        else:
            result_office_time = f"Всего работы в офисе за этот промежуток времени:\n{office_total_hours} часов, " \
                                 f"{office_total_minutes} минут {office_total_seconds} секунд\n\n"

        free_total_hours = str(free_time_total / 3600).split(".")[0]
        free_total_minutes = str((free_time_total % 3600) / 60).split(".")[0]
        free_total_seconds = str((free_time_total % 3600) % 60).split(".")[0]
        result_free_time = f"Всего свободного времени потрачено за этот промежуток времени:\n" \
                           f"{free_total_hours} часов, {free_total_minutes} минут {free_total_seconds} секунд\n\n"

        home_total_hours = str(home_total_time / 3600).split(".")[0]
        home_total_minutes = str((home_total_time % 3600) / 60).split(".")[0]
        home_total_seconds = str((home_total_time % 3600) % 60).split(".")[0]
        home_total_days = 0
        if (home_total_time / 3600) > 24:
            home_total_days = str((home_total_time / 3600) / 24).split(".")[0]
            home_total_hours = str((home_total_time / 3600) % 24).split(".")[0]
            result_home_time = f"Всего работы на дому за этот промежуток времени:\n" \
                               f"{home_total_days} дней {home_total_hours} часов, " \
                               f"{home_total_minutes} минут {home_total_seconds} секунд\n\n"
        else:
            result_home_time = f"Всего работы на дому за этот промежуток времени:\n{home_total_hours} часов, " \
                               f"{home_total_minutes} минут {home_total_seconds} секунд\n\n"

        sick_leave_total_time = str(sick_leave_total_time / 86400).split(".")[0]
        vacation_total_time = str(vacation_total_time / 86400).split(".")[0]
        result_sick_time = f"Всего на больничном, за этот промежуток, дней: {sick_leave_total_time}\n"

        if user_id is None or vacation_days is None:
            result_vacation_time = f"Всего в отпуске, за этот промежуток, дней: {vacation_total_time}\n\n"
        elif vacation_days is not None:
            result_vacation_time = f"Всего в отпуске, за этот промежуток, дней: {vacation_total_time} из {vacation_days}\n"

        neg_start_delay_hours = str(neg_work_start_delay / 3600).split(".")[0]
        result_start_delay = f"Всего опозданий за этот промежуток времени, часов: {neg_start_delay_hours}\n"
        pos_finish_delay_hours = str(pos_work_finish_delay / 3600).split(".")[0]
        result_finish_delay = f"Всего задержек после окончания рабочего дня за этот промежуток времени, часов: {pos_finish_delay_hours}"

        bot.edit_message_text(chat_id=cid, message_id=mid,
                              text=result_office_time + result_home_time + result_free_time + result_sick_time
                                   + result_vacation_time + result_start_delay + result_finish_delay,
                              reply_markup=main_menu_btn())

    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))
    finally:
        if (mySQLConnection.is_connected()):
            mycursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


def get_company_id(id):
    try:
        mySQLConnection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="mydatabase"
        )
        mycursor = mySQLConnection.cursor(buffered=True)
        get_company_id_sql = """SELECT company_id FROM users WHERE user_id = %s AND name IS NULL AND last_name IS NULL 
                                                            ORDER BY id DESC LIMIT 1"""
        mycursor.execute(get_company_id_sql, (id,))
        global my_company_id
        my_company_id = mycursor.fetchall()[0][0]
        return my_company_id
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))
    finally:
        if (mySQLConnection.is_connected()):
            mycursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


def settings_tab():
    setting_keyboard = types.InlineKeyboardMarkup()
    setting_keyboard.add(types.InlineKeyboardButton(text="График работы", callback_data="set_schedule"))
    setting_keyboard.add(types.InlineKeyboardButton(text="Время отпуска", callback_data="set_vacation_time"),
                         types.InlineKeyboardButton(text="Свободное время", callback_data="set_free_time"), )
    setting_keyboard.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    return setting_keyboard


def check_worker():
    worker_keyboard = types.InlineKeyboardMarkup()
    worker_keyboard.add(types.InlineKeyboardButton(text="Что делает сейчас", callback_data="current_status"),
                        types.InlineKeyboardButton(text="Last 30 days statistics",
                                                   callback_data="last_thirty_days_office_work_time"))
    worker_keyboard.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    return worker_keyboard


def main_menu():
    main_menu_keyboard = types.InlineKeyboardMarkup()
    main_menu_keyboard.add(types.InlineKeyboardButton(text="Налаштування", callback_data="company_settings"),
                           types.InlineKeyboardButton(text="Статистика", callback_data="company_stats"),
                           types.InlineKeyboardButton(text="Рейтинг", callback_data="company_rating"))
    # main_menu_keyboard.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    return main_menu_keyboard


def statistics():
    stats_keyboard = types.InlineKeyboardMarkup()
    stats_keyboard.add(types.InlineKeyboardButton(text="Всей компании", callback_data="whole_company_stats"),
                       types.InlineKeyboardButton(text="Каждому работнику", callback_data="worker_stats"))
    stats_keyboard.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    return stats_keyboard


def main_menu_btn():
    main_menu_button = types.InlineKeyboardMarkup()
    main_menu_button.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
    return main_menu_button


@bot.callback_query_handler(func=lambda call: True)
def show_workers(call):
    cid = call.message.chat.id
    workers_names(cid)
    names_keyboard = types.InlineKeyboardMarkup()
    for name in names:
        names_keyboard.add(types.InlineKeyboardButton(text=name, callback_data=name))
    names_keyboard.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))

    for name in names:
        if call.data == name:
            global current_name
            current_name = name
            # bot.send_message(call.message.chat.id, name, reply_markup=watch_worker())
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=name,
                                  reply_markup=check_worker())
            return current_name
            break

    if call.data == "main_menu":
        userStep[cid] = 0
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Main Menu",
                              reply_markup=main_menu())

    elif call.data == "company_settings":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Установить: ",
                              reply_markup=settings_tab())

    elif call.data == "set_schedule":
        userStep[cid] = 1
        bot.send_message(call.message.chat.id, "ОК. Напишите мне график для вашей компании. "
                                               "Пожалуйста, используйте следующий формат, где:\n"
                                               "Начало раб.дня - 23:59:59 и Конец раб.дня - 23:59:59\n\n"
                                               "<Начало раб.дня><ПРОБЕЛ><Конец раб.дня>", reply_markup=main_menu_btn())

    elif call.data == "set_vacation_time":
        userStep[cid] = 2
        bot.send_message(call.message.chat.id,
                         "ОК. Напишите мне выделенное время в год на отпуск для сотрудников вашей "
                         "компании. Пожалуйста, введите время в СУТКАХ:",
                         reply_markup=main_menu_btn())

    elif call.data == "set_free_time":
        userStep[cid] = 3
        bot.send_message(call.message.chat.id,
                         "ОК. Напишите мне выделенное свободное время в год для сотрудников вашей "
                         "компании. Пожалуйста, введите время в ЧАСАХ:",
                         reply_markup=main_menu_btn())

    elif call.data == "company_stats":
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выбрать статистику по:",
                              reply_markup=statistics())

    elif call.data == 'worker_stats':
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                              text="Выбрать статистику по:",
                              reply_markup=names_keyboard)

    elif call.data == 'whole_company_stats':
        main_menu_button = types.InlineKeyboardMarkup()
        main_menu_button.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
        company_stats_select_keyboard = types.InlineKeyboardMarkup()
        company_stats_select_keyboard.add(types.InlineKeyboardButton(text="За все время:",
                                                                     callback_data="whole_company_all_time"),
                                          types.InlineKeyboardButton(text="За последние 30 дней:",
                                                                     callback_data="whole_company_thirty_days"))
        company_stats_select_keyboard.add(types.InlineKeyboardButton(text="Главное меню", callback_data="main_menu"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Вся компания",
                              reply_markup=company_stats_select_keyboard)
    elif call.data == "whole_company_all_time":
        stat_calc(call.message.chat.id, call.message.message_id, None, None)
    elif call.data == "whole_company_thirty_days":
        thirty_days_back = datetime.datetime.now() - datetime.timedelta(days=30)
        stat_calc(call.message.chat.id, call.message.message_id, thirty_days_back, None)

    elif call.data == "current_status":
        try:
            get_company_id(call.message.chat.id)
            mySQLConnection = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="mydatabase"
            )
            mycursor = mySQLConnection.cursor(buffered=True)
            worker_name = current_name.split(" ")[0]
            worker_last_name = current_name.split(" ")[1]
            sql = """SELECT user_id FROM users WHERE name = %s AND last_name = %s LIMIT 1"""
            mycursor.execute(sql, (worker_name, worker_last_name,))
            userId = mycursor.fetchall()[0][0]
            try:
                sql_status = """SELECT status_id FROM workers WHERE user_id = %s AND company_id = %s
                                    AND arrival_time IS NOT NULL AND departure_time IS NULL ORDER BY id DESC LIMIT 1"""
                mycursor.execute(sql_status, (userId, my_company_id,))
                status_id = mycursor.fetchall()[0][0]
            except:
                bot.answer_callback_query(call.id, "Человек дома отдыхает")
                status_id = 6
            try:
                if status_id == 1:
                    bot.answer_callback_query(call.id, "In da office")
                elif status_id == 2:
                    bot.answer_callback_query(call.id, "Private time")
                elif status_id == 3:
                    bot.answer_callback_query(call.id, "Home work")
                elif status_id == 4:
                    bot.answer_callback_query(call.id, "Человек на больничном")
                elif status_id == 5:
                    bot.answer_callback_query(call.id, "Человек в отпуске")
                else:
                    bot.answer_callback_query(call.id, "Человек дома отдыхает")
            except:
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                                      text=str(status_id),
                                      reply_markup=names_keyboard)
            finally:
                mySQLConnection.commit()
        except mysql.connector.Error as error:
            print("Failed to get record from MySQL table: {}".format(error))
        finally:
            if (mySQLConnection.is_connected()):
                mycursor.close()
                mySQLConnection.close()
                print("MySQL connection is closed")

    elif call.data == "last_thirty_days_office_work_time":
        try:
            get_company_id(call.message.chat.id)
            mySQLConnection = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="mydatabase"
            )
            mycursor = mySQLConnection.cursor(buffered=True)
            worker_name = current_name.split(" ")[0]
            worker_last_name = current_name.split(" ")[1]
            sql = """SELECT user_id FROM users WHERE name = %s AND last_name = %s ORDER BY id DESC LIMIT 1"""
            mycursor.execute(sql, (worker_name, worker_last_name,))
            userId = mycursor.fetchall()[0][0]
            print("user_id" + str(userId))
            thirty_days_back = datetime.datetime.now() - datetime.timedelta(days=30)
            stat_calc(call.message.chat.id, call.message.message_id, thirty_days_back, userId)
            # dateNow = datetime.datetime.now()
            # status_id = 1
            # sql = """SELECT time_difference FROM workers WHERE user_id = %s AND status_id = %s AND company_id = %s
            #                 AND DATE(arrival_time) between %s and %s """
            # mycursor.execute(sql, (userId, status_id, my_company_id, thirty_days_back, dateNow,))
            # result = mycursor.fetchall()
            # total_seconds_time = 0
            # for result[0] in result:
            #     if isinstance(result[0][0], int):
            #         total_seconds_time += result[0][0]
            #         # print("ssssssss: " + str(result))
            # total_hours = str(total_seconds_time / 3600).split(".")[0]
            # total_minutes = str((total_seconds_time % 3600) / 60).split(".")[0]
            # total_seconds = str((total_seconds_time % 3600) % 60).split(".")[0]
            # total_days = 0
            # if (total_seconds_time / 3600) > 24:
            #     total_days = str((total_seconds_time / 3600) / 24).split(".")[0]
            #     total_hours = str((total_seconds_time / 3600) % 24).split(".")[0]
            #     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            #                           text=str(
            #                               current_name) + f"\n\nВремя работы за 30 дней: \n{total_days} дней\n{total_hours} часов\n"
            #                                               f"{total_minutes} минут\n{total_seconds} секунд",
            #                           reply_markup=names_keyboard)
            # else:
            #     bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
            #                           text=str(
            #                               current_name) + f"\n\nВремя работы за 30 дней: \n{total_hours} часов\n{total_minutes} минут\n{total_seconds} секунд",
            #                           reply_markup=names_keyboard)
            # mySQLConnection.commit()
        except mysql.connector.Error as error:
            print("Failed to get record from MySQL table: {}".format(error))
        finally:
            if (mySQLConnection.is_connected()):
                mycursor.close()
                mySQLConnection.close()
                print("MySQL connection is closed")


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def set_schedule(m):
    try:
        cid = m.chat.id
        val = list(m.text.split(' '))
        val.append(cid)
        mySQLConnection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="mydatabase"
        )
        mycursor = mySQLConnection.cursor(buffered=True)
        sql = """UPDATE users SET work_start = %s, work_finish = %s WHERE user_id = %s AND name IS NULL 
                            AND last_name IS NULL ORDER BY id DESC"""
        mycursor.execute(sql, val)
        mySQLConnection.commit()
        userStep[cid] = 0
        bot.send_message(cid,
                         text=f"Отлично, установил время начала работы как:\n{val[0]}\nИ конец рабочего дня как:\n{val[1]}",
                         reply_markup=main_menu_btn())
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))
        print("айди: " + str(cid) + "\nкод ошибки: " + str(error))
        bot.send_message(cid, text="Что то пошло не так. "
                                   "Пожалуйста, используйте следующий формат, где:\n"
                                   "Начало раб.дня - 23:59:59 и Конец раб.дня - 23:59:59\n\n"
                                   "<Начало раб.дня><ПРОБЕЛ><Конец раб.дня>", reply_markup=main_menu_btn())
    finally:
        if (mySQLConnection.is_connected()):
            mycursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 2)
def set_vacation(m):
    cid = m.chat.id
    val = m.text
    if val.isdigit():
        try:
            mySQLConnection = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="mydatabase"
            )

            mycursor = mySQLConnection.cursor(buffered=True)
            sql = """UPDATE users SET vacation_time_days = %s WHERE user_id = %s AND name IS NULL 
                                        AND last_name IS NULL ORDER BY id DESC"""
            mycursor.execute(sql, (val, cid,))
            mySQLConnection.commit()
            userStep[cid] = 0
            bot.send_message(cid,
                             text=f"Отлично, установил максимальное время отпуска в сутках как:\n{val}",
                             reply_markup=main_menu_btn())
        except mysql.connector.Error as error:
            print("Failed to get record from MySQL table: {}".format(error))
            bot.send_message(cid, text="Что то пошло не так. Пожалуйста, введите число, которое "
                                       "будет обозначать количество суток, выделенное на отдых сотрудника",
                             reply_markup=main_menu_btn())
        finally:
            if (mySQLConnection.is_connected()):
                mycursor.close()
                mySQLConnection.close()
                print("MySQL connection is closed")
    else:
        bot.send_message(cid, text="Что то пошло не так. Пожалуйста, введите число, которое "
                                   "будет обозначать количество суток, выделенное на отдых сотрудника",
                         reply_markup=main_menu_btn())


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 3)
def set_free_time(m):
    cid = m.chat.id
    val = m.text
    if val.isdigit():
        try:
            mySQLConnection = mysql.connector.connect(
                host="localhost",
                user="root",
                passwd="",
                database="mydatabase"
            )

            mycursor = mySQLConnection.cursor(buffered=True)
            sql = """UPDATE users SET free_time_hours = %s WHERE user_id = %s AND name IS NULL 
                                        AND last_name IS NULL ORDER BY id DESC"""
            mycursor.execute(sql, (val, cid,))
            mySQLConnection.commit()
            userStep[cid] = 0
            bot.send_message(cid,
                             text=f"Отлично, установил максимальное свободное время в сутках как:\n{val}",
                             reply_markup=main_menu_btn())
        except mysql.connector.Error as error:
            print("Failed to get record from MySQL table: {}".format(error))
            bot.send_message(cid, text="Что то пошло не так. Пожалуйста, введите число, которое "
                                       "будет обозначать количество часов, которое будет установлено как свободное время сотрудника",
                             reply_markup=main_menu_btn())
        finally:
            if (mySQLConnection.is_connected()):
                mycursor.close()
                mySQLConnection.close()
                print("MySQL connection is closed")
    else:
        bot.send_message(cid, text="Что то пошло не так. Пожалуйста, введите число, которое "
                                   "будет обозначать количество часов, которое будет установлено как свободное время сотрудника",
                         reply_markup=main_menu_btn())


@bot.message_handler(commands=['workers'])
def get_name_by_user_id(m):
    cid = m.chat.id
    workers_names()
    names_keyboard = types.InlineKeyboardMarkup()
    for name in names:
        names_keyboard.add(types.InlineKeyboardButton(text=name, callback_data=name))
    bot.send_message(cid, "Your Employees: ", reply_markup=names_keyboard)
    print(type(names))
    print(names)
    return names_keyboard
    # userStep[cid] = 2


# @bot.message_handler(commands=['signupcompany'])
# def sign_up_company(m):
#     get_company_id()
#     print(company_id)
#     mycursor = mydb.cursor()
#     sql = """INSERT INTO users (company_id) VALUES (%s)"""
#     mycursor.execute(sql, (company_id,))
#     mydb.commit()
#     bot.send_message(m.chat.id, "Все занёс, gl")
#     return company_id

# company_id = random.randint(1000000, 9999999)
# sql = """SELECT company_id from users"""
#
# print("\n" + str(company_id))


@bot.message_handler(commands=['start'])
def start_function(m):
    cid = m.chat.id
    try:
        mySQLConnection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="mydatabase"
        )
        mycursor = mySQLConnection.cursor(buffered=True)
        sql = """SELECT company_id FROM users WHERE user_id = %s ORDER BY id DESC LIMIT 1"""
        mycursor.execute(sql, (cid,))
        company_token = mycursor.fetchone()[0]
        print(company_token)
        mySQLConnection.commit()
        bot.send_message(m.chat.id,
                         text="Компания уже зарегистрирована, напоминаем, ваш токен:\n<pre>" + str(company_token) +
                              "</pre>\nСохраните этот токен, пожалуйста",
                         parse_mode='HTML', reply_markup=main_menu())
    except:
        mySQLConnection = mysql.connector.connect(
            host="localhost",
            user="root",
            passwd="",
            database="mydatabase"
        )
        mycursor = mySQLConnection.cursor(buffered=True)
        sql = """SELECT company_id from users"""
        mycursor.execute(sql)
        company_token = random.randint(1000000, 9999999)
        # company_id = int(9811344)
        result = mycursor.fetchall()
        for i in result:
            while company_token == i:
                company_token = random.randint(1000000, 9999999)
                break
        sql = """INSERT INTO users (user_id, company_id) VALUES (%s, %s)"""
        mycursor.execute(sql, (cid, company_token,))
        mySQLConnection.commit()
        # bot.send_message(m.chat.id, text="Компания зарегистрирована, ваш токен:\n<pre>" + str(company_token) +
        #                                  "</pre>\nСохраните этот токен, пожалуйста",
        #                  parse_mode='HTML', reply_markup=main_menu())
        bot.send_message(cid, text="Компания зарегистрирована, пожалуйста, запомните ваш токен:\n<pre>" +
                                   str(company_token) + "</pre>\nСохраните этот токен, пожалуйста",
                         parse_mode='HTML', reply_markup=main_menu())
    finally:
        if (mySQLConnection.is_connected()):
            mycursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


if __name__ == '__main__':
    bot.polling(none_stop=True)
