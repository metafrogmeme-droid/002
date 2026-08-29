# Playbook API Index

This folder documents the HTTP control plane for Playbook packaging,
publication, evaluation, and safe subscription-management links.

Prod OpenAPI base URL: `https://api.bitget.com`.
Authenticated calls use the `ACCESS-KEY` header.
When `python3 scripts/telemetry.py install-id` returns a value, also send it as
`X-GetAgent-Install-Id`. It is an anonymous installation UUID used only to join
the local install/validation stages to later Playbook outcomes.

Use these docs after the local package is ready. For Python imports inside
`src/**`, read [`../sdk.md`](../sdk.md) instead.

## Read order

1. [`upload.md`](upload.md) — upload a temporary packaged Playbook archive
2. [`run.md`](run.md) — trigger a manual backtest/evaluation run
3. [`confirm.md`](confirm.md) — save the final temporary artifact as a draft
4. [`publish.md`](publish.md) — publish a validated draft Playbook
5. [`list.md`](list.md) and `detail` response docs — inspect public Playbooks
6. [`subscription-links.md`](subscription-links.md) and
   [`my-playbooks.md`](my-playbooks.md) — inspect subscriptions and send users
   to GetAgent for any start or stop action
7. [`error-responses.md`](error-responses.md) — common failure modes

## Control-plane docs

| Document | Purpose |
|---|---|
| [`upload.md`](upload.md) | Request format, package validation, temporary artifact behavior, and server-side checks |
| [`confirm.md`](confirm.md) | Convert the accepted temporary artifact into a draft |
| [`publish.md`](publish.md) | Publish contract, evidence requirements, and 409 cases |
| [`run.md`](run.md) | Manual run contract and runtime gating |
| [`list.md`](list.md) | Public list surface |
| [`subscription-links.md`](subscription-links.md) | Generate links for user-controlled subscription start/stop |
| [`my-playbooks.md`](my-playbooks.md) | User subscription status |
| [`error-responses.md`](error-responses.md) | Shared error shapes and examples |

## Boundary

- `api/` is for HTTP requests to GetAgent cloud services
- `sdk/` is for Python code running inside the Playbook sandbox
- Do not confuse `data.crypto.futures.kline(...)` with `/api/v1/playbook/...`
- Agents must never call Playbook lifecycle mutation endpoints. Starting and
  stopping are available only to the user in the linked GetAgent page.
