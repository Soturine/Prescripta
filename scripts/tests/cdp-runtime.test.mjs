import assert from "node:assert/strict";
import test from "node:test";

import { callFunction } from "../lib/cdp-runtime.mjs";

test("passes hostile values as CDP arguments, never executable source", async () => {
  const values = ["quotes'\"", "`backtick`", "${globalThis.pwned=true}", "line1\nline2", "Unicode ç漢字", '"); throw new Error("pwned") //', "x".repeat(100_000)];
  for (const value of values) {
    let sent;
    const cdp = { send: async (method, params) => { sent = { method, params }; return { result: { value: true } }; } };
    assert.equal(await callFunction(cdp, "function (needle) { return needle.length > 0; }", value), true);
    assert.equal(sent.method, "Runtime.callFunctionOn");
    assert.equal(sent.params.functionDeclaration.includes(value), false);
    assert.deepEqual(sent.params.arguments, [{ value }]);
  }
});

test("rejects non-function declarations", async () => {
  await assert.rejects(() => callFunction({ send: async () => ({}) }, "alert(1)"), TypeError);
});
