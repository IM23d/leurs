// @ts-check
import js from "@eslint/js";
import { flatConfigs as importX } from "eslint-plugin-import-x";
import unicorn from "eslint-plugin-unicorn";
import { config, configs } from "typescript-eslint";

/** Restricts imports for `files`. Each rule is [patterns, message]. Later blocks replace earlier ones. */
const layer = (files, rules) => ({
  files,
  rules: {
    "no-restricted-imports": [
      "error",
      { patterns: rules.map(([group, message]) => ({ group, message })) },
    ],
  },
});

const MODULE_BOUNDARY = [
  ["#modules/*/*", "!#modules/*/api.ts", "../../*"],
  "Import another module only through its api.ts.",
];

export default config(
  { ignores: ["drizzle/", "data/", "node_modules/", "coverage/"] },
  js.configs.recommended,
  configs.strictTypeChecked,
  configs.stylisticTypeChecked,
  importX.recommended,
  importX.typescript,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    settings: { "import-x/resolver": { typescript: true, node: true } },
    plugins: { unicorn },
    rules: {
      eqeqeq: "error",
      curly: ["error", "multi-line"],
      "no-console": "error",
      "max-lines": ["error", { max: 300, skipBlankLines: true, skipComments: true }],
      "max-lines-per-function": ["error", { max: 80, skipBlankLines: true, skipComments: true }],
      complexity: ["error", 15],
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      "@typescript-eslint/restrict-template-expressions": ["error", { allowNumber: true }],
      "import-x/no-cycle": "error",
      "import-x/no-duplicates": "error",
      "import-x/order": [
        "error",
        {
          groups: ["builtin", "external", "internal", "parent", "sibling", "index"],
          pathGroups: [{ pattern: "#*/**", group: "internal" }],
          "newlines-between": "always",
          alphabetize: { order: "asc" },
        },
      ],
      "unicorn/filename-case": ["error", { case: "kebabCase" }],
      "unicorn/prefer-node-protocol": "error",
      "unicorn/prefer-at": "error",
      "unicorn/prefer-string-replace-all": "error",
      "unicorn/prefer-ternary": "error",
      "unicorn/no-lonely-if": "error",
      "unicorn/throw-new-error": "error",
    },
  },

  // Layer rules. See docs/architecture.md.
  layer(
    ["src/core/**", "src/shared/**", "src/db/**"],
    [[["#modules/*", "#app/*"], "core, shared and db must not depend on modules or the app."]],
  ),
  layer(["src/modules/**"], [MODULE_BOUNDARY]),
  layer(
    ["src/modules/*/*.service.ts", "src/modules/*/*.repo.ts"],
    [MODULE_BOUNDARY, [["discord.js"], "Services must not depend on discord.js."]],
  ),
  layer(
    ["src/modules/*/commands/**", "src/modules/*/events/**", "src/modules/*/components/**"],
    [
      MODULE_BOUNDARY,
      [
        ["drizzle-orm", "drizzle-orm/*", "#db/*", "../*.schema.ts"],
        "Commands, events and components call services, not the database.",
      ],
    ],
  ),

  {
    files: ["**/*.test.ts", "tests/**", "scripts/**"],
    rules: { "max-lines-per-function": "off", "no-console": "off" },
  },
  {
    files: ["**/*.js"],
    extends: [configs.disableTypeChecked],
  },
);
