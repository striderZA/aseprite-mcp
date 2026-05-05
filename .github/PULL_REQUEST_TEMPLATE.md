## Summary

<!-- One sentence describing the change. -->

## Related issue

Closes #<!-- issue number -->

## Type of change

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New tool (exposes a new Aseprite API feature)
- [ ] Refactor / code quality
- [ ] Documentation
- [ ] CI / build / test

## How was this tested?

- [ ] Added/updated unit tests
- [ ] Tested with actual Aseprite (describe the tool call and result)

## Checklist

- [ ] `lua_escape` is used for any user-supplied string embedded in Lua
- [ ] `reject_traversal` is called on any user-supplied filename
- [ ] Tool includes docstring with `Args:` section matching the signature
- [ ] Error messages are user-actionable (not raw Python tracebacks)
