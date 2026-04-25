PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE people (
	id INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	ordinal INTEGER NOT NULL, 
	avatar VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	updated_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);
INSERT INTO people VALUES(1,'Ariel',1,'ariel.png','2026-04-25T19:38:50Z','2026-04-25T19:38:50Z');
INSERT INTO people VALUES(2,'Asaf',2,'asaf.png','2026-04-25T19:38:59Z','2026-04-25T19:38:59Z');
INSERT INTO people VALUES(3,'Amalya',3,'amalya.png','2026-04-25T19:39:10Z','2026-04-25T19:39:10Z');
INSERT INTO people VALUES(4,'Alon',4,'alon.png','2026-04-25T19:39:20Z','2026-04-25T19:39:20Z');
INSERT INTO people VALUES(5,'Aviv',5,'aviv.png','2026-04-25T19:39:31Z','2026-04-25T19:39:31Z');
INSERT INTO people VALUES(6,'Shalom',100,'other.png','2026-04-25T19:42:48Z','2026-04-25T19:42:48Z');
CREATE TABLE chores (
	id INTEGER NOT NULL, 
	name VARCHAR NOT NULL, 
	frequency_in_weeks INTEGER NOT NULL, 
	created_at VARCHAR NOT NULL, 
	updated_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (frequency_in_weeks >= 1), 
	UNIQUE (name)
);
INSERT INTO chores VALUES(1,'Kitchen handles',7,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(2,'Bathroom: Kids''',2,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(3,'Recycling',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(4,'Bins',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(5,'Kitchen cabinets',11,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(6,'Bathroom: loft',5,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(7,'Refill soap and shampoo dispensers: showers and sinks',13,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(8,'Playroom',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(9,'Sweep walkway',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(10,'Sweep Top Stairs',2,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(11,'Sweep Bottom Stairs',2,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(12,'Coffee & Mailbox',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(13,'Toilet Paper / Tissues',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(14,'Under couch',2,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(15,'Bathroom: Entrance',2,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(16,'Pump air in balls',4,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(17,'Stainless steel in kitchen',3,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(18,'Clean garbage cans',11,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(19,'Mow Lawn',2,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(20,'Clean Windows',15,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(21,'Bathroom: master: sink & toilet',3,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(22,'Bathroom: master: shower',7,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(23,'Bleach bath',13,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(24,'Candles',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(25,'Wash Floors',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
INSERT INTO chores VALUES(26,'Pick up Aviv 1245',1,'2026-04-25T19:20:22Z','2026-04-25T19:20:22Z');
CREATE TABLE audit_log (
	id INTEGER NOT NULL, 
	table_name VARCHAR NOT NULL, 
	operation VARCHAR NOT NULL, 
	record_id INTEGER NOT NULL, 
	before_values TEXT, 
	after_values TEXT, 
	changed_at VARCHAR NOT NULL, 
	changed_by VARCHAR, 
	PRIMARY KEY (id)
);
INSERT INTO audit_log VALUES(1,'chores','INSERT',1,NULL,'{"id": 1, "name": "Kitchen handles", "frequency_in_weeks": 7, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(2,'chore_state','INSERT',1,NULL,'{"id": 1, "chore_id": 1, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(3,'chores','INSERT',2,NULL,'{"id": 2, "name": "Bathroom: Kids''", "frequency_in_weeks": 2, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(4,'chore_state','INSERT',2,NULL,'{"id": 2, "chore_id": 2, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(5,'chores','INSERT',3,NULL,'{"id": 3, "name": "Recycling", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(6,'chore_state','INSERT',3,NULL,'{"id": 3, "chore_id": 3, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(7,'chores','INSERT',4,NULL,'{"id": 4, "name": "Bins", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(8,'chore_state','INSERT',4,NULL,'{"id": 4, "chore_id": 4, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(9,'chores','INSERT',5,NULL,'{"id": 5, "name": "Kitchen cabinets", "frequency_in_weeks": 11, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(10,'chore_state','INSERT',5,NULL,'{"id": 5, "chore_id": 5, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(11,'chores','INSERT',6,NULL,'{"id": 6, "name": "Bathroom: loft", "frequency_in_weeks": 5, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(12,'chore_state','INSERT',6,NULL,'{"id": 6, "chore_id": 6, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(13,'chores','INSERT',7,NULL,'{"id": 7, "name": "Refill soap and shampoo dispensers: showers and sinks", "frequency_in_weeks": 13, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(14,'chore_state','INSERT',7,NULL,'{"id": 7, "chore_id": 7, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(15,'chores','INSERT',8,NULL,'{"id": 8, "name": "Playroom", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(16,'chore_state','INSERT',8,NULL,'{"id": 8, "chore_id": 8, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(17,'chores','INSERT',9,NULL,'{"id": 9, "name": "Sweep walkway", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(18,'chore_state','INSERT',9,NULL,'{"id": 9, "chore_id": 9, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(19,'chores','INSERT',10,NULL,'{"id": 10, "name": "Sweep Top Stairs", "frequency_in_weeks": 2, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(20,'chore_state','INSERT',10,NULL,'{"id": 10, "chore_id": 10, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(21,'chores','INSERT',11,NULL,'{"id": 11, "name": "Sweep Bottom Stairs", "frequency_in_weeks": 2, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(22,'chore_state','INSERT',11,NULL,'{"id": 11, "chore_id": 11, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(23,'chores','INSERT',12,NULL,'{"id": 12, "name": "Coffee & Mailbox", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(24,'chore_state','INSERT',12,NULL,'{"id": 12, "chore_id": 12, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(25,'chores','INSERT',13,NULL,'{"id": 13, "name": "Toilet Paper / Tissues", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(26,'chore_state','INSERT',13,NULL,'{"id": 13, "chore_id": 13, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(27,'chores','INSERT',14,NULL,'{"id": 14, "name": "Under couch", "frequency_in_weeks": 2, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(28,'chore_state','INSERT',14,NULL,'{"id": 14, "chore_id": 14, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(29,'chores','INSERT',15,NULL,'{"id": 15, "name": "Bathroom: Entrance", "frequency_in_weeks": 2, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(30,'chore_state','INSERT',15,NULL,'{"id": 15, "chore_id": 15, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(31,'chores','INSERT',16,NULL,'{"id": 16, "name": "Pump air in balls", "frequency_in_weeks": 4, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(32,'chore_state','INSERT',16,NULL,'{"id": 16, "chore_id": 16, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(33,'chores','INSERT',17,NULL,'{"id": 17, "name": "Stainless steel in kitchen", "frequency_in_weeks": 3, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(34,'chore_state','INSERT',17,NULL,'{"id": 17, "chore_id": 17, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(35,'chores','INSERT',18,NULL,'{"id": 18, "name": "Clean garbage cans", "frequency_in_weeks": 11, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(36,'chore_state','INSERT',18,NULL,'{"id": 18, "chore_id": 18, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(37,'chores','INSERT',19,NULL,'{"id": 19, "name": "Mow Lawn", "frequency_in_weeks": 2, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(38,'chore_state','INSERT',19,NULL,'{"id": 19, "chore_id": 19, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(39,'chores','INSERT',20,NULL,'{"id": 20, "name": "Clean Windows", "frequency_in_weeks": 15, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(40,'chore_state','INSERT',20,NULL,'{"id": 20, "chore_id": 20, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(41,'chores','INSERT',21,NULL,'{"id": 21, "name": "Bathroom: master: sink & toilet", "frequency_in_weeks": 3, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(42,'chore_state','INSERT',21,NULL,'{"id": 21, "chore_id": 21, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(43,'chores','INSERT',22,NULL,'{"id": 22, "name": "Bathroom: master: shower", "frequency_in_weeks": 7, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(44,'chore_state','INSERT',22,NULL,'{"id": 22, "chore_id": 22, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(45,'chores','INSERT',23,NULL,'{"id": 23, "name": "Bleach bath", "frequency_in_weeks": 13, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(46,'chore_state','INSERT',23,NULL,'{"id": 23, "chore_id": 23, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(47,'chores','INSERT',24,NULL,'{"id": 24, "name": "Candles", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(48,'chore_state','INSERT',24,NULL,'{"id": 24, "chore_id": 24, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(49,'chores','INSERT',25,NULL,'{"id": 25, "name": "Wash Floors", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(50,'chore_state','INSERT',25,NULL,'{"id": 25, "chore_id": 25, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(51,'chores','INSERT',26,NULL,'{"id": 26, "name": "Pick up Aviv 1245", "frequency_in_weeks": 1, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(52,'chore_state','INSERT',26,NULL,'{"id": 26, "chore_id": 26, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','2026-04-25T19:20:22Z','migration');
INSERT INTO audit_log VALUES(53,'people','INSERT',1,NULL,'{"id": 1, "name": "Ariel", "ordinal": 1, "avatar": "ariel.png", "created_at": "2026-04-25T19:38:50Z", "updated_at": "2026-04-25T19:38:50Z"}','2026-04-25T19:38:50Z','api');
INSERT INTO audit_log VALUES(54,'people','INSERT',2,NULL,'{"id": 2, "name": "Asaf", "ordinal": 2, "avatar": "asaf.png", "created_at": "2026-04-25T19:38:59Z", "updated_at": "2026-04-25T19:38:59Z"}','2026-04-25T19:38:59Z','api');
INSERT INTO audit_log VALUES(55,'people','INSERT',3,NULL,'{"id": 3, "name": "Amalya", "ordinal": 3, "avatar": "amalya.png", "created_at": "2026-04-25T19:39:10Z", "updated_at": "2026-04-25T19:39:10Z"}','2026-04-25T19:39:10Z','api');
INSERT INTO audit_log VALUES(56,'people','INSERT',4,NULL,'{"id": 4, "name": "Alon", "ordinal": 4, "avatar": "alon.png", "created_at": "2026-04-25T19:39:20Z", "updated_at": "2026-04-25T19:39:20Z"}','2026-04-25T19:39:20Z','api');
INSERT INTO audit_log VALUES(57,'people','INSERT',5,NULL,'{"id": 5, "name": "Aviv", "ordinal": 5, "avatar": "aviv.png", "created_at": "2026-04-25T19:39:31Z", "updated_at": "2026-04-25T19:39:31Z"}','2026-04-25T19:39:31Z','api');
INSERT INTO audit_log VALUES(58,'chore_state','UPDATE',15,'{"id": 15, "chore_id": 15, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 15, "chore_id": 15, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 1, "next_execution_date": "2026-05-08", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:41:17Z"}','2026-04-25T19:41:17Z','api');
INSERT INTO audit_log VALUES(59,'chore_state','UPDATE',2,'{"id": 2, "chore_id": 2, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 2, "chore_id": 2, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 2, "next_execution_date": "2026-05-08", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:42:03Z"}','2026-04-25T19:42:03Z','api');
INSERT INTO audit_log VALUES(60,'chore_state','UPDATE',6,'{"id": 6, "chore_id": 6, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 6, "chore_id": 6, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 2, "next_execution_date": "2026-05-08", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:42:19Z"}','2026-04-25T19:42:19Z','api');
INSERT INTO audit_log VALUES(61,'people','INSERT',6,NULL,'{"id": 6, "name": "Shalom", "ordinal": 100, "avatar": "other.png", "created_at": "2026-04-25T19:42:48Z", "updated_at": "2026-04-25T19:42:48Z"}','2026-04-25T19:42:48Z','api');
INSERT INTO audit_log VALUES(62,'chore_state','UPDATE',22,'{"id": 22, "chore_id": 22, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 22, "chore_id": 22, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-06-05", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:43:15Z"}','2026-04-25T19:43:15Z','api');
INSERT INTO audit_log VALUES(63,'chore_state','UPDATE',21,'{"id": 21, "chore_id": 21, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 21, "chore_id": 21, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-05-08", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:43:29Z"}','2026-04-25T19:43:29Z','api');
INSERT INTO audit_log VALUES(64,'chore_state','UPDATE',4,'{"id": 4, "chore_id": 4, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 4, "chore_id": 4, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 3, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:43:47Z"}','2026-04-25T19:43:47Z','api');
INSERT INTO audit_log VALUES(65,'chore_state','UPDATE',23,'{"id": 23, "chore_id": 23, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 23, "chore_id": 23, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-06-26", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:44:01Z"}','2026-04-25T19:44:01Z','api');
INSERT INTO audit_log VALUES(66,'chore_state','UPDATE',18,'{"id": 18, "chore_id": 18, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 18, "chore_id": 18, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 4, "next_execution_date": "2026-05-22", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:44:19Z"}','2026-04-25T19:44:19Z','api');
INSERT INTO audit_log VALUES(67,'chore_state','UPDATE',20,'{"id": 20, "chore_id": 20, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 20, "chore_id": 20, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-02-06", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:44:40Z"}','2026-04-25T19:44:40Z','api');
INSERT INTO audit_log VALUES(68,'chore_state','UPDATE',12,'{"id": 12, "chore_id": 12, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 12, "chore_id": 12, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 1, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:45:09Z"}','2026-04-25T19:45:09Z','api');
INSERT INTO audit_log VALUES(69,'chore_state','UPDATE',5,'{"id": 5, "chore_id": 5, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 5, "chore_id": 5, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 3, "next_execution_date": "2026-07-10", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:45:24Z"}','2026-04-25T19:45:24Z','api');
INSERT INTO audit_log VALUES(70,'chore_state','UPDATE',1,'{"id": 1, "chore_id": 1, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 1, "chore_id": 1, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 2, "next_execution_date": "2026-06-12", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:46:07Z"}','2026-04-25T19:46:07Z','api');
INSERT INTO audit_log VALUES(71,'chore_state','UPDATE',25,'{"id": 25, "chore_id": 25, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 25, "chore_id": 25, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:46:23Z"}','2026-04-25T19:46:23Z','api');
INSERT INTO audit_log VALUES(72,'chore_state','UPDATE',14,'{"id": 14, "chore_id": 14, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 14, "chore_id": 14, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 1, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:46:37Z"}','2026-04-25T19:46:37Z','api');
INSERT INTO audit_log VALUES(73,'chore_state','UPDATE',13,'{"id": 13, "chore_id": 13, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 13, "chore_id": 13, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 1, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:46:53Z"}','2026-04-25T19:46:53Z','api');
INSERT INTO audit_log VALUES(74,'chore_state','UPDATE',9,'{"id": 9, "chore_id": 9, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 9, "chore_id": 9, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 4, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:47:07Z"}','2026-04-25T19:47:07Z','api');
INSERT INTO audit_log VALUES(75,'chore_state','UPDATE',10,'{"id": 10, "chore_id": 10, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 10, "chore_id": 10, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 4, "next_execution_date": "2026-05-08", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:47:35Z"}','2026-04-25T19:47:35Z','api');
INSERT INTO audit_log VALUES(76,'chore_state','UPDATE',11,'{"id": 11, "chore_id": 11, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 11, "chore_id": 11, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 3, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:47:51Z"}','2026-04-25T19:47:51Z','api');
INSERT INTO audit_log VALUES(77,'chore_state','UPDATE',17,'{"id": 17, "chore_id": 17, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 17, "chore_id": 17, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 4, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:48:07Z"}','2026-04-25T19:48:07Z','api');
INSERT INTO audit_log VALUES(78,'chore_state','UPDATE',7,'{"id": 7, "chore_id": 7, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 7, "chore_id": 7, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 2, "next_execution_date": "2026-06-26", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:48:26Z"}','2026-04-25T19:48:26Z','api');
INSERT INTO audit_log VALUES(79,'chore_state','UPDATE',3,'{"id": 3, "chore_id": 3, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 3, "chore_id": 3, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 3, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:48:56Z"}','2026-04-25T19:48:56Z','api');
INSERT INTO audit_log VALUES(80,'chore_state','UPDATE',16,'{"id": 16, "chore_id": 16, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 16, "chore_id": 16, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 1, "next_execution_date": "2026-05-22", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:49:12Z"}','2026-04-25T19:49:12Z','api');
INSERT INTO audit_log VALUES(81,'chore_state','UPDATE',8,'{"id": 8, "chore_id": 8, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 8, "chore_id": 8, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 4, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:49:39Z"}','2026-04-25T19:49:39Z','api');
INSERT INTO audit_log VALUES(82,'chore_state','UPDATE',26,'{"id": 26, "chore_id": 26, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 26, "chore_id": 26, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:49:53Z"}','2026-04-25T19:49:53Z','api');
INSERT INTO audit_log VALUES(83,'chore_state','UPDATE',19,'{"id": 19, "chore_id": 19, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 19, "chore_id": 19, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-01-30", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:50:09Z"}','2026-04-25T19:50:09Z','api');
INSERT INTO audit_log VALUES(84,'chore_state','UPDATE',19,'{"id": 19, "chore_id": 19, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-01-30", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:50:09Z"}','{"id": 19, "chore_id": 19, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 6, "next_execution_date": "2026-01-30", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:50:12Z"}','2026-04-25T19:50:12Z','api');
INSERT INTO audit_log VALUES(85,'chore_state','UPDATE',24,'{"id": 24, "chore_id": 24, "last_executor_id": null, "last_execution_date": null, "next_executor_id": null, "next_execution_date": null, "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:20:22Z"}','{"id": 24, "chore_id": 24, "last_executor_id": null, "last_execution_date": null, "next_executor_id": 5, "next_execution_date": "2026-05-01", "created_at": "2026-04-25T19:20:22Z", "updated_at": "2026-04-25T19:50:38Z"}','2026-04-25T19:50:38Z','api');
CREATE TABLE chore_state (
	id INTEGER NOT NULL, 
	chore_id INTEGER NOT NULL, 
	last_executor_id INTEGER, 
	last_execution_date VARCHAR, 
	next_executor_id INTEGER, 
	next_execution_date VARCHAR, 
	created_at VARCHAR NOT NULL, 
	updated_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (chore_id), 
	FOREIGN KEY(chore_id) REFERENCES chores (id) ON DELETE CASCADE, 
	FOREIGN KEY(last_executor_id) REFERENCES people (id) ON DELETE SET NULL, 
	FOREIGN KEY(next_executor_id) REFERENCES people (id) ON DELETE SET NULL
);
INSERT INTO chore_state VALUES(1,1,NULL,NULL,2,'2026-06-12','2026-04-25T19:20:22Z','2026-04-25T19:46:07Z');
INSERT INTO chore_state VALUES(2,2,NULL,NULL,2,'2026-05-08','2026-04-25T19:20:22Z','2026-04-25T19:42:03Z');
INSERT INTO chore_state VALUES(3,3,NULL,NULL,3,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:48:56Z');
INSERT INTO chore_state VALUES(4,4,NULL,NULL,3,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:43:47Z');
INSERT INTO chore_state VALUES(5,5,NULL,NULL,3,'2026-07-10','2026-04-25T19:20:22Z','2026-04-25T19:45:24Z');
INSERT INTO chore_state VALUES(6,6,NULL,NULL,2,'2026-05-08','2026-04-25T19:20:22Z','2026-04-25T19:42:19Z');
INSERT INTO chore_state VALUES(7,7,NULL,NULL,2,'2026-06-26','2026-04-25T19:20:22Z','2026-04-25T19:48:26Z');
INSERT INTO chore_state VALUES(8,8,NULL,NULL,4,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:49:39Z');
INSERT INTO chore_state VALUES(9,9,NULL,NULL,4,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:47:07Z');
INSERT INTO chore_state VALUES(10,10,NULL,NULL,4,'2026-05-08','2026-04-25T19:20:22Z','2026-04-25T19:47:35Z');
INSERT INTO chore_state VALUES(11,11,NULL,NULL,3,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:47:51Z');
INSERT INTO chore_state VALUES(12,12,NULL,NULL,1,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:45:09Z');
INSERT INTO chore_state VALUES(13,13,NULL,NULL,1,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:46:53Z');
INSERT INTO chore_state VALUES(14,14,NULL,NULL,1,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:46:37Z');
INSERT INTO chore_state VALUES(15,15,NULL,NULL,1,'2026-05-08','2026-04-25T19:20:22Z','2026-04-25T19:41:17Z');
INSERT INTO chore_state VALUES(16,16,NULL,NULL,1,'2026-05-22','2026-04-25T19:20:22Z','2026-04-25T19:49:12Z');
INSERT INTO chore_state VALUES(17,17,NULL,NULL,4,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:48:07Z');
INSERT INTO chore_state VALUES(18,18,NULL,NULL,4,'2026-05-22','2026-04-25T19:20:22Z','2026-04-25T19:44:19Z');
INSERT INTO chore_state VALUES(19,19,NULL,NULL,6,'2026-01-30','2026-04-25T19:20:22Z','2026-04-25T19:50:12Z');
INSERT INTO chore_state VALUES(20,20,NULL,NULL,6,'2026-02-06','2026-04-25T19:20:22Z','2026-04-25T19:44:40Z');
INSERT INTO chore_state VALUES(21,21,NULL,NULL,6,'2026-05-08','2026-04-25T19:20:22Z','2026-04-25T19:43:29Z');
INSERT INTO chore_state VALUES(22,22,NULL,NULL,6,'2026-06-05','2026-04-25T19:20:22Z','2026-04-25T19:43:15Z');
INSERT INTO chore_state VALUES(23,23,NULL,NULL,6,'2026-06-26','2026-04-25T19:20:22Z','2026-04-25T19:44:01Z');
INSERT INTO chore_state VALUES(24,24,NULL,NULL,5,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:50:38Z');
INSERT INTO chore_state VALUES(25,25,NULL,NULL,6,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:46:23Z');
INSERT INTO chore_state VALUES(26,26,NULL,NULL,6,'2026-05-01','2026-04-25T19:20:22Z','2026-04-25T19:49:53Z');
CREATE TABLE executions (
	id INTEGER NOT NULL, 
	chore_id INTEGER NOT NULL, 
	executor_id INTEGER NOT NULL, 
	execution_date VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(chore_id) REFERENCES chores (id) ON DELETE CASCADE, 
	FOREIGN KEY(executor_id) REFERENCES people (id) ON DELETE CASCADE
);
CREATE TABLE rankings (
	id INTEGER NOT NULL, 
	person_id INTEGER NOT NULL, 
	chore_id INTEGER NOT NULL, 
	rating INTEGER NOT NULL, 
	created_at VARCHAR NOT NULL, 
	updated_at VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (person_id, chore_id), 
	CHECK (rating >= 1 AND rating <= 10), 
	FOREIGN KEY(person_id) REFERENCES people (id) ON DELETE CASCADE, 
	FOREIGN KEY(chore_id) REFERENCES chores (id) ON DELETE CASCADE
);
CREATE INDEX ix_audit_table_record ON audit_log (table_name, record_id);
CREATE INDEX ix_audit_changed_at ON audit_log (changed_at);
CREATE INDEX ix_executions_executor ON executions (executor_id);
CREATE INDEX ix_executions_chore_date ON executions (chore_id, execution_date);
CREATE INDEX ix_rankings_chore ON rankings (chore_id);
COMMIT;
