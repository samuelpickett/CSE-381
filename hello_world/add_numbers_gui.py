"""A simple graphical calculator that adds two numbers. Created using Codex"""

import tkinter as tk
from tkinter import messagebox


def calculate_sum():
    """Validate both input boxes, add the numbers, and display the result."""
    first_value = first_number_entry.get().strip()
    second_value = second_number_entry.get().strip()

    try:
        # float() allows the user to enter whole numbers or decimal numbers.
        first_number = float(first_value)
        second_number = float(second_value)
    except ValueError:
        # If either entry cannot be converted to a number, show an error message.
        messagebox.showerror(
            "Invalid input",
            "Please enter numbers in both input boxes.",
        )
        result_entry.delete(0, tk.END)
        return

    # Only update the output box after both values have passed validation.
    result = first_number + second_number
    result_entry.config(state="normal")
    result_entry.delete(0, tk.END)
    result_entry.insert(0, str(result))
    result_entry.config(state="readonly")


# Create the main application window.
window = tk.Tk()
window.title("Add Two Numbers")
window.geometry("320x250")

# Add a heading to explain what the program does.
title_label = tk.Label(window, text="Add Two Numbers", font=("Arial", 16, "bold"))
title_label.pack(pady=(15, 10))

# Create the first input label and input box.
first_number_label = tk.Label(window, text="First number:")
first_number_label.pack()
first_number_entry = tk.Entry(window, width=25)
first_number_entry.pack(pady=(0, 8))

# Create the second input label and input box.
second_number_label = tk.Label(window, text="Second number:")
second_number_label.pack()
second_number_entry = tk.Entry(window, width=25)
second_number_entry.pack(pady=(0, 10))

# This button runs calculate_sum() when the user clicks it.
calculate_button = tk.Button(window, text="Calculate", command=calculate_sum)
calculate_button.pack()

# The result box is read-only so users cannot accidentally edit the answer.
result_label = tk.Label(window, text="Result:")
result_label.pack(pady=(10, 0))
result_entry = tk.Entry(window, width=25, state="readonly")
result_entry.pack()

# Start Tkinter's event loop so the window responds to user actions.
window.mainloop()
