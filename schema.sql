drop table if exists entries;
create table entries (
  id integer primary key autoincrement,
  title string not null,
  text string not null,
  created date not null
);

create table tags (
  id integer primary key autoincrement,
  value string not null
);

create table entry_tags (
  id integer primary key autoincrement,
  entryid integer not null,
  tagid integer not null
);
