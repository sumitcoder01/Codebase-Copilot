from utils import add, subtract, multiply, divide

def main():
    print("Simple Calculator")
    a = float(input("Enter first number: "))
    b = float(input("Enter second number: "))
    op = input("Choose operation (+, -, *, /): ")

    if op == "+":
        print("Result:", add(a, b))
    elif op == "-":
        print("Result:", subtract(a, b))
    elif op == "*":
        print("Result:", multiply(a, b))
    elif op == "/":
        try:
            print("Result:", divide(a, b))
        except ZeroDivisionError as e:
            print("Error:", e)
    else:
        print("Invalid operation")

if __name__ == "__main__":
    main()
