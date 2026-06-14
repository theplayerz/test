from storage import load_todos, save_todos


def add_todo(title):
    todos = load_todos()
    todo = {
        "id": len(todos) + 1,
        "title": title,
        "done": False,
    }
    todos.append(todo)
    save_todos(todos)
    return todo
