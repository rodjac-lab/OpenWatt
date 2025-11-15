-- Postgres DDL (insert-only + vues + triggers)
create table if not exists suppliers (
  id serial primary key,
  name text not null unique,
  website text
);

create table if not exists tariffs (
  id bigserial primary key,
  supplier_id int not null references suppliers(id),
  option text not null check (option in ('BASE','HPHC','TEMPO')),
  puissance_kva int not null check (puissance_kva in (3,6,9,12,15,18,24,30,36)),
  price_kwh_ttc numeric(8,6),
  price_kwh_hp_ttc numeric(8,6),
  price_kwh_hc_ttc numeric(8,6),
  abo_month_ttc numeric(8,4) not null,
  observed_at timestamptz not null,
  parser_version text not null,
  source_url text not null,
  source_checksum char(64) not null,
  notes text
);

create unique index if not exists uq_tariffs_obs
  on tariffs(supplier_id, option, puissance_kva, observed_at, parser_version, source_checksum);

create index if not exists idx_tariffs_latest
  on tariffs(supplier_id, option, puissance_kva, observed_at desc);

-- TRVE reference table
create table if not exists trve_reference (
  id bigserial primary key,
  option text not null check (option in ('BASE','HPHC','TEMPO')),
  puissance_kva int not null check (puissance_kva in (3,6,9,12,15,18,24,30,36)),
  price_kwh_ttc numeric(8,6),
  price_kwh_hp_ttc numeric(8,6),
  price_kwh_hc_ttc numeric(8,6),
  abo_month_ttc numeric(8,4) not null,
  valid_from date not null,
  valid_to date
);

create table if not exists admin_overrides (
  id bigserial primary key,
  supplier text not null,
  url text not null,
  observed_at timestamptz,
  created_at timestamptz not null default now()
);

-- latest view
create or replace view latest_tariffs as
select t.* from (
  select *,
         row_number() over (partition by supplier_id, option, puissance_kva order by observed_at desc) as rn
  from tariffs
) t where rn = 1;

-- latest vs TRVE view
create or replace view latest_vs_trve as
select lt.supplier_id, lt.option, lt.puissance_kva, lt.observed_at,
       lt.price_kwh_ttc, lt.price_kwh_hp_ttc, lt.price_kwh_hc_ttc, lt.abo_month_ttc,
       tr.price_kwh_ttc  as trve_price_base,
       tr.price_kwh_hp_ttc as trve_price_hp,
       tr.price_kwh_hc_ttc as trve_price_hc,
       tr.abo_month_ttc as trve_abo,
       case when lt.option = 'BASE' and tr.price_kwh_ttc is not null
            then (lt.price_kwh_ttc - tr.price_kwh_ttc) / tr.price_kwh_ttc
            else null end as diff_pct_kwh_base,
       (lt.abo_month_ttc - tr.abo_month_ttc) / tr.abo_month_ttc as diff_pct_abo
from latest_tariffs lt
join trve_reference tr
  on tr.option = lt.option
 and tr.puissance_kva = lt.puissance_kva
 and tr.valid_from <= lt.observed_at::date
 and (tr.valid_to is null or tr.valid_to >= lt.observed_at::date);

-- forbid UPDATE/DELETE on tariffs
create or replace function forbid_ud() returns trigger as $$
begin
  raise exception 'Updates/Deletes interdits: historique immuable';
end; $$ language plpgsql;

drop trigger if exists trg_forbid_update on tariffs;
drop trigger if exists trg_forbid_delete on tariffs;
create trigger trg_forbid_update before update on tariffs
for each row execute function forbid_ud();
create trigger trg_forbid_delete before delete on tariffs
for each row execute function forbid_ud();
