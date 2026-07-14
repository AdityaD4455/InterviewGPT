# System Design Interview Notes

## Framework
1. Clarify requirements: functional + non-functional (scale, latency, consistency).
2. Estimate scale: QPS, storage, bandwidth back-of-envelope.
3. High-level design: draw major components (client, load balancer, API, cache, DB, queue).
4. Deep dive into 1-2 components the interviewer cares about.
5. Discuss trade-offs: consistency vs availability, SQL vs NoSQL, caching strategy.

## Core Building Blocks
- Load balancers: round robin, least connections, consistent hashing.
- Caching: read-through/write-through/write-behind, cache invalidation strategies.
- Databases: sharding, replication, CAP theorem trade-offs.
- Message queues: decoupling producers/consumers, at-least-once vs exactly-once delivery.
- CDNs: for static asset delivery and reducing origin load.

## Common Prompts
- Design a URL shortener: hashing scheme, redirect latency, analytics.
- Design a rate limiter: token bucket, sliding window log/counter.
- Design a news feed: fan-out on write vs fan-out on read trade-offs.
- Design a chat system: WebSockets, message ordering, delivery guarantees.

## Interviewer Signals
- They want communication and trade-off reasoning more than a "correct" answer.
- Asking clarifying questions early is a strong positive signal.
