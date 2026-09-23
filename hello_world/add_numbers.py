"""Ask for two numbers, add them, and repeat until the user quits. Generated using Codex"""


def get_number(prompt):
    """Read one number from the user, or return None when they choose to quit."""
    while True:
        # input() pauses the program and returns whatever the user typed as text.
        value = input(prompt).strip()

        # Checking for quit here lets the user leave at either number prompt.
        if value.lower() == "quit":
            return None

        try:
            # float() accepts both whole numbers and decimal numbers.
            return float(value)
        except ValueError:
            # A ValueError means the text could not be converted into a number.
            print("That is not a number. Please enter a number or type 'quit'.")


# Keep asking for pairs of numbers until the user types "quit".
while True:
    first_number = get_number("Enter the first number (or type 'quit'): ")
    if first_number is None:
        break

    second_number = get_number("Enter the second number (or type 'quit'): ")
    if second_number is None:
        break

    # Add the two valid numbers and display the result in the console.
    print(f"The sum is: {first_number + second_number}")

print("Goodbye!")
