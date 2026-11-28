// Custom commit-msg rules matching docs/code-standards.md's "Commits" section:
// header is "<area>: <behavior>" (not Conventional Commits), and the body
// must record how the change was verified.
export default {
  plugins: [
    {
      rules: {
        "header-area-format": ({ header }) => {
          const ok = /^[\w./-]+(?:,\s*[\w./-]+)*:\s+\S.+/.test(header);
          return [
            ok,
            'header must look like "<area>: <behavior>" (areas are the ' +
              "paths/modules touched), e.g. " +
              '"workflow/consumer: stop orphaned consumer when serve is killed"',
          ];
        },
        "body-not-empty": ({ body }) => {
          const ok = Boolean(body && body.trim().length > 0);
          return [
            ok,
            "commit body must not be empty - say how this was verified and " +
              "which test fails without the change",
          ];
        },
        "body-has-verified": ({ body }) => {
          const ok = Boolean(body && /verified:/i.test(body));
          return [
            ok,
            'commit body must include a "Verified:" paragraph describing ' +
              "how the change was checked (command + result)",
          ];
        },
      },
    },
  ],
  rules: {
    "header-max-length": [2, "always", 100],
    "header-area-format": [2, "always"],
    "body-leading-blank": [2, "always"],
    "body-not-empty": [2, "always"],
    "body-has-verified": [2, "always"],
  },
};
