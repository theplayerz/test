#!/usr/bin/env python3
"""Todo CLI App - A simple todo list manager."""

import json
import os
import sys
from typing import NoReturn


TODO_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todos.json")


def load_todos() -> list[dict[str, str | bool]]:
    """Load todos from JSON file. Returns empty list if file doesn't exist."""
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_todos(todos: list[dict[str, str | bool]]) -> None:
    """Save todos to JSON file."""
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add_todo(content: str) -> None:
    """Add a new todo item."""
    todos = load_todos()
    new_id = max((t.get("id", 0) for t in todos), default=0) + 1
    todos.append({"id": new_id, "content": content, "done": False})
    save_todos(todos)
    print(f"Added todo #{new_id}: {content}")


def list_todos() -> None:
    """List all todos with their completion status."""
    todos = load_todos()
    if not todos:
        print("No todos.")
        return
    for t in todos:
        status = "[x]" if t.get("done") else "[ ]"
        print(f"{t['id']:>3}. {status} {t['content']}")


def done_todo(todo_id: int) -> None:
    """Mark a specific todo as completed."""
    todos = load_todos()
    for t in todos:
        if t.get("id") == todo_id:
            t["done"] = True
            save_todos(todos)
            print(f"Todo #{todo_id} marked as done.")
            return
    print(f"Error: Todo #{todo_id} not found.", file=sys.stderr)
    sys.exit(1)


def delete_todo(todo_id: int) -> None:
    """Delete a specific todo."""
    todos = load_todos()
    for i, t in enumerate(todos):
        if t.get("id") == todo_id:
            del todos[i]
            save_todos(todos)
            print(f"Todo #{todo_id} deleted.")
            return
    print(f"Error: Todo #{todo_id} not found.", file=sys.stderr)
    sys.exit(1)


def reset_todos() -> None:
    """Delete all todos."""
    save_todos([])
    print("All todos have been deleted.")


def print_usage() -> NoReturn:
    """Print usage information and exit."""
    print("Usage:")
    print("  todo add \"할 일 내용\"")
    print("  todo list")
    print("  todo done <id>")
    print("  todo delete <id>")
    print("  todo reset")
    sys.exit(1)


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print_usage()

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 3:
            print("Error: Please provide todo content.", file=sys.stderr)
            sys.exit(1)
        add_todo(sys.argv[2])
    elif command == "list":
        list_todos()
    elif command == "done":
        if len(sys.argv) < 3:
            print("Error: Please provide todo ID.", file=sys.stderr)
            sys.exit(1)
        try:
            done_todo(int(sys.argv[2]))
        except ValueError:
            print("Error: Invalid ID. Must be a number.", file=sys.stderr)
            sys.exit(1)
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Error: Please provide todo ID.", file=sys.stderr)
            sys.exit(1)
        try:
            delete_todo(int(sys.argv[2]))
        except ValueError:
            print("Error: Invalid ID. Must be a number.", file=sys.stderr)
            sys.exit(1)
    elif command == "reset":
        reset_todos()
    else:
        print(f"Error: Unknown command '{command}'.", file=sys.stderr)
        print_usage()


if __name__ == "__main__":
    main()
