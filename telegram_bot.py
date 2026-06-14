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
import shutil
import os
from dotenv import load_dotenv

# =========================
# ENV 로드
# =========================

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN 환경변수가 설정되지 않았습니다.")

# =========================
# 설정
# =========================
ALLOWED_CHAT_ID = 8376884340
WORK_DIR = r"C:\dev"
GIT_EXE = shutil.which("git")

if not GIT_EXE:
    GIT_EXE = r"C:\Program Files\Git\bin\git.exe"

# =========================
# 유틸
# =========================

def clean_output(text):
    if not text:
        return ""

    text = re.sub(
        r'\x1B\[[0-?]*[ -/]*[@-~]',
        '',
        text
    )
    
    return text.strip()


def is_git_repo():
    return os.path.isdir(
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

        elapsed = round(time.time() - start_time, 2)

        output = clean_output(result.stdout)
        error = clean_output(result.stderr)

        if not output:
            output = "(출력 없음)"

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

        telegram_output = output

        if error:
            telegram_output += "\n\n[ERROR]\n" + error

        if len(telegram_output) > 3500:
            telegram_output = (
                telegram_output[:3500]
                + "\n\n...(생략)"
            )

        await update.message.reply_text(
            telegram_output
        )

    except subprocess.TimeoutExpired:

        await update.message.reply_text(
            "실행 시간이 300초를 초과했습니다."
        )

    except Exception as e:

        print(f"오류 발생: {e}")

        await update.message.reply_text(
            f"오류 발생:\n{type(e).__name__}\n{str(e)}"
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
                f"Git 실행 파일을 찾을 수 없습니다.\n\n{GIT_EXE}"
            )
            return

        if not is_git_repo():

            await update.message.reply_text(
                f"Git 저장소가 아닙니다.\n\n{WORK_DIR}"
            )
            return

        # 변경사항 확인
        status_result = subprocess.run(
            [GIT_EXE, "status", "--porcelain"],
            cwd=WORK_DIR,
            capture_output=True,
            text=True
        )

        if not status_result.stdout.strip():

            await update.message.reply_text(
                "변경사항이 없습니다."
            )
            return

        # add
        subprocess.run(
            [GIT_EXE, "add", "."],
            cwd=WORK_DIR,
            check=True
        )

        # commit
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

        # push
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

        if push_result.returncode == 0:

            message = "✅ GitHub 업로드 성공"

            if commit_result.stdout:
                message += (
                    "\n\n[Commit]\n"
                    + commit_result.stdout[:1500]
                )

            if push_result.stdout:
                message += (
                    "\n\n[Push]\n"
                    + push_result.stdout[:1500]
                )

            # Git은 성공 메시지를 stderr에 출력하는 경우가 있음
            if push_result.stderr:
                message += (
                    "\n\n[Push]\n"
                    + push_result.stderr[:1500]
                )

        else:

            message = "❌ GitHub 업로드 실패"

            if push_result.stdout:
                message += (
                    "\n\n[STDOUT]\n"
                    + push_result.stdout[:1500]
                )

            if push_result.stderr:
                message += (
                    "\n\n[STDERR]\n"
                    + push_result.stderr[:1500]
                )

        print("\n========================================")
        print("GitHub Push")
        print("----------------------------------------")
        print(message)
        print("========================================\n")

        await update.message.reply_text(
            message[:4000]
        )

    except Exception as e:

        print(f"GitHub 업로드 실패: {e}")

        await update.message.reply_text(
            f"업로드 실패:\n{type(e).__name__}\n{str(e)}"
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
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )
    )

    print("===================================")
    print(" Telegram OpenCode Bot 시작")
    print(" Chat ID :", ALLOWED_CHAT_ID)
    print(" Work Dir:", WORK_DIR)
    print(" Git Path:", GIT_EXE)
    print("===================================")

    app.run_polling()

if __name__ == "__main__":
    main()