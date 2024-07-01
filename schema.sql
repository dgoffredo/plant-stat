-- Note: Here's how to get the current ISO-8601 datetime
-- with sub-second precision:
--
--     strftime('%Y-%m-%dT%H:%M:%fZ')

drop table if exists calibration;
create table calibration(
  when_iso text not null primary key,
  temperature_correction_celsius real not null);

insert into calibration(
  when_iso, temperature_correction_celsius)
values
  ('2024-04-20T12:00:00.000Z', -3.47);

create table if not exists reading_raw(
  id integer primary key not null,
  when_iso text not null,
  temperature_celsius real not null,
  humidity_percent real not null,
  dupe_count integer not null default 0,
  last_iso text null);

create index if not exists reading_raw_by_when_iso on reading_raw(when_iso);

drop view if exists reading;
create view reading(
  id,
  when_iso,
  temperature_celsius,
  humidity_percent,
  dupe_count,
  last_iso
) as
  select raw.id as id,
    raw.when_iso as when_iso,
    round(raw.temperature_celsius + calib.temperature_correction_celsius, 2) as temperature_celsius,
    -- Let there be math!
    -- This formula is based on the source of
    -- <https://www.markusweimar.de/en/humidity-calculator/>.
    round((raw.humidity_percent / 100.0 * 
       (6.112 * exp(17.62 * raw.temperature_celsius / (243.12 + raw.temperature_celsius)))) /
     (6.112 * exp(17.62 * (raw.temperature_celsius + calib.temperature_correction_celsius) / (243.12 + raw.temperature_celsius + calib.temperature_correction_celsius))) *
     100.0, 2) as humidity_percent,
    raw.dupe_count as dupe_count,
    raw.last_iso as last_iso
  from reading_raw raw inner join calibration calib
    on calib.when_iso = (
      select when_iso
      from calibration
      where when_iso <= raw.when_iso
      order by when_iso desc
      limit 1);

create table if not exists error(
  when_iso text not null,
  status integer not null,
  stdout text not null,
  stderr text not null);

create table if not exists relay_state(
  when_iso text not null,
  host text not null,
  alias text not null,
  state integer not null, -- 0=off, 1=on
  reading_id integer not null,

  foreign key (reading_id) references reading_raw(id));

create table if not exists co2_raw(
  id integer primary key not null,
  when_iso text not null,
  sequence_number integer not null,
  co2_ppm integer not null,
  temperature_celsius real not null,
  humidity_percent real not null,
  dupe_count integer not null default 0,
  last_iso text null);

create table if not exists co2_request_duration(
  co2_raw_id integer not null,
  duration_nanoseconds integer not null,

  foreign key (co2_raw_id) references co2_raw(id));

