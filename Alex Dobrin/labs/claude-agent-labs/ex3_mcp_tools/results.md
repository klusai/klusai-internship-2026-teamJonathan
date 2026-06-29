Pre-changes results:

model=claude-haiku-4-5

 #  chosen            expected          result  prompt
--------------------------------------------------------------------------------
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 1  search_orders     search_orders     PASS    Find order #10432
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 2  search_customers  search_customers  PASS    Look up the customer Acme Corporation
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 3  search_orders     search_orders     PASS    What's the status of 88231?
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 4  search_customers  search_customers  PASS    Show me everything for Jane Doe
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 5  search_orders     search_orders     PASS    Pull up ORD-5567
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 6  search_orders     search_orders     PASS    Who placed order 7741?
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 7  search_customers  search_customers  PASS    Get details for Globex
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 8  search_orders     search_orders     PASS    I need the record for 4521
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 9  search_customers  search_customers  PASS    Search for Smith
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
10  search_customers  search_customers  PASS    Find the order from Wayne Enterprises
--------------------------------------------------------------------------------
accuracy: 10/10 = 100%

Post-Changes

(ex3_mcp_tools) d0br1n@GUSI:~/klusai-internship-2026-teamJonathan/Alex Dobrin/labs/claude-agent-labs/ex3_mcp_tools$ python3 run_ambiguity_test.py
model=claude-haiku-4-5

 #  chosen            expected          result  prompt
--------------------------------------------------------------------------------
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 1  search_orders     search_orders     PASS    Find order #10432
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 2  search_customers  search_customers  PASS    Look up the customer Acme Corporation
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 3  search_orders     search_orders     PASS    What's the status of 88231?
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 4  search_customers  search_customers  PASS    Show me everything for Jane Doe
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 5  search_orders     search_orders     PASS    Pull up ORD-5567
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 6  search_orders     search_orders     PASS    Who placed order 7741?
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 7  search_customers  search_customers  PASS    Get details for Globex
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 8  search_orders     search_orders     PASS    I need the record for 4521
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
 9  search_customers  search_customers  PASS    Search for Smith
HTTP Request: POST https://api.anthropic.com/v1/messages "HTTP/1.1 200 OK"
10  search_customers  search_customers  PASS    Find the order from Wayne Enterprises
--------------------------------------------------------------------------------
accuracy: 10/10 = 100%

Apparently haiku was already smart enough to choose the tools properly even with the vague descriptions.
