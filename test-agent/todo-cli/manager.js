const { loadTodos, saveTodos } = require("./storage");

function addTodo(title) {
  const todos = loadTodos();
  const todo = {
    id: todos.length + 1,
    title,
    done: false,
  };
  todos.push(todo);
  saveTodos(todos);
  return todo;
}

function getTodos() {
  return loadTodos();
}

function toggleDone(id) {
  const todos = loadTodos();
  const todo = todos.find((t) => t.id === id);
  if (!todo) return null;
  todo.done = !todo.done;
  saveTodos(todos);
  return todo;
}

module.exports = { addTodo, getTodos, toggleDone };
