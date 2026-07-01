def get_user(user_id):
	return {"id": user_id, "name": "Alice"}


def create_order(user_id, items, total):
	return {"user_id": user_id, "items": items, "total": total, "status": "pending"}
