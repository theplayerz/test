const fs = require("fs");
const path = require("path");

const DATA_FILE = path.join(__dirname, "todos.json");

function loadTodos() {
  if (!fs.existsSync(DATA_FILE)) return [];
  const raw = fs.readFileSync(DATA_FILE, "utf-8");
  return JSON.parse(raw);
}

function saveTodos(todos) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(todos, null, 2), "utf-8");
}

module.exports = { loadTodos, saveTodos };
