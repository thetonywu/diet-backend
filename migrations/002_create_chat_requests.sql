-- Track raw LLM requests and responses
create table public.chat_requests (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users(id) on delete set null,
  input jsonb not null,
  response text not null,
  created_at timestamptz default now()
);

create index idx_chat_requests_user_id on public.chat_requests(user_id);
create index idx_chat_requests_created_at on public.chat_requests(created_at);

alter table public.chat_requests enable row level security;

create policy "Users can read own chat requests"
  on public.chat_requests for select
  using (auth.uid() = user_id);
