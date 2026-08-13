export async function callFunction(cdp, functionDeclaration, ...values) {
  if (typeof functionDeclaration !== "string" || !functionDeclaration.trim().startsWith("function")) {
    throw new TypeError("CDP functionDeclaration must be a fixed function string");
  }
  const response = await cdp.send("Runtime.callFunctionOn", {
    functionDeclaration,
    arguments: values.map((value) => ({ value })),
    awaitPromise: true,
    returnByValue: true,
  });
  if (response.exceptionDetails) throw new Error(response.exceptionDetails.text);
  return response.result?.value;
}
