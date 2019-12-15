import telebot
from telebot import types
import mysql.connector
import datetime
import time

mySQLConnection = mysql.connector.connect(host='localhost',
                                          database='mydatabase',
                                          user='root',
                                          password='')

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
    'arrive': 'Вводить по прибытию на работу',
    'vacation': 'Vacation or sick leave',
    'sign_up': 'Sign up yourself'
}

TOKEN = "INSERT TOKEN PLEASE"                                           #TODO INSERT TOKEN
bot = telebot.TeleBot(TOKEN)
bot.set_update_listener(listener)  # register listener


def keyboard_arrive():
    main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    main_markup.add(types.KeyboardButton('Office work start'), types.KeyboardButton('Home work start'))
    main_markup.add(types.KeyboardButton('Ушел на паузу'), types.KeyboardButton('Назад 🦖'))
    return main_markup


def keyboard_departure():
    main_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    main_markup.add(types.KeyboardButton('Private time'), types.KeyboardButton('Leave work'))
    main_markup.add(types.KeyboardButton('Назад 🦖'))
    return main_markup


def use_it_asap():
    use_it_asap_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    use_it_asap_keyboard.add(types.KeyboardButton('Вышел с больничного 🤕'), types.KeyboardButton('Вышел с больничного 🤕'))
    use_it_asap_keyboard.add(types.KeyboardButton('Назад 🦖'))
    return use_it_asap_keyboard


def assurance():
    assurance_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    assurance_keyboard.add(types.KeyboardButton('Yes'), types.KeyboardButton('No'))


hideBoard = types.ReplyKeyboardRemove()


def get_current_time():
    import datetime
    global utc_plustwo_time
    # utc_plustwo_time = datetime.datetime.now() + datetime.timedelta(hours=2)
    utc_plustwo_time = datetime.datetime.now()
    # utc_plustwo_time = datetime.datetime.now() - datetime.timedelta(hours=5)
    return utc_plustwo_time

def get_company_id(m):
    try:
        cid = m.chat.id
        print(cid)
        global my_company_id
        mySQLConnection = mysql.connector.connect(host='localhost',
                                                  database='mydatabase',
                                                  user='root',
                                                  password='')
        mycursor = mySQLConnection.cursor(buffered=True)
        sql = """SELECT company_id FROM users WHERE user_id = %s ORDER BY id DESC LIMIT 1"""
        mycursor.execute(sql, (cid,))
        my_company_id = mycursor.fetchall()[0][0]
        mySQLConnection.commit()
        print(my_company_id)
        return my_company_id
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))
    finally:
        if (mySQLConnection.is_connected()):
            mycursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


def sign_up_name_and_last_name(msg):
    try:
        mySQLConnection = mysql.connector.connect(host='localhost',
                                                  database='mydatabase',
                                                  user='root',
                                                  password='')
        mycursor = mySQLConnection.cursor(buffered=True)
        user_id = msg.chat.id
        val = list(msg.text.split(' '))
        val.append(user_id)
        sql = """INSERT INTO users (name, last_name, company_id, user_id) VALUES (%s, %s, %s, %s)"""
        mycursor.execute(sql, val)
        bot.send_message(msg.chat.id, "Записал!")
        mySQLConnection.commit()
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))
        bot.send_message(msg.chat.id, "Incorrect input, please try again - Your name, last name and Company ID")
    finally:
        if (mySQLConnection.is_connected()):
            mycursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


def get_office_time(msg):
    from datetime import datetime
    cid = msg.chat.id
    try:
        mySQLConnection = mysql.connector.connect(host='localhost',
                                                  database='mydatabase',
                                                  user='root',
                                                  password='')

        cursor = mySQLConnection.cursor(buffered=True)
        sql_get_departure_time = """SELECT departure_time FROM workers WHERE user_id = %s ORDER BY id DESC LIMIT 1"""
        cursor.execute(sql_get_departure_time, (cid,))
        exception_record_departure = cursor.fetchall()

        sql_get_arrival_time = """SELECT arrival_time FROM workers WHERE user_id = %s ORDER BY id DESC LIMIT 1"""
        cursor.execute(sql_get_arrival_time, (cid,))
        exception_record_arrival = cursor.fetchall()
        office_time = exception_record_departure[0][0] - exception_record_arrival[0][0]
        office_time = office_time.total_seconds()
        print("right office time: " + str(office_time))
        sql_set_office_time = """UPDATE workers SET time_difference = %s WHERE user_id = %s ORDER BY id DESC LIMIT 1"""
        cursor.execute(sql_set_office_time, (office_time, cid,))
        bot.send_message(msg.chat.id, "office time: " + str(office_time))
        mySQLConnection.commit()
    except mysql.connector.Error as error:
        print("Failed to get record from MySQL table: {}".format(error))
        bot.send_message(cid, "Error: {}".format(error))
    finally:
        if (mySQLConnection.is_connected()):
            cursor.close()
            mySQLConnection.close()
            print("MySQL connection is closed")


@bot.message_handler(commands=['start'])
def command_start(m):
    cid = m.chat.id
    if cid not in knownUsers:  # if user hasn't used the "/start" command yet:
        knownUsers.append(cid)  # save user id, so you could broadcast messages to all users of this bot later
        userStep[cid] = 0  # save user id and his current "command level", so he can use the "/getImage" command
        bot.send_message(cid, "Please, register yourself\n/sign_up, \nif you haven't done this yet!")
        command_help(m)  # show the new user the help page
    else:
        bot.send_message(cid, "I already know you, hope you are registered\n/sign_up\n already!")


@bot.message_handler(commands=['help'])
def command_help(m):
    cid = m.chat.id
    help_text = "The following commands are available: \n"
    for key in commands:  # generate help text out of the commands dictionary defined at the top
        help_text += "/" + key + ": "
        help_text += commands[key] + "\n"
    bot.send_message(cid, help_text)  # send the generated help page


@bot.message_handler(commands=['arrive'])
def command_arrive(m):
    cid = m.chat.id
    bot.send_message(cid, "Please choose arrive status now", reply_markup=keyboard_arrive())  # show the keyboard
    userStep[cid] = 1  # set the user to the next step (expecting a reply in the listener now)


def arrival_keyboard():
    pause_leave_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    pause_leave_keyboard.add(types.KeyboardButton('Выйти на паузу'), types.KeyboardButton('Leave work'))
    return pause_leave_keyboard

@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 1)
def msg_arrive_status_select(m):
    cid = m.chat.id
    text = m.text
    try:
        if text == "Office work start":
            try:
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                from datetime import datetime
                get_company_id(m)
                # delete this function if doesnt work correctly
                get_current_time()
                get_work_start_time = """SELECT work_start FROM users WHERE company_id = %s
                                        AND name IS NULL AND last_name IS NULL ORDER BY id DESC LIMIT 1"""
                mycursor.execute(get_work_start_time, (my_company_id,))
                record = mycursor.fetchall()
                records = str(record[0][0])
                timeNow = str(utc_plustwo_time.time())[0:8]
                diff = datetime.strptime(timeNow, '%H:%M:%S') - datetime.strptime(records, '%H:%M:%S')
                # bot.send_message(msg.chat.id, "Записал, оставайся на работе как можно дольше!")
                datetimeNow = utc_plustwo_time
                status_id = 1
                val = [cid, datetimeNow, diff, status_id, my_company_id]
                sql = """INSERT INTO workers (user_id, arrival_time, work_start_difference, status_id, company_id) 
                                        VALUES (%s, %s, %s, %s, %s)"""
                mycursor.execute(sql, val)
                mySQLConnection.commit()
                bot.send_message(cid, "Записал статус;\nExile, do something", reply_markup=arrival_keyboard())
                userStep[cid] = 2  # reset the users step back to 0
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так c работой в офисе" + str(error), reply_markup=hideBoard)
                userStep[cid] = 0  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Home work start":
            try:
                from datetime import datetime
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                get_company_id(m)
                # delete this function if doesnt work correctly
                get_current_time()
                get_work_start_time = """SELECT work_start FROM users WHERE company_id = %s
                                        AND name IS NULL AND last_name IS NULL ORDER BY id DESC LIMIT 1"""
                mycursor.execute(get_work_start_time, (my_company_id,))
                record = mycursor.fetchall()
                records = str(record[0][0])
                timeNow = str(utc_plustwo_time.time())[0:8]
                diff = datetime.strptime(timeNow, '%H:%M:%S') - datetime.strptime(records, '%H:%M:%S')
                # bot.send_message(msg.chat.id, "Записал, оставайся на работе как можно дольше!")
                datetimeNow = utc_plustwo_time
                status_id = 3
                val = [cid, datetimeNow, diff, status_id, my_company_id]
                sql = """INSERT INTO workers (user_id, arrival_time, work_start_difference, status_id, company_id) 
                                                VALUES (%s, %s, %s, %s, %s)"""
                mycursor.execute(sql, val)
                mySQLConnection.commit()
                bot.send_message(cid, "Записал статус - пришел на работу на дом, HF", reply_markup=arrival_keyboard())
                userStep[cid] = 2  # reset the users step back to 0
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так c работой на дому", reply_markup=hideBoard)
                userStep[cid] = 0  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Ушел на паузу":
            try:
                from datetime import datetime
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                get_company_id(m)
                # delete this function if doesnt work correctly
                get_current_time()
                # current_time = utc_plustwo_time
                # sql = """UPDATE workers SET departure_time = %s WHERE user_id = %s AND status_id = 2 ORDER BY id DESC LIMIT 1 """
                # mycursor.execute(sql, (current_time, cid,))
                # get_office_time(m)
                status_id = 2
                val = [cid, utc_plustwo_time, status_id, my_company_id]
                sql = """INSERT INTO workers (user_id, arrival_time, status_id, company_id) VALUES (%s, %s, %s, %s)"""
                mycursor.execute(sql, val)
                mySQLConnection.commit()
                pause_leave_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
                pause_leave_keyboard.add(types.KeyboardButton('Выход с паузы'))
                bot.send_message(cid, "Записал статус - Ушел на паузу", reply_markup=pause_leave_keyboard)
                userStep[cid] = 2  # reset the users step back to 0
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так c выходом на паузу", reply_markup=hideBoard)
                userStep[cid] = 0  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Назад 🦖":
            bot.send_message(cid, "Вышел на главную", reply_markup=hideBoard)
            userStep[cid] = 0
        else:
            bot.send_message(cid, "Cast yourself into oblivion!\nPlease try again")
    except:
        bot.send_message(cid, "incorrect input, try again")


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 2)
def msg_departure_status_select(m):
    cid = m.chat.id
    text = m.text
    start_work_after_pause_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    start_work_after_pause_keyboard.add(types.KeyboardButton('Start work'))
    try:
        if text == "Выйти на паузу":
            try:
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                get_company_id(m)
                # delete this function if doesnt work correctly
                get_current_time()
                # current_time = utc_plustwo_time
                sql = """UPDATE workers SET departure_time = %s WHERE (user_id = %s AND status_id = 1) 
                                                        OR (user_id = %s AND status_id = 3) ORDER BY id DESC LIMIT 1 """
                mycursor.execute(sql, (utc_plustwo_time, cid, cid,))
                get_office_time(m)
                status_id = 2
                val = [cid, utc_plustwo_time, status_id, my_company_id]
                sql = """INSERT INTO workers (user_id, arrival_time, status_id, company_id) VALUES (%s, %s, %s, %s)"""
                mycursor.execute(sql, val)
                bot.send_message(cid, "Записал статус - Ушел на паузу, take care\n"
                                      "По прибытию на работу - не забудь нажать нужную кнопку!",
                                        reply_markup=start_work_after_pause_keyboard)  # send file and hide keyboard
                # userStep[cid] = 2  # reset the users step back to 0
                mySQLConnection.commit()
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так с паузой" + str(error))
                # userStep[cid] = 2  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Leave work":
            try:
                from datetime import datetime
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                # delete this function if doesnt work correctly
                get_current_time()
                get_company_id(m)
                sql_status = """SELECT status_id FROM workers WHERE user_id = %s 
                                    AND arrival_time IS NOT NULL AND departure_time IS NULL ORDER BY id DESC LIMIT 1"""
                mycursor.execute(sql_status, (cid,))
                status_id = mycursor.fetchall()[0][0]
                get_work_finish_time = """SELECT work_finish FROM users WHERE company_id = %s
                                        AND name IS NULL AND last_name IS NULL ORDER BY id DESC LIMIT 1"""
                mycursor.execute(get_work_finish_time, (my_company_id,))
                record = mycursor.fetchall()
                record = str(record[0][0])[-8:]
                timeNow = str(utc_plustwo_time)[0:19]
                # timeNow = "2019-12-02 20:22:13"  # test time (-1)
                # timeNow = "2019-12-03 01:22:13" #test time (0)
                # timeNow = "2019-12-02 23:22:13" #test time (0)
                get_arrival_date = """SELECT DATE(arrival_time) FROM workers WHERE user_id = %s
                                        AND arrival_time IS NOT NULL AND departure_time IS NULL ORDER BY id DESC LIMIT 1"""
                mycursor.execute(get_arrival_date, (cid,))
                arrival_date = mycursor.fetchall()
                date_and_work_finish_time = str(arrival_date[0][0]) + " " + record
                timeDiff = datetime.strptime(timeNow, '%Y-%m-%d %H:%M:%S') - datetime.strptime(
                    date_and_work_finish_time, '%Y-%m-%d %H:%M:%S')
                if timeDiff.days != 0:
                    minus_right_diff = datetime.strptime(date_and_work_finish_time, '%Y-%m-%d %H:%M:%S') \
                                       - datetime.strptime(timeNow, '%Y-%m-%d %H:%M:%S')
                    timeDiff = "-" + str(minus_right_diff)[-8:]
                sql = """UPDATE workers SET departure_time = %s, work_finish_difference = %s
                                            WHERE user_id = %s AND status_id = %s ORDER BY id DESC LIMIT 1 """
                mycursor.execute(sql, (utc_plustwo_time, timeDiff, cid, status_id))
                mySQLConnection.commit()
                get_office_time(m)
                bot.send_message(cid, "Почему так рано ушел, негодяй?", reply_markup=hideBoard)
                userStep[cid] = 0
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так c работой на дому" + str(error))
                # userStep[cid] = 0  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == 'Start work':
            try:
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                get_company_id(m)
                # delete this function if doesnt work correctly
                get_current_time()
                get_status_id = """SELECT status_id FROM workers WHERE (user_id = %s AND status_id = 1) 
                                                        OR (user_id = %s AND status_id = 3) ORDER BY id DESC LIMIT 1"""
                mycursor.execute(get_status_id, (cid, cid,))
                status_id = mycursor.fetchall()[0][0]
                print("last_work_status: " + str(status_id))
                sql = """UPDATE workers SET departure_time = %s WHERE user_id = %s AND status_id = 2 ORDER BY id DESC LIMIT 1 """
                mycursor.execute(sql, (utc_plustwo_time, cid,))
                get_office_time(m)
                # status_id = 1
                val = [cid, utc_plustwo_time, status_id, my_company_id]
                sql = """INSERT INTO workers (user_id, arrival_time, status_id, company_id) VALUES (%s, %s, %s, %s)"""
                mycursor.execute(sql, val)
                bot.send_message(cid, "Записал статус - Пришел на работу после паузы!",
                                        reply_markup=arrival_keyboard())  # send file and hide keyboard
                # userStep[cid] = 2  # reset the users step back to 0
                mySQLConnection.commit()
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так с началом работы" + str(error))
                # userStep[cid] = 2  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == 'Выход с паузы':
            try:
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                get_company_id(m)
                get_current_time()
                sql = """UPDATE workers SET departure_time = %s WHERE user_id = %s AND status_id = 2 
                                                                        ORDER BY id DESC LIMIT 1"""
                mycursor.execute(sql, (utc_plustwo_time, cid,))
                mySQLConnection.commit()
                get_office_time(m)
                bot.send_message(cid, "Окей, передохнул - давай снова за работу!\n/arrive", reply_markup=hideBoard)
                userStep[cid] = 0
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        else:
            bot.send_message(cid, "Cast yourself into oblivion!\nPlease try again")
    except:
        bot.send_message(cid, "incorrect input, try again")


@bot.message_handler(commands=['sign_up'])
def sign_up(message):
    bot.send_message(message.chat.id, "Введите своё имя, фамилию и ID компании в формате\nИмя Фамилия ID")
    bot.register_next_step_handler(message, sign_up_name_and_last_name)


@bot.message_handler(commands=['vacation'])
def do_not_use_command(message):
    cid = message.chat.id
    userStep[cid] = 4
    static_markup_for_do_not_use = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton('Ухожу на больничный 🤒')
    btn2 = types.KeyboardButton('Ухожу в отпуск 🚀')
    btn3 = types.KeyboardButton('Назад 🦖')
    static_markup_for_do_not_use.add(btn1, btn2)
    static_markup_for_do_not_use.add(btn3)
    bot.send_message(cid, "Работа не волк!", reply_markup=static_markup_for_do_not_use)


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 4)
def vacation_start(m):
    cid = m.chat.id
    text = m.text

    last_step_bolnica_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    last_step_bolnica_keyboard.add(types.KeyboardButton("Вышел с больничного 🤕"))

    last_step_otpusk_keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    last_step_otpusk_keyboard.add(types.KeyboardButton("Out otpusk"))
    try:
        if text == "Ухожу на больничный 🤒":
            try:
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                # delete this function if doesnt work correctly
                get_current_time()
                status_id = 4
                get_company_id(m)
                val = [cid, utc_plustwo_time, status_id, my_company_id]
                sql = """INSERT INTO workers (user_id, arrival_time, status_id, company_id) VALUES (%s, %s, %s, %s)"""
                mycursor.execute(sql, val)
                mySQLConnection.commit()
                bot.send_message(cid, "Записал статус;\nУшел на больничный", reply_markup=last_step_bolnica_keyboard)
                userStep[cid] = 5
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так c выходом на больничный")
                userStep[cid] = 0  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Ухожу в отпуск 🚀":
            try:
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                # delete this function if doesnt work correctly
                get_current_time()
                status_id = 5
                get_company_id(m)
                val = [cid, utc_plustwo_time, status_id, my_company_id]
                sql = """INSERT INTO workers (user_id, arrival_time, status_id, company_id) VALUES (%s, %s, %s, %s)"""
                mycursor.execute(sql, val)
                mySQLConnection.commit()
                bot.send_message(cid, "Записал статус;\nУшел в отпуск", reply_markup=last_step_otpusk_keyboard)
                userStep[cid] = 5
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так c выходом в отпуск")
                userStep[cid] = 0  # reset the users step back to 0
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Назад 🦖":
            bot.send_message(cid, "Вышел на главную", reply_markup=hideBoard)
            userStep[cid] = 0
        else:
            bot.send_message(cid, "Cast yourself into oblivion!\nPlease try again")
    except:
        bot.send_message(cid, "incorrect input, try again")


@bot.message_handler(func=lambda message: get_user_step(message.chat.id) == 5)
def do_not_use_handler_finish(m):
    cid = m.chat.id
    text = m.text
    try:
        if text == "Вышел с больничного 🤕":
            try:
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                status_id = 4
                # delete this function if doesnt work correctly
                get_current_time()
                get_company_id(m)
                print(my_company_id)
                val = [utc_plustwo_time, cid, status_id, my_company_id]
                sql = """UPDATE workers SET departure_time = %s WHERE user_id = %s AND status_id = %s AND company_id = %s
                                                                    ORDER BY id DESC LIMIT 1"""
                mycursor.execute(sql, val)
                get_office_time(m)
                mySQLConnection.commit()
                bot.send_message(cid, "Уже поболел? Ok, get back to work, exile", reply_markup=hideBoard)
                # userStep[cid] = 0
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                print(error, cid)
                bot.send_message(cid, "Что-то пошло не так c выходом ИЗ больничного")
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Out otpusk":
            try:
                from datetime import datetime
                mySQLConnection = mysql.connector.connect(host='localhost',
                                                          database='mydatabase',
                                                          user='root',
                                                          password='')

                mycursor = mySQLConnection.cursor(buffered=True)
                status_id = 5
                # delete this function if doesnt work correctly
                get_current_time()
                get_company_id(m)
                print(my_company_id)
                # utc_plustwo_times = "2020-01-23 20:22:13"
                # utc_plustwo_times = datetime.strptime(utc_plustwo_times, '%Y-%m-%d %H:%M:%S')
                val = [utc_plustwo_time, cid, status_id, my_company_id]
                sql = """UPDATE workers SET departure_time = %s WHERE user_id = %s AND status_id = %s AND company_id = %s 
                                        ORDER BY id DESC LIMIT 1"""
                mycursor.execute(sql, val)
                get_office_time(m)
                bot.send_message(cid, "Уже отдохнул? Ok, get back to work, exile", reply_markup=hideBoard)
                userStep[cid] = 0
                mySQLConnection.commit()
            except mysql.connector.Error as error:
                print("Failed to get record from MySQL table: {}".format(error))
                bot.send_message(cid, "Что-то пошло не так c выходом ИЗ отпуска")
            finally:
                if (mySQLConnection.is_connected()):
                    mycursor.close()
                    mySQLConnection.close()
                    print("MySQL connection is closed")
        elif text == "Назад 🦖":
            bot.send_message(cid, "Вышел на главную", reply_markup=hideBoard)
            userStep[cid] = 5
        else:
            bot.send_message(cid, "Cast yourself into Oblivion!\nTry again please")
    except:
        bot.send_message(cid, "incorrect input, try again")


@bot.message_handler(commands=['sendLongText'])
def command_long_text(m):
    cid = m.chat.id
    get_company_id(m)
    print(my_company_id)
    # bot.send_message(cid, "If you want so...")
    # bot.send_chat_action(cid, 'typing')  # show the bot "typing" (max. 5 secs)
    # time.sleep(5)
    # bot.send_message(cid, ".")


if __name__ == '__main__':
    bot.polling(none_stop=True)
