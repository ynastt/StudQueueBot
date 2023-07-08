import telebot
from telebot import types
import psycopg2
from configparser import ConfigParser
import datetime
import data_storage as db
import re

# API_TOKEN = '6042118462:AAFSsuIPOcaRocGuT9ImTnuaR8yXgy-_7e0'
bot = telebot.TeleBot(API_TOKEN)

def config(filename='../configs/database.ini', section='postgresql'):
    parser = ConfigParser()
    parser.read(filename)
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


def connectDB():
    conn = None
    try:
        params = config()
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        cur = conn.cursor()
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    return conn, cur
    

@bot.message_handler(commands=['start'])
def start(message):
    db.auth = False
    db.subj_choice = False
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👋 Привет, запиши меня в очередь")
    markup.add(btn1)
    bot.send_message(message.from_user.id, "👋 - Привет, Я - бот-помощник для организации очереди на сдачу лабораторных работ! Для записи в очередь нажми на кнопку ниже", reply_markup=markup)
    

@bot.message_handler(commands=['help'])
def start(message):
    bot.send_message(message.from_user.id, "Этот бот создан того, чтобы студенты могли организовать очередь на сдачу лабораторных работ!\nДля запуска напиши сообщение /start")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == '👋 Привет, запиши меня в очередь':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Войти в электронный дневник')
        markup.add(btn1)
        bot.send_message(message.from_user.id, '❗Для записи в очередь необходимо авторизоваться в электронном дневнике студента', reply_markup=markup)
    
    elif message.text == 'Войти в электронный дневник':
        bot.send_message(message.from_user.id, 'Введите логин:')
        conn, cur = connectDB()
        cur.execute('SELECT * from Users')
        usrs = cur.fetchall()
        for user in usrs:
            db.user_data.add(user[1])
        cur.execute('SELECT SubjectID, Description from Subject')
        subjects = cur.fetchall()
        for s in subjects:
            db.subj_data[s[1]] = s[0] 
        cur.close()
        conn.close()
    
    elif message.text in db.user_data and not db.auth:
        db.subj_choice = False
        db.login = message.text
        conn, cur = connectDB()
        cur.execute('SELECT StudentID from Student where user_id = (SELECT UserID from Users where Login=%s)', (db.login,))
        db.current_student_id = cur.fetchone()[0]
        # print('current user-student:',db.login, db.current_student_id)
        # print(message.text)
        # print(message.text in db.user_data)
        db.auth = True
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in db.subj_data.keys():
            # print(s)
            btn1 = types.KeyboardButton(s)
            markup.add(btn1)
        bot.send_message(message.from_user.id, 'Авторизация прошла успешно! Выберете предмет, по которому Вы сдаете работу', reply_markup=markup)    
    
    elif message.text == 'Вернуться в главное меню':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in db.subj_data.keys():
            # print(s)
            btn1 = types.KeyboardButton(s)
            markup.add(btn1)
        bot.send_message(message.from_user.id, 'Выберете предмет, по которому Вы сдаете работу', reply_markup=markup)
    
    elif message.text not in db.user_data and not db.auth:
        # print(message.text in db.user_data)
        # print(db.user_data)
        bot.send_message(message.from_user.id, 'Вы не зарегистрированы в электронном дневнике.\nК сожалению, вы не можете быть записаны в очередь.')
         
    elif message.text in db.subj_data.keys() and not db.subj_choice:
        db.subj_choice = True
        db.current_subject = db.Subject(db.subj_data[message.text], message.text)
        # print(db.current_subject.name, db.current_subject.id)
        conn, cur = connectDB()
        cur.execute('SELECT * from Queue where subject_id = %s and StartDate >= %s',
                     (db.current_subject.id, datetime.datetime.now().date()))
        active_queues = cur.fetchall()
        # print(len(active_queues))
        if len(active_queues) == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('Создать очередь на сегодня')
            markup.add(btn1)
            bot.send_message(message.from_user.id, 'Сейчас нет активных очередей по данному предмету.\nХотите создать новую очередь?', reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for q in active_queues:
                # print(q)
                date = q[1].date()
                time = q[1].time()
                name = 'Очередь {day}-{month}-{year} {hour}:{min}'.format(day=date.day, month=date.month, 
                                                                          year=date.year, hour=time.hour, min=time.minute)
                btn1 = types.KeyboardButton(name)
                markup.add(btn1)
            markup.add(types.KeyboardButton('Создать очередь на сегодня'))
            bot.send_message(message.from_user.id, 'Выберите одну из активных очередей', reply_markup=markup)
        cur.close()
        conn.close()
    
    elif message.text == 'Создать очередь на сегодня':
        conn, cur = connectDB()
        queue_date = datetime.datetime.now()
        date = queue_date.date()
        time = queue_date.time()
        text = 'Очередь {day}-{month}-{year} {hour}:{min}'.format(day=date.day,
                             month=date.month, year=date.year, hour=time.hour, min=time.minute)
        db.queue_date[text] = queue_date
        print(text, db.queue_date[text])
        cur.execute("INSERT INTO Queue(QueueID, StartDate, subject_id) VALUES (gen_random_uuid(), %s, %s)", 
                    (queue_date, db.current_subject.id))
        cur.execute('select QueueID from Queue where StartDate = %s', (queue_date,))
        cqid = cur.fetchone()[0]
        cur.close()
        conn.commit()
        conn.close()
        db.current_queue.id = cqid
        db.current_queue.date = queue_date
        db.current_queue.subject_id = db.current_subject.id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Записаться')
        btn2 = types.KeyboardButton('Вернуться к списку очередей')
        markup.add(btn1, btn2) 
        bot.send_message(message.from_user.id, text + ' создана', reply_markup=markup)
    
    elif re.fullmatch("Очередь \d{1,2}\-\d{1,2}\-\d{4} \d{1,2}\:\d{1,2}", message.text):
        print(db.queue_date)
        norm_date = db.queue_date[message.text]
        conn, cur = connectDB()
        cur.execute('SELECT * from Queue where StartDate = %s', (norm_date,))
        cur_queue = cur.fetchone()
        db.current_queue.id = cur_queue[0]
        db.current_queue.date = cur_queue[1]
        db.current_queue.subject_id = db.current_subject.id
        cur.close()
        conn.close()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Записаться')
        btn2 = types.KeyboardButton('Вернуться к списку очередей')
        markup.add(btn1, btn2)
        bot.send_message(message.from_user.id, 'Для записи в текущую очередь нажмите кнопку "Записаться"', reply_markup=markup)
    
    elif message.text == 'Вернуться к списку очередей':
        conn, cur = connectDB() 
        cur.execute('SELECT * from Queue where subject_id = %s and StartDate >= %s',
                     (db.current_subject.id, datetime.datetime.now().date()))
        active_queues = cur.fetchall()
        if len(active_queues) == 0:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('Создать очередь на сегодня')
            markup.add(btn1)
            bot.send_message(message.from_user.id, 'Сейчас нет активных очередей по данному предмету.\nХотите создать новую очередь?', reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            for q in active_queues:
                print(q)
                date = q[1].date()
                time = q[1].time()
                name = 'Очередь {day}-{month}-{year} {hour}:{min}'.format(day=date.day, month=date.month, 
                                                                          year=date.year, hour=time.hour, min=time.minute)
                btn1 = types.KeyboardButton(name)
                markup.add(btn1)
            markup.add(types.KeyboardButton('Создать очередь на сегодня'))
            bot.send_message(message.from_user.id, 'Выберите одну из активных очередей', reply_markup=markup)
        cur.close()
        conn.close()
    
    elif message.text == 'Записаться':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Подтвердить запись')
        btn2 = types.KeyboardButton('Посмотреть очередь')
        markup.add(btn1, btn2)
        bot.send_message(message.from_user.id, 'Для предпросмотра очереди нажмите кнопку "Посмотреть очередь"\n\nДля подтверждения записи - "Подтвердить запись"', reply_markup=markup)
    
    elif message.text == 'Посмотреть очередь':
        conn, cur = connectDB()
        cur.execute('SELECT NumInQueue, student_id from StudentQueue where queue_id = %s order by NumInQueue', (db.current_queue.id,))
        cur_queue = cur.fetchall()
        # cur.execute('select * from StudentInQueue where queue_id = %s', (db.current_queue.id,))
        # cur_queue = cur.fetchall()
        print(cur_queue)
        print(db.current_queue.id)
        if len(cur_queue) == 0:
            queue_list = 'Очередь пуста. Запишитесь первым!'
        else:    
            queue_list = ''
            for s in cur_queue:
                cur.execute('SELECT Surname, StudentName, group_id from Student where StudentID = %s', (s[1],))
                student = cur.fetchone()
                cur.execute('SELECT GroupName from StudentGroup where GroupID = %s', (student[2],))
                g = cur.fetchone()
                stud = '{surname} {name} {group}'.format(surname=student[0], name=student[1], group=g[0])
                queue_list += '{num}. {name}\n'.format(num=s[0], name=stud)
        cur.close()
        conn.close()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Подтвердить запись')
        btn2 = types.KeyboardButton('Посмотреть очередь')
        btn3 = types.KeyboardButton('Вернуться к списку очередей')
        markup.add(btn1, btn2, btn3)
        if len(cur_queue) > 0:
            btn = types.KeyboardButton('Удалить запись')
            markup.add(btn)
        bot.send_message(message.from_user.id, queue_list, reply_markup=markup)
    
    elif message.text == 'Подтвердить запись':
        conn, cur = connectDB()
        cur.execute('SELECT 1 FROM StudentInQueue WHERE student_id = %s and queue_id = %s', 
                    (db.current_student_id, db.current_queue.id,))
        res = cur.fetchall()
        
        if len(res) == 1:
            cur.close()
            conn.close()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('Посмотреть очередь')
            btn2 = types.KeyboardButton('Вернуться в главное меню')
            btn3 = types.KeyboardButton('Вернуться к списку очередей')
            markup.add(btn1, btn2, btn3)
            date = db.current_queue.date.date()
            time = db.current_queue.date.time()
            text = 'Вы не можете записаться в очередь второй раз!\nВы уже присутствуете в очереди {day}-{month}-{year} {hour}:{min}'.format(
                day=date.day, month=date.month, year=date.year, hour=time.hour, min=time.minute)
            bot.send_message(message.from_user.id, text, reply_markup=markup)
        else:
            cur.execute('INSERT INTO StudentInQueue(student_id, queue_id, NumInQueue) VALUES (%s, %s, (SELECT COUNT(*) + 1 from StudentInQueue where queue_id = %s))', 
                    (db.current_student_id, db.current_queue.id, db.current_queue.id))
            cur.close()
            conn.commit()
            conn.close()
            # conn, cur = connectDB()
            # cur.execute('select * from StudentInQueue where queue_id = %s', (db.current_queue.id,))
            # al = cur.fetchall()
            # print(al)
            # print(db.current_queue.id)
            # cur.close()
            # conn.close()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn1 = types.KeyboardButton('Посмотреть очередь')
            btn2 = types.KeyboardButton('Вернуться в главное меню')
            markup.add(btn1, btn2)
            date = db.current_queue.date.date()
            time = db.current_queue.date.time()
            text = 'Вы записаны в очередь {day}-{month}-{year} {hour}:{min}'.format(
                day=date.day, month=date.month, year=date.year, hour=time.hour, min=time.minute)
            
            bot.send_message(message.from_user.id, text, reply_markup=markup)
    elif message.text == 'Удалить запись':
        conn, cur = connectDB()
        cur.execute('delete from StudentQueue where student_id =%s', (db.current_student_id,))
        conn.commit()
        cur.close()
        conn.close()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton('Посмотреть очередь')
        btn2 = types.KeyboardButton('Вернуться в главное меню')
        markup.add(btn1, btn2)
        date = db.current_queue.date.date()
        time = db.current_queue.date.time()
        text = 'Вы удалены из очереди  {day}-{month}-{year} {hour}:{min}'.format(
                day=date.day, month=date.month, year=date.year, hour=time.hour, min=time.minute)
        bot.send_message(message.from_user.id, text, reply_markup=markup)

        


if __name__ == '__main__':
    print("START...")
    bot.polling(none_stop=True, interval=0)

