import sys
from PyQt6.QtWidgets import QApplication


def main() -> None:
    app = QApplication(sys.argv)
    print("Pomodoro timer — scaffold OK")
    sys.exit(0)


if __name__ == "__main__":
    main()
