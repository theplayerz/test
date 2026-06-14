from manager import add_todo


def main():
    print("=== TODO CLI ===")
    while True:
        print("\n1. 할 일 추가")
        print("2. 종료")
        choice = input("선택: ").strip()

        if choice == "1":
            title = input("할 일: ").strip()
            if title:
                todo = add_todo(title)
                print(f"[추가됨] {todo['title']} (id: {todo['id']})")
            else:
                print("내용을 입력하세요.")
        elif choice == "2":
            print("종료합니다.")
            break
        else:
            print("올바른 번호를 입력하세요.")


if __name__ == "__main__":
    main()
