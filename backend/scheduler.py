from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import datetime
import memory as mem

scheduler = AsyncIOScheduler()

def start():
    if not scheduler.running:
        scheduler.start()

def schedule_reminder(message: str, minutes: float):
    trigger_at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    mem.add_reminder(message, trigger_at.isoformat())
    scheduler.add_job(
        lambda: None,
        trigger=DateTrigger(run_date=trigger_at),
        id=f"reminder_{trigger_at.timestamp()}",
        name=message,
    )
    return trigger_at.isoformat()

async def check_reminders():
    pending = mem.get_pending_reminders()
    for r in pending:
        mem.mark_reminder_fired(r["id"])
    return pending
