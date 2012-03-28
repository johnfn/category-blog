drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title string not null,
  text string not null,
  created date not null
);

drop table if exists tags;
create table tags (
  id integer primary key autoincrement,
  value string not null,
  desc string not null,
  longdesc string not null
);

drop table if exists entry_tags;
create table entry_tags (
  id integer primary key autoincrement,
  entryid integer not null,
  tagid integer not null
);

