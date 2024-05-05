-- Note: Here's how to get the current ISO-8601 datetime
-- with sub-second precision:
--
--     strftime('%Y-%m-%dT%H:%M:%fZ')

create table calibration(
  when_iso text not null,
  temperature_correction_celsius real not null);

insert into calibration(when_iso, temperature_correction_celsius) values('2024-04-20T12:00:00.000Z', -3.47);

create table reading_raw(
  id integer primary key not null,
  when_iso text not null,
  temperature_celsius real not null,
  humidity_percent real not null,
  dupe_count integer not null default 0,
  last_iso text null);

create index reading_raw_by_when_iso on reading_raw(when_iso);

create view reading(
  when_iso,
  temperature_celsius,
  humidity_percent,
  last_iso
) as
  select raw.when_iso as when_iso,
    round(raw.temperature_celsius + calib.temperature_correction_celsius, 2) as temperature_celsius,
    -- Let there be math!
    -- This formula is based on the source of
    -- <https://www.markusweimar.de/en/humidity-calculator/>.
    round((raw.humidity_percent / 100.0 * 
       (6.112 * exp(17.62 * raw.temperature_celsius / (243.12 + raw.temperature_celsius)))) /
     (6.112 * exp(17.62 * (raw.temperature_celsius + calib.temperature_correction_celsius) / (243.12 + raw.temperature_celsius + calib.temperature_correction_celsius))) *
     100.0, 2) as humidity_percent,
    raw.last_iso as last_iso
  from reading_raw raw inner join calibration calib
    on calib.when_iso = (
      select when_iso
      from calibration
      where when_iso <= raw.when_iso
      order by when_iso desc
      limit 1);

-- TODO: dummy values
-- insert into reading_raw values('2020-01-01T10:10:10.000Z', 20, 50, 0, 0);
-- insert into reading_raw values(strftime('%Y-%m-%dT%H:%M:%fZ'), 30, 50, 0, 0);
-- insert into reading_raw values(strftime('%Y-%m-%dT%H:%M:%fZ'), 30, 50, 0, 0);

create table error(
  when_iso text not null,
  status integer not null,
  stdout text not null,
  stderr text not null);
