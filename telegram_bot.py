from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    ContextTypes,
    filters,
)

import subprocess
import re
import time

# =========================
# 설정
# =========================
TOKEN = "8973869827:AAH-54-NSwvKO3o_e59wpR0CKaFaCd82AkY"
ALLOWED_CHAT_ID = 8376884340

# =========================
# 유틸
# =========================

def clean_output(text):
    if not text:
        return ""

    # ANSI 컬러 코드 제거
    text = re.sub(
        r'\x1B\[[0-?]*[ -/]*[@-~]',
        '',
        text
    )

    return text.strip()

# =========================
# 메시지 처리
# =========================

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 허용된 사용자만 사용
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

        # =========================
        # PC 콘솔 로그
        # =========================

        print("\n========================================")
        print(f"실행 시간: {elapsed}초")
        print(f"명령: {command}")
        print("----------------------------------------")
        print(output)

        if error:
            print("----------------------------------------")
            print("STDERR:")
            print(error)

        print("========================================\n")

        # Telegram 메시지 길이 제한 대응
        telegram_output = output

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
            f"오류 발생:\n{str(e)}"
        )

# =========================
# 메인
# =========================

def main():

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle
        )
    )

    print("===================================")
    print(" Telegram OpenCode Bot 시작")
    print(" Chat ID:", ALLOWED_CHAT_ID)
    print("===================================")

    app.run_polling()

if __name__ == "__main__":
    main()