import datetime as dt
import sqlite3
import tempfile
import unittest
from pathlib import Path
import uuid

from memory import MemoryStore, ReminderStore
from reminder_scheduler import notify_due_reminders


class ReminderStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = ReminderStore(Path(self.temp.name) / "jarvis.sqlite3")

    def tearDown(self):
        self.temp.cleanup()

    def test_add_list_delete_and_due_once(self):
        future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat()
        item = self.store.add("Enviar relatório", future)
        self.assertEqual(self.store.list(), [item])
        overdue = {
            "id": str(uuid.uuid4()), "title": "Reunião",
            "due_at": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1))
            .isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        with sqlite3.connect(self.store.db_path) as db:
            db.execute("INSERT INTO reminders(id,title,due_at) VALUES(?,?,?)",
                       (overdue["id"], overdue["title"], overdue["due_at"]))
        self.assertEqual(self.store.take_due(), [overdue])
        self.assertEqual(self.store.take_due(), [])
        self.assertEqual(self.store.list(), [item])
        self.assertTrue(self.store.delete(item["id"]))
        self.assertFalse(self.store.delete(item["id"]))

    def test_rejects_blank_long_and_timezone_free_input(self):
        due = dt.datetime.now(dt.timezone.utc).isoformat()
        for title in (" ", "x" * 201):
            with self.assertRaises(ValueError):
                self.store.add(title, due)
        with self.assertRaises(ValueError):
            self.store.add("Lembrete", "2026-11-07T12:00")
        past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1)).isoformat()
        with self.assertRaises(ValueError):
            self.store.add("Lembrete", past)

    def test_operates_while_memory_store_uses_the_same_database(self):
        path = Path(self.temp.name) / "shared.sqlite3"
        memory = MemoryStore(path, ollama_url="http://127.0.0.1:9")
        try:
            reminders = ReminderStore(path)
            due = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=1)).isoformat()
            item = reminders.add("Revisar", due)
            self.assertEqual(reminders.list(), [item])
            self.assertTrue(reminders.delete(item["id"]))
        finally:
            memory.close()

    def test_scheduler_emits_due_reminder_and_refreshed_list(self):
        overdue = {
            "id": str(uuid.uuid4()), "title": "Reunião",
            "due_at": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=1))
            .isoformat(timespec="seconds").replace("+00:00", "Z"),
        }
        with sqlite3.connect(self.store.db_path) as db:
            db.execute("INSERT INTO reminders(id,title,due_at) VALUES(?,?,?)",
                       (overdue["id"], overdue["title"], overdue["due_at"]))

        class UI:
            def __init__(self):
                self.events = []

            def has_clients(self):
                return True

            def emit(self, kind, **values):
                self.events.append((kind, values))

        ui = UI()
        notify_due_reminders(self.store, ui)

        self.assertEqual(ui.events, [
            ("reminder_due", {"item": overdue}),
            ("reminders", {"items": []}),
        ])
        self.assertEqual(self.store.take_due(), [])


if __name__ == "__main__":
    unittest.main()
