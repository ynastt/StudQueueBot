drop table Users cascade;
CREATE TABLE IF NOT EXISTS Users (
	UserID UUID PRIMARY KEY,
	Login VARCHAR(50) NOT NULL,
	Passw VARCHAR(50) NOT NULL,
	UsersRights INT NOT NULL,
	CONSTRAINT user_unique UNIQUE(Login) --именование ограничение табилцы
);

CREATE TABLE IF NOT EXISTS StudentGroup (
	GroupID UUID PRIMARY KEY,
	GroupName VARCHAR NOT NULL,
	YearOfAdmission INT NOT NULL,
	Course INT NOT NULL,
	AmountOfStudents INT NOT NULL
);

CREATE TABLE IF NOT EXISTS Student (
	StudentID UUID PRIMARY KEY,
	StudentName VARCHAR(50) NOT NULL,
	Surname VARCHAR(50) NOT NULL,
	Patronymic VARCHAR(50),
	Email VARCHAR(255) UNIQUE NOT NULL,
	Phone VARCHAR(11) NOT NULL,
	YearOfAdmission INT NOT NULL,
	PassedCourses INT NOT NULL,
	NumInGroup INT NOT NULL,
	user_id UUID NOT NULL REFERENCES Users(UserID),
	group_id UUID NOT NULL REFERENCES StudentGroup(GroupID),
	CONSTRAINT student_unique UNIQUE(user_id, group_id)
);

CREATE TABLE IF NOT EXISTS Subject (
	SubjectID UUID PRIMARY KEY,
	Description TEXT NOT NULL UNIQUE,  --название предмета
	SubjectProgram TEXT NOT NULL, 
	NumberOfHours INT NOT NULL,
	NumberOfCredits INT NOT NULL, 
	CONSTRAINT subject_unique UNIQUE(SubjectID, Description)
);

CREATE TABLE IF NOT EXISTS Queue (
	QueueID UUID PRIMARY KEY,
	StartDate timestamp with time zone NOT NULL,
	subject_id UUID NOT NULL REFERENCES Subject(SubjectID) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS StudentInQueue (
	student_id UUID NOT NULL REFERENCES Student(StudentID) ON DELETE CASCADE,
	queue_id UUID NOT NULL REFERENCES Queue(QueueID) ON DELETE CASCADE,
	NumInQueue Int NOT NULL,
	PRIMARY KEY(student_id, queue_id)
);

drop view if exists StudentQueue
create view StudentQueue AS 
	SELECT student_id, queue_id, NumInQueue 
	FROM StudentInQueue
