import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    smoke: {
      executor: "constant-vus",
      vus: __ENV.VUS ? parseInt(__ENV.VUS, 10) : 10,
      duration: __ENV.DURATION || "30s",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<1500"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";

export default function () {
  const headers = { "Content-Type": "application/json", "X-Request-Id": `k6-${__VU}-${__ITER}` };

  const res1 = http.get(`${BASE_URL}/api/v1/system/health`, { headers });
  check(res1, { "health 200": (r) => r.status === 200 });

  const res2 = http.post(
    `${BASE_URL}/api/v1/orchestrator/route`,
    JSON.stringify({ query: "请帮我批改这份试卷" }),
    { headers }
  );
  check(res2, { "route 200": (r) => r.status === 200 });

  sleep(0.2);
}

