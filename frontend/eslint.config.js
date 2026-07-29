import js from "@eslint/js";
import reactHooks from "eslint-plugin-react-hooks";
import globals from "globals";
import tseslint from "typescript-eslint";

function jsxName(node) {
  return node?.name?.name;
}

function hasAttribute(node, name) {
  return node.attributes?.some((attribute) => attribute.type === "JSXAttribute" && attribute.name.name === name);
}

const accessibilityPlugin = {
  rules: {
    "img-requires-alt": {
      create(context) {
        return {
          JSXOpeningElement(node) {
            if (jsxName(node) === "img" && !hasAttribute(node, "alt")) {
              context.report({ node, message: "Imagens devem declarar texto alternativo." });
            }
          },
        };
      },
    },
    "anchor-requires-href": {
      create(context) {
        return {
          JSXOpeningElement(node) {
            if (jsxName(node) === "a" && !hasAttribute(node, "href")) {
              context.report({ node, message: "Links devem declarar href." });
            }
          },
        };
      },
    },
    "button-requires-type": {
      create(context) {
        return {
          JSXOpeningElement(node) {
            if (jsxName(node) === "button" && !hasAttribute(node, "type")) {
              context.report({ node, message: "Botões devem declarar type explicitamente." });
            }
          },
        };
      },
    },
  },
};

export default tseslint.config(
  { ignores: ["dist/**", "node_modules/**", "playwright-report/**", "test-results/**"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["src/**/*.{ts,tsx}"],
    languageOptions: {
      globals: globals.browser,
    },
    plugins: {
      "prescripta-a11y": accessibilityPlugin,
      "react-hooks": reactHooks,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      "react-hooks/set-state-in-effect": "off",
      "prescripta-a11y/img-requires-alt": "error",
      "prescripta-a11y/anchor-requires-href": "error",
      "prescripta-a11y/button-requires-type": "error",
    },
  },
  {
    files: ["*.config.{js,ts}", "tests/**/*.ts", "e2e/**/*.ts"],
    languageOptions: {
      globals: { ...globals.node, ...globals.browser },
    },
  },
);
