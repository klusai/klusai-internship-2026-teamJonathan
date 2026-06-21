# Northwind Robotics — FY2024 Annual Report

## Executive Summary

FY2024 was a year of disciplined growth for Northwind Robotics. The company crossed
540 full-time employees across eight functions and closed the year ahead of plan on
both revenue and margin. The board approved a multi-year platform investment and a
renewed focus on reliability after a difficult prior year. Each department summary
below covers what shipped, what broke, and what we learned. Unless noted, all figures
are for the fiscal year ending March 31, 2024, and are unaudited at the time of
writing.

## Software Engineering

The platform team's headline deliverable was shipping the Quokka platform v2 to
general availability. Quokka replaced the legacy monolith with a service-mesh
architecture, which let teams deploy independently for the first time. The migration
cut p95 API latency by 38% and reduced mean time to recovery from 47 minutes to 9.
The team also retired four internal services and consolidated logging onto a single
pipeline. Remaining work for next year: finish the read-path caching project and pay
down the test-flakiness backlog, which still costs roughly a day of engineering time
per week.

## Cybersecurity

The defining event of the year was incident INC-2023-014, a targeted phishing breach
that compromised two employee mailboxes before detection. There was no customer-data
loss, but the response reshaped the program. The team rotated all internal
credentials, moved secrets out of CI logs, and shortened the detection-to-containment
window from 31 hours to under 4. The team also issued hardware security keys to all
540 staff and made them mandatory for every administrative login. An external red-team
engagement in Q4 found no critical findings, down from nine the year before.

## Sales and Marketing

Annual recurring revenue (ARR) grew 24% year over year to $47M, led by expansion in
the existing base rather than new logos. The largest new deal was a three-year
contract with Globex for the fleet-management tier. Marketing shifted spend from
events to product-led content, which lowered customer acquisition cost by 19%. Net
revenue retention finished at 116%. The pipeline for next year is weighted toward the
manufacturing segment, where the new compliance certifications opened doors that were
previously closed.

## Customer Support

Customer satisfaction (CSAT) finished the year at 92%, up four points. The team cut
median first-response time from 5.6 hours to 2.1 hours, largely by deploying an
internal triage assistant that routes and drafts replies for agent review. Ticket
volume rose 27% with headcount flat, so deflection through the new self-serve help
center did most of the work. The biggest remaining pain point is after-hours coverage
for enterprise customers, which the team plans to address with a follow-the-sun
rotation next year.

## Finance

Gross margin improved to 71%, up from 64%, on better infrastructure utilization and
the service retirements noted by engineering. The company raised a $60M Series C in
the second half at a valuation the board considered strong given market conditions.
Operating expenses grew slower than revenue for the first time in three years.
Days-sales-outstanding crept up to 52 days, a watch item for next year. The finance
team also closed the books four days faster after automating the revenue-recognition
workflow.

## People and Culture

Attrition fell sharply, from 18% to 11%, which the team attributes to a new mentorship
program, clearer promotion ladders, and a remote-work stipend. Employee engagement
scores rose across every function except sales, where rapid hiring diluted the
result. The company made 180 hires and promoted 47 people internally. The biggest
open question for next year is compensation banding, which has drifted out of line
with the market in two engineering levels and is the most common theme in exit
interviews.

## Research and Development

The research group prototyped Project Halibut, an on-device inference engine that runs
the perception stack without a network connection — the single most-requested feature
from field customers. Early benchmarks show it within 12% of the cloud model's
accuracy at a fraction of the latency. The group filed three patents and published two
papers. Project Halibut is not yet on the product roadmap; the decision on whether to
productize it is the headline strategic question going into next year.
