"""Supabase (Postgres) repository.

The backend uses the SERVICE ROLE key (server-side only!). RLS is enabled on the table with no
policies, so the browser (anon key) can never read tickets directly. See supabase/schema.sql.
"""
from supabase import Client, create_client

TABLE = "tickets"


class SupabaseTicketRepository:
    def __init__(self, url: str, service_key: str) -> None:
        if not url or not service_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set (or use REPOSITORY=memory).")
        self.client: Client = create_client(url, service_key)

    def create(self, data: dict) -> dict:
        res = self.client.table(TABLE).insert(data).execute()
        return res.data[0]

    def get(self, ticket_id: int) -> dict | None:
        res = self.client.table(TABLE).select("*").eq("id", ticket_id).limit(1).execute()
        return res.data[0] if res.data else None

    def list(self, category, status, limit, offset) -> list[dict]:
        q = self.client.table(TABLE).select("*").order("created_at", desc=True).order("id", desc=True)
        if category:
            q = q.eq("category", category)
        if status:
            q = q.eq("status", status)
        return q.range(offset, offset + limit - 1).execute().data

    def update(self, ticket_id: int, fields: dict) -> dict | None:
        res = self.client.table(TABLE).update(fields).eq("id", ticket_id).execute()
        return res.data[0] if res.data else self.get(ticket_id)
