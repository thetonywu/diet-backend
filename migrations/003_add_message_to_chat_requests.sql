alter table public.chat_requests add column message text not null default '';
alter table public.chat_requests alter column message drop default;
