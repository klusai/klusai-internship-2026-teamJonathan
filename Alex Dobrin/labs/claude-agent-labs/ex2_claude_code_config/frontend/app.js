// Frontend entry point — used to test the frontend/** rule (no console.log).

function greet(name) {
	const message = `Hello, ${name}!`;
	console.log(message); // <- should be flagged by .claude/rules/frontend.md
	return message;
}

greet("world");
