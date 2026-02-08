import uuid

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from ..db import SessionLocal
from ..models import Draft, DraftStatus
from ..services.workflow import approve_draft_and_schedule

from ..config import settings


def _is_authorized(update: Update) -> bool:
    if not settings.telegram_chat_id:
        return True
    chat_id = str(update.effective_chat.id) if update.effective_chat else ""
    return chat_id == str(settings.telegram_chat_id)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    await update.message.reply_text("LinkedIn autoposter bot is running.")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    db = SessionLocal()
    try:
        drafts = (
            db.query(Draft)
            .filter(Draft.status == DraftStatus.pending)
            .order_by(Draft.created_at.desc())
            .limit(5)
            .all()
        )
        if not drafts:
            await update.message.reply_text("No pending drafts.")
            return

        lines = [
            f"{draft.id} | {draft.pillar_theme} > {draft.sub_theme} | {draft.format.value} | {draft.tone.value}"
            for draft in drafts
        ]
        await update.message.reply_text("Pending drafts:\n" + "\n".join(lines))
    finally:
        db.close()


async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /approve <draft_id>")
        return

    draft_id = context.args[0]
    try:
        parsed_id = uuid.UUID(draft_id)
    except ValueError:
        await update.message.reply_text("Invalid draft ID.")
        return

    db = SessionLocal()
    try:
        draft = db.query(Draft).filter(Draft.id == parsed_id).first()
        if not draft:
            await update.message.reply_text("Draft not found.")
            return
        if draft.status != DraftStatus.pending:
            await update.message.reply_text("Draft is not pending.")
            return

        post = approve_draft_and_schedule(db=db, draft=draft, scheduled_time=None)
        await update.message.reply_text(
            f"Approved draft {draft.id}. Scheduled for {post.scheduled_time.isoformat()} UTC."
        )
    finally:
        db.close()


async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_authorized(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /reject <draft_id> <reason>")
        return

    draft_id = context.args[0]
    reason = " ".join(context.args[1:])
    try:
        parsed_id = uuid.UUID(draft_id)
    except ValueError:
        await update.message.reply_text("Invalid draft ID.")
        return

    db = SessionLocal()
    try:
        draft = db.query(Draft).filter(Draft.id == parsed_id).first()
        if not draft:
            await update.message.reply_text("Draft not found.")
            return
        if draft.status != DraftStatus.pending:
            await update.message.reply_text("Draft is not pending.")
            return

        draft.status = DraftStatus.rejected
        draft.rejection_reason = reason
        db.commit()
        await update.message.reply_text(f"Rejected draft {draft.id}.")
    finally:
        db.close()


def build_bot():
    if not settings.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")

    app = ApplicationBuilder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("approve", approve))
    app.add_handler(CommandHandler("reject", reject))
    return app


if __name__ == "__main__":
    bot = build_bot()
    bot.run_polling()
