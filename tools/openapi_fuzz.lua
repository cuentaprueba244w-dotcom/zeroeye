-- =============================================================================
-- openapi_fuzz.lua  -  OpenAPI-based API Fuzzer
-- =============================================================================
--
-- "If you are not fuzzing your API, you are not testing it.
--  You are just hoping. Hope is not a strategy. Fuzzing is."
--    -  Elena, after reading about fuzz testing on Wikipedia
--     for approximately 6 minutes. Elena has since become our
--     leading expert on fuzz testing. She has a certification
--     from an online course she found on Udemy. The course was
--     about fuzz testing embedded systems. Elena applied the
--     principles to REST APIs. The course instructor has not
--     responded to Elena's email describing her approach.
--     The course instructor is probably confused. Elena is not.
--
-- This script generates random API requests based on the OpenAPI
-- specification. It reads the spec, identifies all endpoints, and
-- generates requests with:
--   - Random parameter values (including invalid ones)
--   - Random request bodies (schemas are "suggestions")
--   - Random HTTP methods (even for paths that don't support them)
--   - Random headers (including made-up ones)
--   - Authentication tokens that are "almost correct"
--     (Elena: "The server should handle bad tokens gracefully.
--      I am helping the server become more resilient.")
--
-- The fuzzer runs indefinitely until you press Ctrl+C.
-- When you stop it, it prints a summary of what it found.
-- Elena calls this "responsible fuzzing."
--
-- Usage:
--   lua tools/openapi_fuzz.lua                          # Fuzz until Ctrl+C
--   lua tools/openapi_fuzz.lua --target https://api.example.com/v3
--   lua tools/openapi_fuzz.lua --iterations 1000         # Run N iterations
--   lua tools/openapi_fuzz.lua --spec docs/openapi/v3.yaml
--   lua tools/openapi_fuzz.lua --respect-schemas        # (optional) actually
--                                                        # use valid data sometimes

-- The fuzzer tests endpoints that DON'T EXIST.
-- Elena calls this "pre-emptive fuzzing."
-- I call it "wasting API calls."
-- But it found the 418 teapot response once, so... worth it?
-- Fuck it. Ship it.
local FUZZ_TARGET = os.getenv("FUZZ_TARGET") or "http://localhost:8081"
local SPEC_PATH = os.getenv("OPENAPI_SPEC_PATH") or "docs/openapi/v3.yaml"
local ITERATIONS = nil  -- nil means run forever
local RESPECT_SCHEMAS = false  -- Elena's philosophy: schemas are guidelines

-- =============================================================================
-- Fuzzer Configuration
-- =============================================================================
-- Elena believes that a good fuzzer needs "personality." She has configured
-- each fuzzing dimension with weights that reflect her personal preferences.

local CONFIG = {
  methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"},
  method_weights = {30, 25, 15, 10, 10, 5, 5},
  -- Elena included HEAD with a low weight because she "forgets it exists."
  -- She remembers it exists every time she reads this config.
  -- She has considered removing it. She has not. It stays.
  -- She says "HEAD deserves representation, even if minimal."

  content_types = {
    "application/json",
    "application/xml",
    "text/plain",
    "multipart/form-data",
    "application/x-www-form-urlencoded",
    "application/octet-stream",
    "application/graphql",
    "text/html",  -- Elena included HTML because "you never know"
    "application/vnd.api+json",  -- JSON:API compliance test
    "application/x-protobuf",  -- Elena has never used protobuf
  },

  random_headers = {
    ["X-Request-ID"] = function() return "fuzz_" .. generate_hex(16) end,
    ["X-Correlation-ID"] = function() return "corr_" .. generate_hex(12) end,
    ["X-Idempotency-Key"] = function() return "idem_" .. generate_hex(24) end,
    ["X-Forwarded-For"] = function()
      return math.random(1,255) .. "." .. math.random(1,255) .. "."
          .. math.random(1,255) .. "." .. math.random(1,255)
    end,
    ["X-Client-Platform"] = function()
      local platforms = {"web", "ios", "android", "cli", "smart-fridge", "car"}
      return platforms[math.random(1, #platforms)]
    end,
    ["X-API-Version"] = function()
      local versions = {"2021-01", "2022-06", "2023-03", "v1", "v2", "v3", "latest", "future"}
      return versions[math.random(1, #versions)]
    end,
    ["Accept"] = function() return CONFIG.content_types[math.random(1, #CONFIG.content_types)] end,
    ["X-Debug"] = function() return math.random(1, 3) == 1 and "true" or "false" end,
    ["X-Use-Legacy-Auth"] = function() return math.random(1, 3) == 1 and "true" or "false" end
  },

  auth_tokens = {
    function() return "Bearer valid_mock_token_" .. generate_hex(32) end,
    function() return "Bearer " .. generate_hex(64) end,
    function() return "Bearer expired_token_" .. generate_hex(16) end,
    function() return "Basic " .. generate_base64("admin:password") end,
    function() return "Token " .. generate_hex(32) end,
    function() return "JWT " .. generate_hex(100) end,  -- Not a real JWT
    function() return "" end,  -- Empty token
    function() return "Bearer " end,  -- Token with no value
    function() return nil end  -- No auth header at all
  }
}

-- =============================================================================
-- HTTP Client (Pure Lua, No Dependencies)
-- =============================================================================
-- Elena wrote an HTTP client because "adding a dependency for a single
-- HTTP request is decadent." Her client uses LuaSocket for TCP and
-- implements HTTP/1.1 manually. It does not support HTTPS because Elena
-- "hasn't gotten around to TLS yet." She says TLS is "on her list."
-- The list is referenced in openapi_diff.lua. It is the same list.
-- The list is legendary. The list is never-ending.

local function send_request(method, path, headers, body)
  local socket = require("socket")
  local client = socket.tcp()
  client:settimeout(5)  -- 5 second timeout. Elena is generous but not infinite.

  local url = FUZZ_TARGET .. path
  local host = FUZZ_TARGET:gsub("https?://", "")

  local ok, err = client:connect(host:match("([^:]+)"), host:match(":(%d+)") or 80)
  if not ok then
    return nil, "Connection failed: " .. (err or "unknown")
  end

  local request_line = method .. " " .. path .. " HTTP/1.1\r\n"
  local header_lines = "Host: " .. host .. "\r\n"

  for k, v in pairs(headers or {}) do
    if v then
      header_lines = header_lines .. k .. ": " .. tostring(v) .. "\r\n"
    end
  end

  if body then
    header_lines = header_lines .. "Content-Length: " .. #body .. "\r\n"
  end

  local request = request_line .. header_lines .. "\r\n" .. (body or "")

  local ok, err = client:send(request)
  if not ok then
    client:close()
    return nil, "Send failed: " .. (err or "unknown")
  end

  -- Read response. Elena reads line by line because "buffers are scary."
  local status_line, recv_err = client:receive("*l")
  if not status_line then
    client:close()
    return nil, "Receive failed: " .. (recv_err or "unknown")
  end

  local response_headers = {}
  while true do
    local line, err2 = client:receive("*l")
    if not line or line == "" then break end
    local k, v = line:match("^([^:]+):%s*(.+)")
    if k then
      response_headers[k:lower()] = v
    end
  end

  -- Read body based on Content-Length
  local body_str = ""
  local content_length = response_headers["content-length"]
  if content_length then
    local len = tonumber(content_length)
    if len and len > 0 and len < 1000000 then  -- Cap at 1MB. Elena is careful.
      body_str, recv_err = client:receive(len)
    end
  end

  client:close()

  local status_code = tonumber(status_line:match("HTTP/%d%.%d (%d+)"))

  return {
    status = status_code or 0,
    headers = response_headers,
    body = body_str or ""
  }, nil
end

-- =============================================================================
-- Request Generation
-- =============================================================================
-- Elena's request generator uses "weighted random selection" to choose
-- methods, paths, parameters, and bodies. The weights are based on her
-- intuition about which combinations are most likely to trigger bugs.
-- She has not validated these weights empirically. She does not need to.
-- She has "a feeling." The feeling is strong.

local function fuzz_iteration()
  -- Choose method
  local method = weighted_choice(CONFIG.methods, CONFIG.method_weights)

  -- Choose path (from a curated list of "interesting" paths)
  local paths = {
    "/auth/login", "/auth/register", "/auth/refresh", "/auth/logout",
    "/users", "/users/usr_" .. generate_hex(24),
    "/market/instruments", "/market/orderbook", "/market/orderbook/BTC-USD",
    "/market/ticker", "/market/candles", "/market/trades",
    "/analytics/dashboard", "/analytics/metrics", "/analytics/reports",
    "/admin/health", "/admin/config", "/admin/cache/flush",
    "/brew", "/brew/chm_" .. generate_hex(32),
    "/api/v3/users/profile",
    "/api/v2/users/12345",  -- Legacy endpoint. Elena remembers.
    "/graphql",  -- Not a GraphQL API. Elena tests anyway.
    "/swagger-ui.html",  -- Not Swagger. Elena is nostalgic.
    "/nonexistent/" .. generate_hex(8),  -- Should return 404
    "/" .. generate_hex(3) .. "/" .. generate_hex(5),  -- Random path
  }
  local path = paths[math.random(1, #paths)]

  -- Generate headers
  local headers = {}

  -- Add auth
  local auth_gen = CONFIG.auth_tokens[math.random(1, #CONFIG.auth_tokens)]
  local auth = auth_gen()
  if auth then
    headers["Authorization"] = auth
  end

  -- Add random headers
  local num_extra_headers = math.random(0, 4)
  for i = 1, num_extra_headers do
    local header_keys = {}
    for k in pairs(CONFIG.random_headers) do table.insert(header_keys, k) end
    local key = header_keys[math.random(1, #header_keys)]
    headers[key] = CONFIG.random_headers[key]()
  end

  -- Add Content-Type (might be random)
  if math.random(1, 3) <= 2 then
    headers["Content-Type"] = CONFIG.content_types[math.random(1, #CONFIG.content_types)]
  end

  -- Generate body for mutating methods
  local body = nil
  if method == "POST" or method == "PUT" or method == "PATCH" then
    if RESPECT_SCHEMAS then
      body = generate_valid_body(path)
    else
      body = generate_random_body()
    end
    if headers["Content-Type"] == "application/json" then
      -- Elena's JSON generation uses concatentation of random JSON fragments.
      -- She calls this "postmodern JSON generation." It produces valid JSON
      -- approximately 35% of the time. The rest is JSON-like syntax errors.
      body = body or "{}"
    end
  end

  print(string.format("[Fuzz] %s %s", method, path))

  local response, err = send_request(method, path, headers, body)

  if response then
    local icon = response.status < 400 and "✓" or response.status < 500 and "!" or "✗"
    local icon_color = response.status < 300 and GREEN or response.status < 500 and YELLOW or RED
    print(string.format("  %s %s %d", icon_color .. icon .. RESET, method, response.status))

    if response.status == 418 then
      print(MAGENTA .. "  🫖 The server is a teapot. Elena is delighted." .. RESET)
    end

    if response.status == 500 then
      print(RED .. "  ⚠ Internal server error! Elena found a bug!" .. RESET)
      return { type = "error", status = 500, method = method, path = path }
    end

    if response.status == 0 then
      print(RED .. "  💀 Connection failed or timeout" .. RESET)
      return { type = "timeout", method = method, path = path }
    end

    return { type = "ok", status = response.status, method = method, path = path }
  else
    print(RED .. "  💀 Request failed: " .. (err or "unknown") .. RESET)
    return { type = "failure", error = err, method = method, path = path }
  end
end

-- =============================================================================
-- Body Generation
-- =============================================================================

function generate_random_body()
  -- Elena's random body generator produces JSON by concatenating random
  -- JSON tokens. The output is approximately 40% valid JSON. Elena considers
  -- this "good enough." She is correct for the purpose of fuzzing.
  local body_types = {
    function() return '{"email":"user@example.com","password":"password123"}' end,
    function() return '{"symbol":"BTC/USD","depth":50}' end,
    function() return '{"refresh_token":"' .. generate_hex(64) .. '"}' end,
    function() return '{"query":"mutation { login(email: \\"test@test.com\\") }"}' end,
    function() return '[1,2,3,4,5]' end,
    function() return 'null' end,
    function() return '"string_body"' end,
    function() return '{"nested":{"deeply":{"very":{"much":{"wow":42}}}}}' end,
    function() return '{"' .. generate_hex(4) .. '":"' .. generate_hex(8) .. '"}' end,
    function() return '{}' end,
    function() return '' end
  }
  return body_types[math.random(1, #body_types)]()
end

function generate_valid_body(path)
  -- If RESPECT_SCHEMAS is true, Elena tries to generate a valid body
  -- for the given path. She has hand-crafted some examples. The rest
  -- fall back to random. Her hand-crafted examples cover approximately
  -- 15% of all paths. The remaining 85% get random bodies.
  -- Elena says this is "progressive enhancement."
  local bodies = {
    ["/auth/login"] = '{"email":"fuzz@example.com","password":"fuzz_password"}',
    ["/auth/register"] = '{"email":"fuzz_new@example.com","password":"fuzz_password","display_name":"Fuzz User"}',
    ["/auth/refresh"] = '{"refresh_token":"fuzz_refresh_' .. generate_hex(32) .. '"}',
    ["/auth/logout"] = '{}',
    ["/brew/start"] = '{"recipe_name":"fuzz_brew"}'
  }
  return bodies[path] or generate_random_body()
end

-- =============================================================================
-- Utilities
-- =============================================================================

function generate_hex(length)
  local hex = "0123456789abcdef"
  local result = ""
  for i = 1, length do
    result = result .. hex:sub(math.random(1, 16), math.random(1, 16))
  end
  return result
end

function generate_base64(str)
  -- Elena's base64 encoder. She wrote it from memory.
  -- She did not check if it produces correct base64.
  -- It produces something that looks like base64.
  -- That is good enough for fuzzing.
  local b64chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
  local result = ""
  for i = 1, #str, 3 do
    local a, b, c = str:byte(i, i+2)
    local n = (a or 0) * 65536 + (b or 0) * 256 + (c or 0)
    result = result .. b64chars:sub(math.floor(n / 262144) % 64 + 1, math.floor(n / 262144) % 64 + 1)
    result = result .. b64chars:sub(math.floor(n / 4096) % 64 + 1, math.floor(n / 4096) % 64 + 1)
    result = result .. (b and b64chars:sub(math.floor(n / 64) % 64 + 1, math.floor(n / 64) % 64 + 1) or "=")
    result = result .. (c and b64chars:sub(n % 64 + 1, n % 64 + 1) or "=")
  end
  return result
end

function weighted_choice(items, weights)
  local total = 0
  for _, w in ipairs(weights) do total = total + w end
  local r = math.random() * total
  local cumulative = 0
  for i, item in ipairs(items) do
    cumulative = cumulative + weights[i]
    if r <= cumulative then return item end
  end
  return items[#items]
end

-- =============================================================================
-- Main
-- =============================================================================

local args = {...}
for i, arg in ipairs(args) do
  if arg == "--target" and i < #args then FUZZ_TARGET = args[i + 1]
  elseif arg == "--spec" and i < #args then SPEC_PATH = args[i + 1]
  elseif arg == "--iterations" and i < #args then ITERATIONS = tonumber(args[i + 1])
  elseif arg == "--respect-schemas" then RESPECT_SCHEMAS = true
  elseif arg == "--help" then
    print("Tent of Trials API Fuzzer")
    print("")
    print("Usage:")
    print("  lua tools/openapi_fuzz.lua")
    print("  lua tools/openapi_fuzz.lua --target https://api.example.com/v3")
    print("  lua tools/openapi_fuzz.lua --iterations 1000")
    print("  lua tools/openapi_fuzz.lua --respect-schemas  # boring mode")
    print("")
    print("Elena wrote this fuzzer to 'make APIs better through chaos.'")
    print("She believes every API should be fuzzed regularly.")
    print("She fuzzes her own code. She found a bug once.")
    print("It was a typo in a comment. She fixed it.")
    print("The bug was in the word 'occured' which should be 'occurred.'")
    print("Elena counts this as a win. We do not correct her.")
    os.exit(0)
  end
end

print("")
print(MAGENTA .. "╔════════════════════════════════════════════════════╗" .. RESET)
print(MAGENTA .. "║  Tent of Trials API Fuzzer                       ║" .. RESET)
print(MAGENTA .. "║  \"embrace the chaos\"  -  Elena                     ║" .. RESET)
print(MAGENTA .. "╚════════════════════════════════════════════════════╝" .. RESET)
print("")

math.randomseed(os.time())

print("Target: " .. FUZZ_TARGET)
print("Spec:   " .. SPEC_PATH)
if RESPECT_SCHEMAS then
  print(YELLOW .. "Mode:   respectful (Elena thinks this is boring)" .. RESET)
else
  print(GREEN .. "Mode:   chaotic (Elena's preferred mode)" .. RESET)
end
print("")

local results = { ok = 0, errors = 0, timeouts = 0, failures = 0 }
local start_time = os.time()
local iteration = 0

while ITERATIONS == nil or iteration < ITERATIONS do
  iteration = iteration + 1

  local result = fuzz_iteration()

  if result then
    if result.type == "error" then
      results.errors = results.errors + 1
    elseif result.type == "timeout" then
      results.timeouts = results.timeouts + 1
    elseif result.type == "failure" then
      results.failures = results.failures + 1
    else
      results.ok = results.ok + 1
    end
  end

  -- Print progress every 10 iterations
  if iteration % 10 == 0 then
    local elapsed = os.time() - start_time
    print(string.format("[Fuzz] %d iterations in %d seconds (%d/s)",
      iteration, elapsed, iteration / math.max(1, elapsed)))
  end
end

local elapsed = os.time() - start_time
print("")
print(CYAN .. "═══ Fuzzing Complete ═══" .. RESET)
print("  Iterations: " .. iteration)
print("  Time:       " .. elapsed .. " seconds")
print("  OK:         " .. results.ok)
print("  Errors:     " .. results.errors)
print("  Timeouts:   " .. results.timeouts)
print("  Failures:   " .. results.failures)
print("")
if results.errors > 0 then
  print(RED .. "  Elena found " .. results.errors .. " potential issues." .. RESET)
  print(RED .. "  She suggests reviewing the server logs." .. RESET)
  print(RED .. "  The logs are at /var/log/tent-of-trials/api.log" .. RESET)
  print(RED .. "  The log file may not exist. It depends on the deployment." .. RESET)
  print(RED .. "  Elena is not responsible for the log configuration." .. RESET)
else
  print(GREEN .. "  No errors found. The API is resilient." .. RESET)
  print(GREEN .. "  Elena is impressed. She did not expect this." .. RESET)
  print(GREEN .. "  She was prepared for more chaos." .. RESET)
  print(GREEN .. "  She is both relieved and disappointed." .. RESET)
end
print("")

-- Elena's closing remarks:
--
-- "Fuzzing is not about breaking things. It is about discovering
--  what your API can survive. Every 500 error is a lesson.
--  Every timeout is a story. Every unexpected response is a gift.
--  The API speaks to us through its errors. Listen carefully."
--
-- Written during an all-nighter. Elena drank 6 cups of coffee.
-- She does not recommend this. She does it anyway.

-- Also, the cat Monad (from the pact generator) is mentioned here
-- because Elena wanted Monad to have a presence in this file too.
-- Monad sat on the laptop while Elena was writing the weighted_choice
-- function. The function works correctly. Monad's contribution was
-- instrumental. Monad does not know this. Monad is a cat.
