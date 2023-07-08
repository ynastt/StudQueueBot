from enum import Enum

user_data = set()
subj_data = {}
auth = False
subj_choice = False
login = ''
current_student_id = ''
queue_date = {}

class Subject:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class Queue:
    def __init__(self, id, date, subject_id):
        self.id = id
        self.date = date
        self.subject_id =  subject_id

class StudentInQueue:
    def __init__(self, student_id, queue_id, num):
        self.student_id = student_id
        self.queue_id = queue_id
        self.num = num

current_subject = Subject('', '')
current_queue = Queue('','','')