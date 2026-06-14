def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        return "0으로 나눌 수 없습니다"
    return a / b

def main():
    print("=== 계산기 ===")
    print("1. 더하기")
    print("2. 빼기")
    print("3. 곱하기")
    print("4. 나누기")
    print("5. 종료")

    while True:
        try:
            choice = input("\n선택 (1-5): ")
            if choice == "5":
                print("종료합니다.")
                break

            if choice not in ("1", "2", "3", "4"):
                print("1-5 사이의 숫자를 입력하세요.")
                continue

            a = float(input("첫 번째 숫자: "))
            b = float(input("두 번째 숫자: "))

            if choice == "1":
                print(f"{a} + {b} = {add(a, b)}")
            elif choice == "2":
                print(f"{a} - {b} = {subtract(a, b)}")
            elif choice == "3":
                print(f"{a} * {b} = {multiply(a, b)}")
            elif choice == "4":
                print(f"{a} / {b} = {divide(a, b)}")

        except ValueError:
            print("올바른 숫자를 입력하세요.")

if __name__ == "__main__":
    main()
