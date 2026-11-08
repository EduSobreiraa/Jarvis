def notify_due_reminders(reminders, ui):
    if not ui.has_clients():
        return
    due = reminders.take_due()
    for item in due:
        ui.emit("reminder_due", item=item)
    if due:
        ui.emit("reminders", items=reminders.list())
