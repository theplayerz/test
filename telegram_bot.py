from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters,
)

import subprocess
import re
import time
import os

# =========================
# 설정
# =========================
TOKEN = "8973869827:AAH-54-NSwvKO3o_e59wpR0CKaFaCd82AkY"
ALLOWED_CHAT_ID = 8376884340
WORK_DIR = r"C:\dev"
GIT_EXE = r"C:\Program Files\Git\bin\git.exe"

# =========================
# 유틸
# =========================

def clean_output(text):
    if not text:
        return ""

    text = re.sub(
        r"\x1B\[[0-?]*[ -/]*[@-~]",
        "",
        text
    )

    return text.strip()


def send_safe(text, limit=4000):
    if not text:
        return "(출력 없음)"

    if len(text) > limit:
        return text[:limit] + "\n\n...(생략)"

    return text


def is_git_repo():
    return os.path.exists(
        os.path.join(WORK_DIR, ".git")
    )


# =========================
# OpenCode 실행
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    command = update.message.text.strip()

    if not command:
        return

    await update.message.reply_text(
        f"명령 실행 중...\n\n{command}"
    )

    try:

        start_time = time.time()

        result = subprocess.run(
            ["cmd", "/c", "opencode", "run", command],
            cwd=WORK_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=300
        )

        elapsed = round(
            time.time() - start_time,
            2
        )

        output = clean_output(result.stdout)
        error = clean_output(result.stderr)

        print("\n========================================")
        print(f"작업폴더 : {WORK_DIR}")
        print(f"실행시간 : {elapsed}초")
        print(f"명령어   : {command}")
        print("----------------------------------------")
        print(output)

        if error:
            print("----------------------------------------")
            print("STDERR:")
            print(error)

        print("========================================\n")

        message = output

        if error:
            message += "\n\n[ERROR]\n"
            message += error

        await update.message.reply_text(
            send_safe(message)
        )

    except subprocess.TimeoutExpired:

        await update.message.reply_text(
            "실행 시간이 300초를 초과했습니다."
        )

    except Exception as e:

        print(e)

        await update.message.reply_text(
            f"오류 발생:\n{type(e).__name__}\n{str(e)}"
        )


# =========================
# Git 상태 확인
# =========================

async def gitstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    try:

        result = subprocess.run(
            [GIT_EXE, "status"],
            cwd=WORK_DIR,
            capture_output=True,
            text=True
        )

        message = (
            result.stdout +
            "\n" +
            result.stderr
        )

        await update.message.reply_text(
            send_safe(message)
        )

    except Exception as e:

        await update.message.reply_text(
            str(e)
        )


# =========================
# GitHub Push
# =========================

async def push(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != ALLOWED_CHAT_ID:
        return

    await update.message.reply_text(
        "GitHub 업로드 시작..."
    )

    try:

        if not os.path.exists(GIT_EXE):

            await update.message.reply_text(
                f"Git 실행파일을 찾을 수 없습니다.\n\n{GIT_EXE}"
            )
            return

        if not is_git_repo():

            await update.message.reply_text(
                f".git 폴더를 찾을 수 없습니다.\n\n{WORK_DIR}"
            )
            return

        version = subprocess.run(
            [GIT_EXE, "--version"],
            capture_output=True,
            text=True
        )

        add_result = subprocess.run(
            [GIT_EXE, "add", "."],
            cwd=WORK_DIR,
            capture_output=True,
            text=True
        )

        commit_result = subprocess.run(
            [
                GIT_EXE,
                "commit",
                "-m",
                "telegram auto push"
            ],
            cwd=WORK_DIR,
            capture_output=True,
            text=True
        )

        push_result = subprocess.run(
            [
                GIT_EXE,
                "push",
                "origin",
                "main"
            ],
            cwd=WORK_DIR,
            capture_output=True,
            text=True
        )

        message = ""

        message += "[Git Version]\n"
        message += version.stdout

        if add_result.stderr:
            message += "\n\n[Add Error]\n"
            message += add_result.stderr

        if commit_result.stdout:
            message += "\n\n[Commit]\n"
            message += commit_result.stdout

        if commit_result.stderr:
            message += "\n\n[Commit Error]\n"
            message += commit_result.stderr

        if push_result.stdout:
            message += "\n\n[Push]\n"
            message += push_result.stdout

        if push_result.stderr:
            message += "\n\n[Push Error]\n"
            message += push_result.stderr

        await update.message.reply_text(
            send_safe(message)
        )

    except Exception as e:

        print(e)

        await update.message.reply_text(
            f"업로드 실패\n\n{type(e).__name__}\n{str(e)}"
        )


# =========================
# 메인
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("push", push)
    )

    app.add_handler(
        CommandHandler("gitstatus", gitstatus)
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )
    )

    print("===================================")
    print(" Telegram OpenCode Bot 시작")
    print(" Chat ID :", ALLOWED_CHAT_ID)
    print(" Work Dir:", WORK_DIR)
    print("===================================")

    app.run_polling()


if __name__ == "__main__":
    main()