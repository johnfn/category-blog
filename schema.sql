drop table if exists entries;
create table entries (
  id serial primary key,
  title text not null,
  text text not null,
  created date not null
);

drop table if exists tags;
create table tags (
  id serial primary key,
  value text not null,
  description text not null,
  longdesc text not null
);

drop table if exists entry_tags;
create table entry_tags (
  id serial primary key,
  entryid integer not null,
  tagid integer not null
);

