function loadDashboard(userId) {
	console.log("Loading dashboard for user", userId);
	return fetch(`/api/dashboard/${userId}`).then(r => r.json());
}
