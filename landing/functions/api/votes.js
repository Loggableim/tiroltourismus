/**
 * GET /api/votes — Vote-Counts (separater Endpoint für sauberes Routing)
 * Delegiert an die gleiche Logik wie /api/vote.
 */
export { onRequest } from './vote.js';
