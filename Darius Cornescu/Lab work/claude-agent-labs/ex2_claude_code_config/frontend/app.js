// Small frontend module. Deliberately contains a console.log so the
// frontend/** rule (.claude/rules/frontend.md) fires when Claude reviews it.

const greeting = "hello";

function renderGreeting(target) {
	const el = document.querySelector(target);
	// VIOLATION (frontend rule): no console.* in committed code.
	console.log("rendering greeting:", greeting);
	el.textContent = greeting;
}

export { renderGreeting };
