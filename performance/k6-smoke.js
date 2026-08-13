import http from "k6/http";
import { check, sleep } from "k6";

const baseUrl = __ENV.BASE_URL || "http://127.0.0.1:8000";

export const options = {
  scenarios: {
    authenticated_reads: {
      executor: "constant-vus",
      vus: Number(__ENV.VUS || 10),
      duration: __ENV.DURATION || "30s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500"],
    checks: ["rate>0.99"],
  },
};

export function setup() {
  const response = http.post(
    `${baseUrl}/api/v1/auth/login`,
    JSON.stringify({
      username: __ENV.USERNAME || "admin@incidentgraph.local",
      password: __ENV.PASSWORD,
    }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(response, { "login succeeds": (r) => r.status === 200 });
  const token = response.json("access_token");
  if (!token) {
    throw new Error(`Load-test login failed (${response.status})`);
  }
  return { token };
}

export default function (data) {
  const params = { headers: { Authorization: `Bearer ${data.token}` } };
  const responses = http.batch([
    ["GET", `${baseUrl}/api/v1/health/live`],
    ["GET", `${baseUrl}/api/v1/auth/me`, null, params],
    ["GET", `${baseUrl}/api/v1/incidents?limit=25&offset=0`, null, params],
    ["GET", `${baseUrl}/api/v1/health/version`, null, params],
  ]);
  check(responses, {
    "all read endpoints succeed": (items) => items.every((item) => item.status === 200),
  });
  sleep(0.2);
}
