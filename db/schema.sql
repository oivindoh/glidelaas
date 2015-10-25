drop table healthstatus;
create table if not exists healthstatus("when" datetime not null, "system" text not null, "status" integer not null, "who" text, "meta" text);
create unique index if not exists uniqueHealthStatus on healthstatus ("when","system");
insert into healthstatus values("2015-10-24 20:30:12.123", "EN", 10, "abat","");
insert into healthstatus values("2015-10-24 20:40:15.321", "EN", 20, "abat","");
insert into healthstatus values("2015-10-24 20:50:13.123", "EN", 20, "abat","");
insert into healthstatus values("2015-10-24 21:00:18.321", "EN", 30, "abat","");
insert into healthstatus values("2015-10-24 21:10:17.123", "EN", 50, "abat","");
insert into healthstatus values("2015-10-24 20:31:12.123", "ES", 50, "abat","");
insert into healthstatus values("2015-10-24 20:41:15.321", "ES", 50, "abat","");
insert into healthstatus values("2015-10-24 20:51:13.123", "ES", 30, "abat","");
insert into healthstatus values("2015-10-24 21:01:18.321", "ES", 20, "abat","");
insert into healthstatus values("2015-10-24 21:11:17.123", "ES", 10, "abat","");
-- just to test unique constraint works...
--insert into healthstatus values("2015-10-24 21:10:17.123", "EN", 50, "abat");
