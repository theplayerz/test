const { addTodo, getTodos, toggleDone } = require("./manager");
const readline = require("readline");

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

const inputBuffer = [];
let bufferReady = null;

rl.on("line", (line) => {
  inputBuffer.push(line.trim());
  if (bufferReady) {
    bufferReady();
    bufferReady = null;
  }
});

async function nextLine() {
  if (inputBuffer.length > 0) {
    return inputBuffer.shift();
  }
  return new Promise((resolve) => {
    bufferReady = () => resolve(inputBuffer.shift());
  });
}

function printTodos(todos) {
  if (todos.length === 0) {
    console.log("할 일이 없습니다.");
    return;
  }
  for (const t of todos) {
    const status = t.done ? "[✓]" : "[ ]";
    console.log(`  ${status} ${t.id}. ${t.title}`);
  }
}

async function main() {
  console.log("=== TODO CLI ===");
  while (true) {
    console.log("\n1. 할 일 추가");
    console.log("2. 목록 보기");
    console.log("3. 완료 처리");
    console.log("4. 종료");
    process.stdout.write("선택: ");
    const choice = await nextLine();
    if (!choice) break;

    if (choice === "1") {
      process.stdout.write("할 일: ");
      const title = await nextLine();
      if (!title) break;
      if (title) {
        const todo = addTodo(title);
        console.log(`[추가됨] ${todo.title} (id: ${todo.id})`);
      } else {
        console.log("내용을 입력하세요.");
      }
    } else if (choice === "2") {
      const todos = getTodos();
      printTodos(todos);
    } else if (choice === "3") {
      process.stdout.write("완료할 할 일 ID: ");
      const id = parseInt(await nextLine(), 10);
      if (isNaN(id)) {
        console.log("올바른 ID를 입력하세요.");
        continue;
      }
      const todo = toggleDone(id);
      if (!todo) {
        console.log("해당 ID의 할 일이 없습니다.");
        continue;
      }
      const status = todo.done ? "완료" : "취소";
      console.log(`[${status}] ${todo.title} (id: ${todo.id})`);
    } else if (choice === "4") {
      console.log("종료합니다.");
      break;
    } else {
      console.log("올바른 번호를 입력하세요.");
    }
  }
  rl.close();
}

main();
